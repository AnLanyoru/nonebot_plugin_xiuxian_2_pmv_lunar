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
