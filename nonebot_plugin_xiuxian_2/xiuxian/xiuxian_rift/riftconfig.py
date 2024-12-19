configkey = ["open", "rift"]
CONFIG = {
    "open": [],
    "rift": {
        "东玄域": {
            "type_rate": 200,  # 概率
            "rank": 1,  # 增幅等级
            "count": 30,  # 每次探索消耗体力
            "time": 60,  # 时间，单位分
        },
        "西玄域": {
            "type_rate": 200,
            "rank": 1,
            "count": 30,
            "time": 60,
        },
        "妖域": {
            "type_rate": 100,
            "rank": 2,
            "count": 50,
            "time": 90,
        },
        "乱魔海": {
            "type_rate": 100,
            "rank": 2,
            "count": 50,
            "time": 90,
        },
        "幻雾林": {
            "type_rate": 50,
            "rank": 3,
            "count": 50,
            "time": 120,
        },
        "狐鸣山": {
            "type_rate": 50,
            "rank": 3,
            "count": 50,
            "time": 120,
        },
        "云梦泽": {
            "type_rate": 25,
            "rank": 4,
            "count": 50,
            "time": 150,
        },
        "乱星原": {
            "type_rate": 12,
            "rank": 4,
            "count": 50,
            "time": 150,
        },
        "黑水湖": {
            "type_rate": 6,
            "rank": 5,
            "count": 50,
            "time": 180,
        }
    }
}


def get_rift_config():
    return CONFIG
