import random
from abc import abstractmethod

from nonebot_plugin_xiuxian_2.xiuxian.xiuxian_utils.clean_utils import number_to


class BaseSkill:
    """基础神通技能类"""
    name: str
    """神通名称"""
    desc: str
    """神通台词"""
    use_rate: int
    """释放概率"""
    cost_hp: float
    """消耗气血 当前值"""
    cost_mp: float
    """消耗真元 基础值 不足时无法释放"""
    rest_turn: int
    """释放神通后休息回合，-1为永久休息"""

    def act(self,
            user,
            target_member,
            msg_list: list[str]):
        """行动实现"""
        if random.randint(0, 100) > self.use_rate:  # 随机概率释放技能
            self.normal_attack(user, target_member, msg_list)
            return
        mp_cost_num = user.base_mp * self.cost_mp
        if mp_cost_num > user.mp:
            self.normal_attack(user, target_member, msg_list)
            return

        hp_cost_num = self.cost_hp * user.hp
        user.hp -= hp_cost_num
        hp_cost_msg = f"气血{number_to(hp_cost_num)}点，" if hp_cost_num else ''
        mp_cost_msg = f"真元{number_to(mp_cost_num)}点，" if mp_cost_num else ''
        cost_msg = '消耗' if hp_cost_msg or mp_cost_msg else ''
        rest_msg = ''
        if self.rest_turn:
            user.rest_turn += self.rest_turn
            rest_msg = f"休息{self.rest_turn}回合！"
        msg = f"{user.name}释放神通{self.name}，{cost_msg}{rest_msg}{hp_cost_msg}{mp_cost_msg}{self.desc}"
        msg_list.append(msg)
        self.achieve(user, target_member, msg_list)

    @abstractmethod
    def achieve(self, user, target_member, msg_list: list[str]):
        ...

    @staticmethod
    def normal_attack(user, target_member, msg_list: list[str]):
        """
        释放技能失败，平A
        :param user: 使用者
        :param target_member:攻击目标
        :param msg_list: 消息列表
        :return: 无
        """
        base_damage = [user.base_damage]
        msg = f"{user.name}发起攻击"
        msg_list.append(msg)
        user.attack(enemy=target_member, normal_damage=base_damage, msg_list=msg_list)



class BaseSub:
    """基础辅修技能类"""
    name: str
    """功法名称"""
    is_before_attack_act: bool = 0
    """是否有战斗后生效的效果"""
    is_after_attack_act: bool = 0
    """是否有战斗前生效的效果"""

    def before_attack_act(self, user, target_member, msg_list: list[str]):
        """战斗前生效的效果"""
        ...

    def after_attack_act(self, user, target_member, msg_list: list[str]):
        """战斗后生效的效果"""
        ...


class BaseBuff:
    """基础特殊效果类"""
    name: str
    """特殊效果名称"""
    least_turn: int
    """效果余剩回合 初始设置-1则持续时间无限"""

    @abstractmethod
    def act(self, user, target_member, msg_list: list[str]):
        """特殊效果主动效果"""
        ...

    @staticmethod
    def damage_change(damage: int, buff_damage_change: dict) -> None:
        """
        实现该方法可以增加或翻倍伤害
        :param damage: 原始伤害
        :param buff_damage_change: {'add': '为伤害增加一定数值', 'mul': '为伤害翻倍一定数值'}
        """
        ...

    @staticmethod
    def crit_change(crit_rate, buff_crit_change):
        """
        实现该方法可以增加或翻倍暴击率
        :param crit_rate: 原始暴击率
        :param buff_crit_change: {'add': '为暴击率增加一定数值（百分比）', 'mul': '为暴击率翻倍一定数值'}
        """
        ...

    @staticmethod
    def burst_change(burst, buff_burst_change):
        """
        实现该方法可以增加或翻倍暴击伤害
        :param burst: 原始暴击伤害
        :param buff_burst_change: {'add': '为暴击伤害增加一定数值', 'mul': '为暴击伤害翻倍一定数值'}
        """
        ...


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
    status: int
    """当前状态 1活0死"""
    name: str
    """对象名称"""
    hp: int
    """当前血量"""
    hp_max: int
    """最大血量"""
    mp: int
    """当前真元"""
    base_mp: int
    """基础100%真元"""
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
    armour_break: float
    """破甲效果对方的减伤减去此值"""
    rest_turn: int
    """休息回合，跳过主动行动"""
    turn_damage: int
    """本回合造成伤害"""
    sum_damage: int
    """整场战斗造成的总伤害"""
    turn_kill: bool
    """本回合是否有击杀事件发生"""
    main_skill: list[BaseSkill]
    """神通"""
    sub_skill: list[BaseSub]
    """辅修功法"""
    buffs: list[BaseBuff]
    """特殊效果"""
    increase: Increase
    """属性提升（不变常量类）"""

    def active(self, enemy, msg_list: list[str]):
        if not self.status:
            """寄了"""
            return
        msg_list.append(f"☆--{self.name}的回合！--☆")
        # 重置回合伤害
        self.turn_damage = 0
        # buff生效
        for buff in self.buffs:
            buff.act(self, enemy, msg_list)
        if self.sub_skill:
            for sub in self.sub_skill:
                if sub.is_before_attack_act:
                    sub.before_attack_act(self, enemy, msg_list)
        if self.rest_turn:
            msg = f"{self.name}动弹不得!!"
            msg_list.append(msg)
        if self.main_skill and not self.rest_turn:
            for skill in self.main_skill:
                skill.act(self, enemy, msg_list)
        if self.sub_skill:
            for sub in self.sub_skill:
                if sub.is_after_attack_act:
                    sub.after_attack_act(self, enemy, msg_list)

    @abstractmethod
    def hurt(
            self,
            attacker,
            msg_list: list[str],
            normal_damage: list[int] = None,
            real_damage: list[int] = None,
            armour_break: float = 0):
        """
        受伤接口
        :param attacker: 攻击者
        :param msg_list: 消息列表
        :param normal_damage: 普通伤害
        :param real_damage: 真实伤害
        :param armour_break: 破甲，减伤减少
        """
        ...

    @abstractmethod
    @property
    def base_damage(self) -> int:
        """
        基础伤害
        """
        ...

    @abstractmethod
    def check_crit(self, damage: int) -> int:
        """
        检测暴击并输出暴击伤害
        """
        ...

    @abstractmethod
    def attack(
            self,
            enemy,
            msg_list: list[str],
            normal_damage: list[int] = None,
            real_damage: list[int] = None,
            armour_break: float = 0):
        """造成伤害事件"""
        ...
