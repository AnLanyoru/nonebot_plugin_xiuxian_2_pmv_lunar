from pathlib import Path

DATABASE = Path() / "data" / "xiuxian"


def convert_rank(rank_name: str = '求道者'):
    """
    获取境界等级，替代原来的USERRANK
    convert_rank('求道者')[0] 返回求道者的境界等级
    convert_rank('求道者')[1] 返回境界列表
    """
    ranks = [
        '求道者',  # 55
        '炼体境一重', '炼体境二重', '炼体境三重',
        '炼体境四重', '炼体境五重', '炼体境六重', 
        '炼体境七重', '炼体境八重', '炼体境九重',  # 56 - 64
        '感气境初期', '感气境中期', '感气境后期',  # 65 - 67
        '引气境初期', '引气境中期', '引气境后期',  # 68 - 70
        '凝气境一重', '凝气境二重', '凝气境三重',
        '凝气境四重', '凝气境五重', '凝气境六重', 
        '凝气境七重', '凝气境八重', '凝气境九重',  # 71 - 79
        '聚元境一重', '聚元境二重', '聚元境三重',
        '聚元境四重', '聚元境五重', '聚元境六重', 
        '聚元境七重', '聚元境八重', '聚元境九重',  # 80 - 88
        '归元境一重', '归元境二重', '归元境三重',
        '归元境四重', '归元境五重', '归元境六重', 
        '归元境七重', '归元境八重', '归元境九重',  # 89 - 97
        '通玄境一重', '通玄境二重', '通玄境三重',
        '通玄境四重', '通玄境五重', '通玄境六重', 
        '通玄境七重', '通玄境八重', '通玄境九重',  # 98 - 106
        '踏虚境初期', '踏虚境中期', '踏虚境后期',  # 107 - 109
        '天人境初期', '天人境中期', '天人境后期', '天人境圆满',  # 110 - 113
        '悟道境初期', '悟道境中期', '悟道境后期',  # 114 - 116
        '炼神境初期', '炼神境中期', '炼神境后期',  # 117 - 119
        '逆虚境初期', '逆虚境中期', '逆虚境后期',  # 120 - 122
        '合道境初期', '合道境中期', '合道境后期',  # 123 - 125
        '虚劫境初期', '虚劫境中期', '虚劫境后期',  # 126 - 128
        '羽化境初期', '羽化境中期', '羽化境后期',  # 129 - 131
        '登仙境·叩天门', '登仙境·归一', '登仙境·虚火',
        '登仙境·星髓', '登仙境·归藏', '登仙境·脱凡',
        '登仙境·万象', '登仙境·太虚', '登仙境·九劫',  # 132 - 140
        '真仙境·半步', '真仙境·初期', '真仙境·中期', 
        '真仙境·后期', '真仙境·巅峰', '真仙境·大圆满',  # 141 - 146
        '玄仙境·半步', '玄仙境·初期', '玄仙境·中期',
        '玄仙境·后期', '玄仙境·巅峰', '玄仙境·大圆满',  # 147 - 152
        '金仙境·半步', '金仙境·初期', '金仙境·中期',
        '金仙境·后期', '金仙境·巅峰', '金仙境·大圆满',  # 152 - 157
        '太乙金仙·半步', '太乙金仙·初期', '太乙金仙·中期',
        '太乙金仙·后期', '太乙金仙·巅峰', '太乙金仙·大圆满',  # 158 - 163
        '大罗金仙·半步', '大罗金仙·初期', '大罗金仙·中期',
        '大罗金仙·后期', '大罗金仙·巅峰', '大罗金仙·大圆满',  # 164 - 169
        '九天玄仙·半步', '九天玄仙·初期', '九天玄仙·中期',
        '九天玄仙·后期', '九天玄仙·巅峰', '九天玄仙·大圆满',  # 170 - 175
        '混元大罗金仙·半步', '混元大罗金仙·初期', '混元大罗金仙·中期',
        '混元大罗金仙·后期', '混元大罗金仙·巅峰', '混元大罗金仙·大圆满',  # 176 - 181
        '罗天上仙·半步', '罗天上仙·初期', '罗天上仙·中期',
        '罗天上仙·后期', '罗天上仙·巅峰', '罗天上仙·大圆满',  # 182 - 187
        '无上仙君·半步', '无上仙君·初期', '无上仙君·中期',
        '无上仙君·后期', '无上仙君·巅峰', '无上仙君·大圆满',  # 188 - 193
        '混沌仙帝·半步', '混沌仙帝·初期', '混沌仙帝·中期',
        '混沌仙帝·后期', '混沌仙帝·巅峰', '混沌仙帝·大圆满',  # 194 - 199
        '无极仙尊·半步', '无极仙尊·初期', '无极仙尊·中期',
        '无极仙尊·后期', '无极仙尊·巅峰', '无极仙尊·大圆满',  # 200 - 205
        '神君境·半步', '神君境·初期', '神君境·中期',
        '神君境·后期', '神君境·巅峰', '神君境·大圆满',  # 206 - 211
        '神王境·半步', '神王境·初期', '神王境·中期',
        '神王境·后期', '神王境·巅峰', '神王境·大圆满',  # 212 - 217
        '神皇境·半步', '神皇境·初期', '神皇境·中期', 
        '神皇境·后期', '神皇境·巅峰', '神皇境·大圆满',  # 218 - 223
        '神帝境·半步', '神帝境·初期', '神帝境·中期', 
        '神帝境·后期', '神帝境·巅峰', '神帝境·大圆满',  # 224 - 229
        '神尊境·半步', '神尊境·初期', '神尊境·中期', 
        '神尊境·后期', '神尊境·巅峰', '神尊境·大圆满',  # 230 - 235
        '无上至尊·半步', '无上至尊·初期', '无上至尊·中期', 
        '无上至尊·后期', '无上至尊·巅峰', '无上至尊·大圆满',  # 236 - 241
        '鸿蒙掌控者·半步', '鸿蒙掌控者·初期', '鸿蒙掌控者·中期', 
        '鸿蒙掌控者·后期', '鸿蒙掌控者·巅峰', '鸿蒙掌控者·大圆满',  # 242 - 247
        '道神境·一重天', '道神境·二重天', '道神境·三重天',
        '道神境·四重天', '道神境·五重天', '道神境·六重天', 
        '道神境·七重天', '道神境·八重天', '道神境·九重天',  # 248 - 256
        '道无涯·生有涯', '道无涯·知无涯', '道无涯·地有边',
        '道无涯·天无边', '道无涯·劫落', '道无涯·掌缘生灭',  # 257 - 262
        "彼岸境·太皇天", "彼岸境·太明天", "彼岸境·清童天",
        "彼岸境·玄胎天", "彼岸境·元明天", "彼岸境·七曜天",
        "彼岸境·虚无天", "彼岸境·太极天", "彼岸境·赤阳天",
        "彼岸境·玄明天", "彼岸境·曜宗天", "彼岸境·皇笳天",
        "彼岸境·虚名天", "彼岸境·观靖天", "彼岸境·玄庆天", 
        "彼岸境·太瑶天", "彼岸境·元升天", "彼岸境·太安天",
        "彼岸境·极风天", "彼岸境·孝芒天", "彼岸境·太翁天",
        "彼岸境·无思天", "彼岸境·阮乐天", "彼岸境·昙誓天",
        "彼岸境·霄度天", "彼岸境·元洞天", "彼岸境·妙成天",
        "彼岸境·禁上天", "彼岸境·常融天", "彼岸境·玉胜天", 
        "彼岸境·梵度天", "彼岸境·平奕天", "彼岸境·三清天"
    ]

    if rank_name in ranks:
        rank_number = ranks.index(rank_name)
        return rank_number, ranks
    else:
        return None, ranks


class XiuConfig:
    def __init__(self):
        self.sql_table = ["user_xiuxian", "user_cd", "sects", "back", "buff_info", "bank_info", "mix_elixir_info"]
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
        self.break_world_need = ["天人境圆满", "登仙境·九劫", "无极仙尊·大圆满"]  # 突破位面最低境界要求
        self.lunhui_min_level = "天人境圆满"  # 千世轮回最低境界
        self.twolun_min_level = "羽化境后期"  # 万世轮回最低境界
        self.threelun_min_level = "无极仙尊·大圆满"  # 无上轮回最低境界
        self.merge_forward_send = 2  # 消息合并转发,1是分条发送，2是合成单消息转发，3是长图发送，建议长图发送
        self.img_compression_limit = 90  # 图片压缩率，0为不压缩，最高100
        self.img_type = "webp"  # 图片类型，webp或者jpeg，如果机器人的图片消息不显示请使用jpeg，jpeg请调低压缩率
        self.img_send_type = "base64"  # 图片发送类型,默认io,官方bot建议base64
        self.version = "xiuxian_2.2"  # 修仙插件资源包版本，todo 制作资源包 lunar_1.0
        self.elixir_def = {'回血丹药': 'hp', '回血丹': 'hp', '恢复丹': 'hp', '恢复丹药': 'hp', '回复丹': 'hp',
                           '突破丹药': 'level_up_rate', '突破丹': 'level_up_rate', '突破概率丹': 'level_up_rate'}
