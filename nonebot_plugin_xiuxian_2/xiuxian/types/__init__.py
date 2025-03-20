from enum import Enum
from typing import TypedDict


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


class BuffInfo(TypedDict):
    """用户buff信息"""
    id: int
    """唯一主键"""
    user_id: int
    """用户id"""
    main_buff: int
    """主功法"""
    sec_buff: int
    """神通"""
    faqi_buff: int
    """法器"""
    armor_buff: int
    """防具"""
    fabao_weapon: int
    """法宝（未实装）"""
    sub_buff: int
    """辅修功法"""
    atk_buff: int
    """攻击提升（丹药提升，已删除）"""
    blessed_spot: int
    """聚灵旗提升修炼速度"""
    elixir_buff: dict
    """丹药效果"""
    blessed_spot_name: str
    """聚灵旗名称"""
    learned_main_buff: str
    """学习的主功法"""
    learned_sub_buff: str
    """学习的辅修功法"""
    learned_sec_buff: str
    """学习的神通"""
    prepare_elixir_set: str
    """预备丹方"""
    lifebound_treasure: int
    """本命法宝"""
    support_artifact: int
    """辅助法宝"""
    inner_armor: int
    """内甲"""
    daoist_robe: int
    """道袍"""
    daoist_boots: int
    """道靴"""
    spirit_ring: int
    """灵戒"""
