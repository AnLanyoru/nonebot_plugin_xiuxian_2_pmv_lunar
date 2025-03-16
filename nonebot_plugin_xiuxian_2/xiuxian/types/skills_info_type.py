from typing import TypedDict

from nonebot_plugin_xiuxian_2.xiuxian.types import BaseItem


class MainBuff(BaseItem):
    """主功法"""
    hpbuff: float
    """血量提升 实际数值"""
    mpbuff: float
    """真元提升 实际数值"""
    atkbuff: float
    """攻击力提升 实际值"""
    ratebuff: float
    """修炼速度提升 实际值"""
    crit_buff: float
    """暴击率增加 实际值"""
    def_buff: float
    """减伤率 实际值"""
    dan_exp: int
    """炼丹经验提升 实际值"""
    dan_buff: int
    """炼丹获取数量提升 实际值"""
    reap_buff: int
    """灵田收取数量提升 数量"""
    exp_buff: float
    """突破失败经验保护 实际值"""
    critatk: float
    """暴击伤害增加 实际值"""
    two_buff: int
    """双修次数提升"""
    number: int
    """突破概率提升 百分比值"""
    clo_exp: float
    """闭关修为提升 实际提升值"""
    clo_rs: float
    """闭关恢复 实际提升值"""
    random_buff: bool
    """随机buff 是否拥有"""
    ew: int
    """专武对应id"""


class SubBuff(BaseItem):
    """辅修"""
    buff_type: str
    """
    buff类型
    1 攻击增加
    2 暴击率增加
    3 暴击伤害增加
    4 每回合生命恢复
    5 每回合真元恢复
    6 气血吸取
    7 真元吸取
    8 施加中毒
    9 气血，真元双吸取
    ---9之后的都是乱来的--
    10 重伤效果
    11 使对手发出的debuff失效，获得破甲
    12 提升boss战灵石获取，积分获取
    13 获得破甲，增加战斗获取修为
    """
    buff: str
    """buff效果，仅有一个效果时取该值，百分比"""
    buff2: str
    """
    buff效果2，有双效果时生效，第二个效果的值，百分比
    目前仅9有效果
    """
    # 以下废弃
    stone: int
    """boss战灵石获取增加"""
    integral: int
    """boss战积分获取增加"""
    jin: int
    """禁止对手气血吸取"""
    drop: int
    """Boss掉落率提高"""
    fan: int
    """使对手发出的debuff失效"""
    break_: int
    """获得boss战破甲"""
    exp: int
    """战斗获取修为提高"""


class SecBuff(BaseItem):
    """神通"""
    skill_type: int
    """
    神通类别
    1 直接伤害类型
    2 持续伤害类型
    3 buff类型
    """
    atkvalue: list[float] | float
    """
    神通类别
    1 直接伤害类型 atkvalue 为列表
    2 持续伤害类型 atkvalue 为float类型
    3 buff类型时无本项
    """
    bufftype: int
    """
    仅神通类别skill_type为3时有本项
    1 为攻击力增加 提升buffvalue倍攻击力
    2 为减伤率提升 直接增加buffvalue减伤数值
    """
    buffvalue: float
    """
    仅神通类别skill_type为3时有本项
    buff的数值
    """
    hpcost: float
    """释放消耗生命值"""
    mpcost: float
    """释放消耗真元"""
    turncost: int
    """
    1 直接伤害时为休息回合
    2 持续伤害时为持续回合
    3 buff类型时为持续回合
    """
    rate: int
    """释放概率"""
