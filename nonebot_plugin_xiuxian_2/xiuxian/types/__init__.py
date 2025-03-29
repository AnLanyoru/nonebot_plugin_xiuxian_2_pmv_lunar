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


class NewEquipmentBuffs(TypedDict):
    # 面板加成
    攻击: float
    """攻击力加成"""
    生命: float
    """生命值加成"""
    真元: float
    """真元加成"""
    会心率: float
    """暴击率增加"""

    # 战斗加成
    空间穿梭: int
    """空间穿梭（闪避率）"""
    空间封锁: int
    """空间封锁（减少对方闪避率）"""
    抗会心率: int
    """减少对方暴击率"""
    神魂伤害: float
    """灵魂伤害（真实伤害）"""
    神魂抵抗: float
    """灵魂抵抗（减少对方真实伤害）"""
    护盾: float
    """开局护盾"""
    因果转嫁: float
    """反伤"""
    冰之印记: float
    """叠标记加敌方受到伤害"""
    炽焰: float
    """受伤叠标记，满6层使敌方陷入dot状态"""
    金乌: float
    """
    金乌之力
    生命低于百分之50时，触发‘金乌之力’为自身生成一个百分比护盾【套装里面】，
    护盾存期间自身伤害提升百分之25【整局一次，吸血上来再次低于50%不可触发】
    """
    炎魔: float
    """炎魔之力；
    自身血量低于百分之30时【整局一次，吸血上来再次低于50%不可触发】，
    触发炎魔形态伤势快速回复，回复自身最大血量百分比【套装里面】"""
    烈火焚天: float
    """开局提升百分比【套装】伤害。"""
    雷霆: float
    """雷霆神力；自身生命低于百分之60时触发【整局一次，吸血上来再次低于50%不可触发】，
    触发后获得百分比【套装】伤害加成"""
    昊天神力: float
    """自身血量每低于百分之10，伤害增加百分比【套装】"""
    星魂之力: float
    """星魂之力；血量高于50%以上时伤害增加百分比【套装】，
    血量低于50以下时效果失效"""
    两仪领域: float
    """开局触发；进入战斗将敌人拉入两仪领域内，
    在领域内自身每回合提升百分比【套装】攻击"""
    四象之力: float
    """进入战斗提升自身百分比【套装】攻击力"""
    五行操控: float
    """五行操控；每次攻击叠加一层bf，为金木水火土，
    攻击5次后，下次1攻击百分比【套装】概率封印对面其行动一回合
    【无次数限制，每5次攻击触发】"""
    周天星辰之力: float
    """自身受到伤害超过自身最大生命百分之30后触发【整局一次】，
    被打通任督二脉，后续伤害增加百分比【套装】"""
    混元神树: float
    """混元神树，触发方式；自身生命低于最大生命50%时，
    召唤一颗自身最大生命百分比【套装】的混元神树【此效果整局一次】，
    该树会影响周围修士心智向他发动攻击【最大5人】，
    神树每受到攻击都会反弹百分比20的伤害回去，
    当神树被其他玩家杀死，召唤神树的修士会受到反噬，
    自身会受到神神树总生命的伤害反噬"""
