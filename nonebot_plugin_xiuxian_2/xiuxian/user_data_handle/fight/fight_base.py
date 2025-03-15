from abc import abstractmethod


class BaseSkill:
    """基础神通技能类"""
    status: dict
    """状态字典"""

    @abstractmethod
    def act(self, user, target_member, msg_list: list[str]): ...


class BaseSub:
    """基础辅修技能类"""
    status: dict
    """状态字典"""

    @abstractmethod
    def act(self, user, target_member, msg_list: list[str]): ...


class BaseBuff:
    """基础特殊效果类"""
    status: dict
    """状态字典"""

    @abstractmethod
    def act(self, user, target_member, msg_list: list[str]): ...


class Increase:
    def __init__(self):
        """
        增益字段 (也可以是减益)
        """
        self.atk = 1
        self.crit = 1
        self.burst = 1
        self.hp_steal = 1
        self.mp_steal = 1


class BaseFightMember:
    team: int
    """所属阵营，pve中怪物阵营恒定为0"""
    name: str
    """对象名称"""
    hp: int
    """当前血量"""
    hp_max: int
    """最大血量"""
    mp: int
    """当前真元"""
    mp_max: int
    """最大真元"""
    atk: int
    """攻击力"""
    crit: int
    """暴击率（百分比）"""
    burst: float
    """暴击伤害（倍率）"""
    defence: float
    """减伤数值 伤害*本数值"""
    main_skill: list[BaseSkill]
    """神通"""
    sub_skill: list[BaseSub]
    """辅修功法"""
    buffs: list[BaseBuff]
    """特殊效果"""
    increase: Increase
    """属性提升（不变常量类）"""

    def active(self, enemy, msg):
        # buff生效
        for buff in (self.buffs + self.main_skill + self.sub_skill):
            buff.act(self, enemy, msg)
        if self.main_skill:
            for skill in self.main_skill:
                skill.act(self, enemy, msg)
        if self.sub_skill:
            for sub in self.sub_skill:
                sub.act(self, enemy, msg)
        return msg

    @abstractmethod
    def hurt(self,
             msg_list: list[str],
             normal_damage: int = 0,
             real_damage: int = 0,
             armour_break: float = 0):
        """
        受伤接口
        :param msg_list: 消息列表
        :param normal_damage: 普通伤害
        :param real_damage: 真实伤害
        :param armour_break: 破甲，减伤减少
        """
        pass
