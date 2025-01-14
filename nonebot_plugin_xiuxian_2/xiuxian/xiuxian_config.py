from pathlib import Path

DATABASE = Path() / "data" / "xiuxian"


def convert_rank(rank_name):
    """
    获取境界等级，替代原来的USERRANK
    convert_rank('求道者')[0] 返回求道者的境界等级
    convert_rank('求道者')[1] 返回境界列表
    """
    ranks = [
        '求道者',  # 55
        '炼体境一重', '炼体境二重', '炼体境三重', '炼体境四重', '炼体境五重', '炼体境六重', '炼体境七重', '炼体境八重',
        '炼体境九重',  # 56 - 64
        '感气境初期', '感气境中期', '感气境后期',  # 65 - 67
        '引气境初期', '引气境中期', '引气境后期',  # 68 - 70
        '凝气境一重', '凝气境二重', '凝气境三重', '凝气境四重', '凝气境五重', '凝气境六重', '凝气境七重', '凝气境八重',
        '凝气境九重',  # 71 - 79
        '聚元境一重', '聚元境二重', '聚元境三重', '聚元境四重', '聚元境五重', '聚元境六重', '聚元境七重', '聚元境八重',
        '聚元境九重',  # 80 - 88
        '归元境一重', '归元境二重', '归元境三重', '归元境四重', '归元境五重', '归元境六重', '归元境七重', '归元境八重',
        '归元境九重',  # 89 - 97
        '通玄境一重', '通玄境二重', '通玄境三重', '通玄境四重', '通玄境五重', '通玄境六重', '通玄境七重', '通玄境八重',
        '通玄境九重',  # 98 - 106
        '踏虚境初期', '踏虚境中期', '踏虚境后期',  # 107 - 109
        '天人境初期', '天人境中期', '天人境后期', '天人境圆满',  # 110 - 113
        '悟道境初期', '悟道境中期', '悟道境后期',  # 114 - 116
        '炼神境初期', '炼神境中期', '炼神境后期',  # 117 - 119
        '逆虚境初期', '逆虚境中期', '逆虚境后期',  # 120 - 122
        '合道境初期', '合道境中期', '合道境后期',  # 123 - 125
        '虚劫境初期', '虚劫境中期', '虚劫境后期',  # 126 - 128
        '羽化境初期', '羽化境中期', '羽化境后期',  # 129 - 131
        '登仙境初期', '登仙境中期', '登仙境后期',  # 132 - 134
        '凡仙境初期', '凡仙境中期', '凡仙境后期',  # 135 - 137
        '地仙境初期', '地仙境中期', '地仙境后期',  # 138 - 140
        '玄仙境初期', '玄仙境中期', '玄仙境后期',  # 141 - 143
        '金仙境初期', '金仙境中期', '金仙境后期',  # 144 - 146
        '仙帝境初期', '仙帝境中期', '仙帝境后期',  # 147 - 149
        '准圣境初期', '准圣境中期', '准圣境后期',  # 150 - 152
        '圣人境一重', '圣人境二重', '圣人境三重', '圣人境四重', '圣人境五重', '圣人境六重', '圣人境七重', '圣人境八重',
        '圣人境九重',  # 153 - 161
        '大圣境初期', '大圣境中期', '大圣境后期',  # 162 - 164
        '圣王境初期', '圣王境中期', '圣王境后期',  # 165 - 167
        '不可言初期', '不可言中期', '不可言后期',  # 168 - 170
        '道神境一重', '道神境二重', '道神境三重', '道神境四重', '道神境五重', '道神境六重', '道神境七重', '道神境八重',
        '道神境九重',  # 171 - 179
        '道无涯初期', '道无涯中期', '道无涯后期',  # 180 - 182
        "彼岸境太皇天", "彼岸境太明天", "彼岸境清童天", "彼岸境玄胎天", "彼岸境元明天", "彼岸境七曜天", "彼岸境虚无天",
        "彼岸境太极天", "彼岸境赤阳天", "彼岸境玄明天", "彼岸境曜宗天",
        "彼岸境皇笳天", "彼岸境虚名天", "彼岸境观靖天", "彼岸境玄庆天", "彼岸境太瑶天", "彼岸境元升天", "彼岸境太安天",
        "彼岸境极风天", "彼岸境孝芒天", "彼岸境太翁天", "彼岸境无思天",
        "彼岸境阮乐天", "彼岸境昙誓天", "彼岸境霄度天", "彼岸境元洞天", "彼岸境妙成天", "彼岸境禁上天", "彼岸境常融天",
        "彼岸境玉胜天", "彼岸境梵度天", "彼岸境平奕天", "彼岸境三清天"
    ]

    if rank_name in ranks:
        rank_number = ranks.index(rank_name)
        return rank_number, ranks
    else:
        return None, ranks


class XiuConfig:
    def __init__(self):
        self.sql_table = ["user_xiuxian", "user_cd", "sects", "back", "buff_info"]
        self.sql_user_xiuxian = ["id", "user_id", "user_name", "stone", "root",
                                 "root_type", "level", "power",
                                 "create_time", "is_sign", "is_beg", "is_ban",  # 玩家状态相关
                                 "exp", "work_num", "level_up_cd",
                                 "level_up_rate", "sect_id",
                                 "sect_position", "hp", "mp", "atk", "atkpractice",
                                 "sect_task", "sect_contribution", "sect_elixir_get",
                                 "blessed_spot_flag", "blessed_spot_name", "user_stamina",
                                 "place_id"]
        self.sql_user_cd = ["user_id", "type", "create_time", "scheduled_time", "last_check_info_time", "place_id"]
        self.sql_sects = ["sect_id", "sect_name", "sect_owner", "sect_scale", "sect_used_stone", "sect_fairyland",
                          "sect_materials", "mainbuff", "secbuff", "elixir_room_level", "is_open"]
        self.sql_buff = ["id", "user_id", "main_buff", "sec_buff", "faqi_buff", "fabao_weapon", "armor_buff",
                         "atk_buff", "sub_buff", "blessed_spot"]
        self.sql_back = ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
                         "remake", "day_num", "all_num", "action_time", "state", "bind_num"]
        # 合成表数据校验
        self.sql_mixture = ["item_id", "need_items_id", "need_items_num", "create_time",
                            "update_time", "state", "is_bind_mixture"]
        self.sql_user_auctions = [""]
        # 上面是数据库校验,别动
        self.message_limit_time = 60  # 消息限制重置间隔
        self.message_limit = 30  # 消息限制间隔内最大发送信息条数
        self.level = convert_rank('求道者')[1]  # 境界列表，别动
        self.img = False  # 是否使用图片发送消息
        self.user_info_image = False  # 是否使用图片发送个人信息
        self.stamina_open = True  # 体力系统开关
        self.level_up_cd = 0  # 突破CD(分钟)
        self.closing_exp = 60  # 闭关每分钟获取的修为
        self.two_exp_limit = 7  # 基础双修次数
        self.two_exp = 1000000000  # 双修获取的修为上限
        self.sect_min_level = "归元境四重"  # 创建宗门最低境界
        self.sect_create_cost = 5000000  # 创建宗门消耗
        self.sect_rename_cost = 50000000  # 宗门改名消耗
        self.sect_rename_cd = 1  # 宗门改名cd/天
        self.auto_change_sect_owner_cd = 7  # 自动换长时间不玩宗主cd/天
        self.closing_exp_upper_limit = 1.3  # 闭关获取修为上限（例如：1.5 下个境界的修为数*1.5）
        self.level_punishment_floor = 1  # 突破失败扣除修为，惩罚下限（百分比）
        self.level_punishment_limit = 5  # 突破失败扣除修为，惩罚上限(百分比)
        self.level_up_probability = 1  # 突破失败增加当前境界突破概率的比例 0.2原始
        self.sign_in_lingshi_lower_limit = 1200000  # 每日签到灵石下限
        self.sign_in_lingshi_upper_limit = 1500000  # 每日签到灵石上限
        self.beg_max_level = "凝气境九重"  # 仙途奇缘能领灵石最高境界
        self.beg_max_days = 3  # 仙途奇缘能领灵石最多天数
        self.beg_lingshi_lower_limit = 10000000  # 仙途奇缘灵石下限
        self.beg_lingshi_upper_limit = 15000000  # 仙途奇缘灵石上限
        self.tou = 100000000  # 偷灵石惩罚
        self.dufang_cd = 10  # 金银阁cd/秒
        self.tou_lower_limit = 0.01  # 偷灵石下限(百分比)
        self.tou_upper_limit = 0.50  # 偷灵石上限(百分比)
        self.remake = 100000  # 重入仙途的消费
        self.max_stamina = 2400  # 体力上限
        self.stamina_recovery_points = 1  # 体力恢复点数/分钟
        self.break_world_need = ["天人境圆满", "羽化境后期", "仙帝境后期"]  # 突破位面最低境界要求
        self.lunhui_min_level = "天人境圆满"  # 千世轮回最低境界
        self.twolun_min_level = "羽化境后期"  # 万世轮回最低境界
        self.threelun_min_level = "仙帝境后期"  # 无上轮回最低境界
        self.merge_forward_send = 2  # 消息合并转发,1是分条发送，2是合成单消息转发，3是长图发送，建议长图发送
        self.img_compression_limit = 90  # 图片压缩率，0为不压缩，最高100
        self.img_type = "webp"  # 图片类型，webp或者jpeg，如果机器人的图片消息不显示请使用jpeg，jpeg请调低压缩率
        self.img_send_type = "base64"  # 图片发送类型,默认io,官方bot建议base64
        self.version = "xiuxian_2.2"  # 修仙插件资源包版本，todo 制作资源包 lunar_1.0
        self.elixir_def = {'回血丹药': 'hp', '回血丹': 'hp', '恢复丹': 'hp', '恢复丹药': 'hp', '回复丹': 'hp',
                           '突破丹药': 'level_up_rate', '突破丹': 'level_up_rate', '突破概率丹': 'level_up_rate'}
