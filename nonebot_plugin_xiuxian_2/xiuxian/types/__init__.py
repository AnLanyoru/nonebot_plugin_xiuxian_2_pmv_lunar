from enum import Enum
from typing import TypedDict

from nonebot_plugin_xiuxian_2.xiuxian.types.skills_info_type import SubBuff, SecBuff


class UserStatusType(Enum):
    """用户状态"""

    free = 0
    """无状态"""

    closing = 1
    """闭关"""

    working = 2
    """悬赏令"""

    rift = 3
    """秘境"""

    exp_up = 4
    """修炼"""

    xu_world_closing = 5
    """虚神界闭关"""

    world_tower = 6
    """位面挑战"""

    mix_elixir = 7
    """炼丹"""


class SectPosition(Enum):
    """宗门职位"""

    owner = 0
    """宗主"""

    elder = 1
    """长老"""

    own_disciple = 2
    """亲传弟子"""

    indoor_disciple = 3
    """内门弟子"""

    outdoor_disciple = 4
    """外门弟子"""


class UserInfo(TypedDict):
    """用户信息模型"""

    id: int
    """位序id"""
    user_id: int
    """游戏id"""
    user_name: str
    """道号"""
    stone: int
    """灵石数量"""
    root: str
    """灵根名称（可以随便改）"""
    root_type: str
    """灵根类型（枚举但是懒得写）"""
    level: str
    """境界（枚举）"""
    power: int
    """战斗力（🥚）"""
    create_time: str
    """账号创建时间"""
    is_sign: int
    """是否每日签到"""
    is_beg: int
    """是否仙途奇缘领取"""
    is_ban: int
    """是否被ban掉"""
    exp: int
    """当前修为"""
    work_num: int
    """悬赏令刷新次数"""
    level_up_cd: str
    """突破 CD（没用上）"""
    level_up_rate: int
    """突破概率（百分比）"""
    sect_id: int
    """所在宗门ID"""
    sect_position: int
    """宗门职位"""

    hp: int
    """记录生命值（不是战斗中实际生命值）"""
    mp: int
    """记录真元（不是战斗中实际真元）"""
    atk: int
    """记录攻击（用处不大）"""

    atkpractice: int
    """攻击修炼等级（md加个下划线会死？）"""
    sect_task: int
    """每日宗门任务次数"""
    sect_contribution: int
    """宗门贡献"""
    sect_elixir_get: int
    """宗门丹药领取"""

    blessed_spot_flag: int
    """是否创建洞天福地"""
    blessed_spot_name: str
    """洞天福地名称"""
    user_stamina: int
    """用户当前体力"""
    place_id: int
    """用户当前地图位置"""


class UserFightInfo(UserInfo):
    hp_buff: float
    """获取面板血量加成"""
    fight_hp: int
    """战斗中使用血量"""
    max_hp: int
    """战斗中基础最大血量"""
    mp_buff: float
    """获取面板真元加成"""
    fight_mp: int
    """战斗中使用真元"""
    base_mp: int
    """基础100%真元，用于计算神通消耗"""
    max_mp: int
    """战斗中基础最大真元"""
    atk: int
    """战斗中攻击力"""
    crit: int
    """基础暴击率 百分比"""
    burst: float
    """基础暴击伤害"""
    defence: float
    """基础减伤率 伤害*减伤率"""
    sub_buff_info: SubBuff
    """辅修数据"""
    sec_buff_info: SecBuff
    """神通数据"""



class UserMixElixirInfo(TypedDict):
    user_id: int
    farm_num: int
    farm_grow_speed: int
    farm_harvest_time: str
    last_alchemy_furnace_data: str
    user_fire_control: int
    user_herb_knowledge: int
    user_mix_elixir_exp: int
    user_fire_name: str
    user_fire_more_num: int
    user_fire_more_power: int
    mix_elixir_data: str
    sum_mix_num: int


class BaseItem(TypedDict, total=False):
    name: str
    """物品名称"""
    rank: str
    """物品等级"""
    level: str
    """物品等级别称，无具体作用"""
    desc: str
    """物品介绍"""
    type: str
    """物品所属大类"""
    item_type: str
    """物品所属细分类别"""


class BackItem(TypedDict):
    user_id: int
    goods_id: int
    goods_name: str
    goods_type: str
    goods_num: int
    bind_num: int
    create_time: str
    update_time: str
    remake: str
    day_num: int
    all_num: int
    action_time: str
    state: int
