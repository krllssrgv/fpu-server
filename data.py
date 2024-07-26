class Data:
    straight = 'straight'
    narrow = 'narrow'
    wide = 'wide'
    reverse = 'reverse'

    acts = [
        [
            [straight, reverse, narrow, reverse, straight],
            [5, 4, 5, 4, 3],
            [6, 5, 5, 6, 4],
            [5, 6, 6, 5, 5]
        ],
        [
            [straight, reverse, narrow, reverse, straight],
            [6, 5, 4, 6, 5],
            [8, 5, 5, 4, 4],
            [5, 9, 5, 5, 5]
        ],
        [
            [straight, reverse, narrow, reverse, wide],
            [8, 6, 5, 6, 2],
            [8, 7, 6, 5, 2],
            [10, 6, 7, 8, 2]
        ],
        [
            [straight, reverse, narrow, reverse, wide],
            [8, 10, 6, 6, 2],
            [11, 6, 8, 6, 2],
            [10, 10, 10, 6, 2]
        ],
        [
            [straight, reverse, straight, reverse, straight],
            [10, 9, 10, 7, 6],
            [11, 10, 9, 7, 5],
            [14, 12, 11, 9, 0]
        ],
        [
            [straight, reverse, narrow, reverse, straight],
            [11, 12, 11, 10, 10],
            [15, 12, 10, 9, 9],
            [17, 15, 12]
        ],
        [
            [straight, reverse, narrow, reverse, straight],
            [14, 16, 10, 10, 10],
            [15, 15, 10, 10, 10],
            [14, 13, 12, 11, 10]
        ],
        [
            [straight, reverse, straight, reverse, reverse],
            [12, 10, 9, 9, 8],
            [12, 10, 10, 9, 9],
            [13, 10, 10, 9, 8]
        ],
        [
            [straight, reverse, straight, reverse, reverse],
            [15, 11, 10, 9, 8],
            [15, 12, 11, 9, 8],
            [14, 13, 12, 11, 9]
        ],
        [
            [straight, reverse, straight, reverse, reverse],
            [15, 14, 10, 12, 10],
            [15, 14, 11, 13, 10],
            [14, 14, 14, 12, 11]
        ],
        [
            [straight, reverse, straight, reverse, reverse],
            [17, 10, 16, 10, 14],
            [14, 19, 11, 13, 9],
            [19, 13, 14, 13, 11]
        ],
        [
            [straight, reverse, straight, reverse, straight],
            [22, 13, 11, 10, 888],
            [24, 10, 11, 13, 888],
            [26, 10, 11, 10, 888]
        ],
        [
            [straight, reverse, straight, reverse, straight],
            [30, 15, 10, 15, 888],
            [33, 16, 11, 13, 888],
            [35, 10, 11, 10, 888]
        ],
        [
            [straight, reverse, straight],
            [30, 22, 888],
            [34, 20, 888],
            [19, 13, 888]
        ]    
    ]


    @classmethod
    def get_week(cls, week):
        return cls.acts[week]