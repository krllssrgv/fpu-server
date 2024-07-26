from flask import Flask, request, Blueprint, make_response, redirect, url_for, flash, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade, init, migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt, set_access_cookies, unset_jwt_cookies
from flask_cors import CORS
from flask_restx import Api, Resource, Namespace, fields
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from check_user import send_email, create_code
from data import Data
from admin import AdminUser

from config import SECRET_KEY, JWT_SECRET_KEY, SQLALCHEMY_DATABASE_URI



# App
app = Flask(__name__)

app.config['SECRET_KEY'] = SECRET_KEY
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=15)
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access']
app.config['JWT_COOKIE_SAMESITE'] = 'None'
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_COOKIE_CSRF_PROTECT'] = False


# CORS
CORS(app, supports_credentials=True)

# JWT
jwt = JWTManager(app)

# API
api_bp = Blueprint('API', __name__, url_prefix='/api')
api = Api(api_bp)
user_api = Namespace('user')
act_api = Namespace('act')

# DataBase
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(40), nullable=False)
    surname = db.Column(db.String(40), nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    confirmed = db.Column(db.Boolean, default=False, nullable=False)
    check_code = db.Column(db.String(10), default='', nullable=False)
    
    current_week = db.Column(db.Integer, nullable=False, default=0)
    day_one = db.Column(db.Boolean, nullable=False, default=False)
    day_two = db.Column(db.Boolean, nullable=False, default=False)
    day_three = db.Column(db.Boolean, nullable=False, default=False)
    success = db.Column(db.String(2), nullable=False, default='')

    def __repr__(self):
        return '<users %r>' % self.id


# Models
user_login_model = user_api.model('user_login', {
    'email': fields.String(required=True, description='Email'),
    'password': fields.String(required=True, description='Password')
})

user_confirm_model = user_api.model('user_login', {
    'code': fields.String(required=True, description='Code'),
})


BLACKLIST = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return jti in BLACKLIST


# Admin Login
class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# Admin
class MyAdminIndexView(AdminIndexView):
    @expose('/')
    @jwt_required()
    def index(self):
        return super(MyAdminIndexView, self).index()

class MyModelView(ModelView):
    @jwt_required()
    def is_accessible(self):
        return True
    

admin = Admin(app, name='Admin', template_mode='bootstrap3', index_view=MyAdminIndexView())
admin.add_view(MyModelView(users, db.session))


# User API

@user_api.route('/register')
class Register(Resource):
    def post(self):
        data = request.json
        check = True
        result = {}

        if (users.query.filter(users.email == data['email']).all()):
            check = False
            result['email'] = 'Пользователь уже существует'

        if (len(data['password']) < 6):
            check = False
            result['password'] = 'Минимальная длина 6 символов'

        if (data['password'] != data['repeatedPassword']):
            check = False
            result['repeatedPassword'] = 'Пароли не совпадают'

        if check:
            code = create_code()
            new_user = users(
                email=str(data['email']),
                password=generate_password_hash(str(data['password'])),
                name=str(data['name']),
                surname=str(data['surname']),
                check_code = code
            )
            try:
                db.session.add(new_user)
                db.session.commit()
                print(send_email(str(data['email']), code))
                return '', 204
            except:
                return '', 500
        else:
            return result, 400


@user_api.route('/login')
class Login(Resource):
    @user_api.expect(user_login_model)
    def post(self):
        data = request.json
        user = users.query.filter_by(email=data['email']).first()
        if user:
            if check_password_hash(user.password, data['password']):
                access_token = create_access_token(identity=user.id)
                response = make_response()
                set_access_cookies(response, access_token)
                return response
            else:
                return {'password': 'Неправильный пароль'}, 401
        else:
            return {'email': 'Нет такого пользователя'}, 401


@user_api.route('/logout')
class Logout(Resource):
    @jwt_required(optional=True)
    def post(self):
        user = db.session.get(users, get_jwt_identity())

        if (user):
            jti = get_jwt()['jti']
            BLACKLIST.add(jti)
            response = make_response()
            unset_jwt_cookies(response)
            return response
        else:
            return '', 401
    

@user_api.route('/check_login')
class CheckLogin(Resource):
    @jwt_required(optional=True)
    def get(self):
        user = db.session.get(users, get_jwt_identity())

        if (user):
            return '', 204
        else:
            return '', 401
        

@user_api.route('/confirm_email')
class ConfirmEmail(Resource):
    @jwt_required(optional=True)
    @user_api.expect(user_confirm_model)
    def post(self):
        user = db.session.get(users, get_jwt_identity())

        if (user):
            if (not user.confirmed):
                code = request.json['code']
                if (code == user.check_code):
                    user.check_code = ''
                    user.confirmed = True
                    try:
                        db.session.commit()
                        return '', 204
                    except:
                        return '', 500
                else:
                    return {'error': 'Неправильный код'}, 400
            else:
                return {'error': 'Почта уже подтверждена'}, 400
        else:
            return '', 401
        

@user_api.route('/user')
class UserRequests(Resource):
    @jwt_required(optional=True)
    def get(self):
        user = db.session.get(users, get_jwt_identity())

        if (user):
            if (user.current_week < 14):
                user_data = Data.get_week(user.current_week)
                days = [
                    {
                        'number': 1,
                        'done': user.day_one,
                        'acts': user_data[1]
                    },
                    {
                        'number': 2,
                        'done': user.day_two,
                        'acts': user_data[2]
                    },
                    {
                        'number': 3,
                        'done': user.day_three,
                        'acts': user_data[3]
                    }
                ]
                
                return {
                    'name': user.name,
                    'surname': user.surname,
                    'email': user.email,
                    'confirmed': user.confirmed,
                    'progress': int((round(user.current_week / 14, 2)) * 100),
                    'success': user.success,
                    'current_week': user.current_week,
                    'types': user_data[0],
                    'days': days,
                    'finish': False
                }
            else:
                return {
                    'name': user.name,
                    'surname': user.surname,
                    'email': user.email,
                    'confirmed': user.confirmed,
                    'progress': 100,
                    'finish': True
                }
        else:
            return '', 401
        

@user_api.route('/remove')
class RemoveUser(Resource):
    @jwt_required(optional=True)
    def post(self):
        user = db.session.get(users, get_jwt_identity())

        if (user):
            try:
                db.session.delete(user)
                db.session.commit()
                jti = get_jwt()['jti']
                BLACKLIST.add(jti)
                response = make_response()
                unset_jwt_cookies(response)
                return response
            except:
                return '', 500
        else:
            return '', 401


# Act API

@act_api.route('/set_day_as_done')
class DoneDay(Resource):
    @jwt_required(optional=True)
    def post(self):
        user = db.session.get(users, get_jwt_identity())

        if (user):
            data = request.json
            if ('set_day' in data):
                if (data['set_day'] == 1):
                    user.day_one = True
                elif (data['set_day'] == 2):
                    user.day_two = True
                elif (data['set_day'] == 3):
                    user.day_three = True
                    
                if (user.day_one and user.day_two and user.day_three):
                    user.success = '0'

                try:
                    db.session.commit()
                    return '', 200
                except:
                    return '', 500
            else:
                    return '', 400
        else:
            return '', 401


@act_api.route('/send_result')
class Result(Resource):
    @jwt_required(optional=True)
    def post(self):
        user = db.session.get(users, get_jwt_identity())

        if (user):
            data = request.json
            if ('success' in data):
                if (data['success']):
                    user.success = '1'
                else:
                    user.success = '-1'
                    
                try:
                    db.session.commit()
                    return {'success': user.success}, 200
                except:
                    return '', 500 
            else:
                return '', 400
        else:
            return '', 401 
        

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        if (AdminUser.check_admin(username, password)):
            access_token = create_access_token(identity=username)
            response = make_response(redirect(url_for('admin.index')))
            set_access_cookies(response, access_token)
            return response
        else:
            flash('Invalid username or password')
    
    return render_template('login.html', form=form)


# Register
api.add_namespace(act_api, path='/act')
api.add_namespace(user_api, path='/user')
app.register_blueprint(api_bp)


# BackgroundScheduler
def update_weeks():
    with app.app_context():
        all_users = users.query.all()
        for user in all_users:
            user.day_one = False
            user.day_two = False
            user.day_three = False

            if (user.success == '1'):
                user.current_week += 1

            user.success = ''
        db.session.commit()


if __name__ == '__main__':
    app.run(debug=False)
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_weeks, 'cron', day_of_week='mon', hour=1, minute=0)
    scheduler.start()