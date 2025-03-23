import random
from abc import abstractmethod

from .damage_data import DamageData
from ...types.skills_info_type import BuffIncreaseDict, SecBuff
from ...xiuxian_utils.clean_utils import number_to


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
    rest_turn: int = 0
    """释放神通后休息回合，-1为永久休息"""

    def __init__(self, sec_buff_info: SecBuff):
        self.name = sec_buff_info['name']
        self.desc = sec_buff_info['desc']
        self.cost_hp = sec_buff_info['hpcost']
        self.cost_mp = sec_buff_info['mpcost']
        self.use_rate = sec_buff_info['rate']

    def act(self,
            user,
            target_member,
            fight_event: 'FightEvent',
            user_skill_list: list):
        """行动实现"""
        # 基础伤害
        cost_msg, is_use = self.use_check(user, target_member, fight_event)
        if not is_use:
            # 不使用则普通攻击
            self.normal_attack(user, target_member, fight_event)
            return
        rest_msg = ''
        if self.rest_turn:
            user.rest_turn += self.rest_turn
            rest_msg = f"休息{self.rest_turn}回合！"
        base_damage, crit_msg = self.act_base_damage(user, target_member)
        msg = (f"{user.name}释放神通：{self.name}，"
               f"{cost_msg}"
               f"{self.desc}{rest_msg}{crit_msg}")
        fight_event.add_msg(msg)
        self.achieve(user, target_member, base_damage, fight_event)
        self.back_skill_list(user_skill_list)

    @abstractmethod
    def achieve(self, user, target_member, base_damage: int, fight_event: 'FightEvent'):
        """
        技能基础实现
        :param user: 使用该技能的对象
        :param target_member: 该技能的目标
        :param base_damage: 该技能的基础数值
        :param fight_event: 消息列表
        :return:
        """
        ...

    @staticmethod
    def normal_attack(user, target_member, fight_event: 'FightEvent'):
        """
        未释放技能，普通攻击
        :param user: 使用者
        :param target_member:攻击目标
        :param fight_event: 消息列表
        :return: 无
        """
        base_damage = user.base_damage
        normal_attack_value = [1]
        for buff in user.buffs.values():
            buff.skill_value_change(normal_attack_value)
        base_damage, is_crit = user.check_crit(base_damage, target_member)
        damage = DamageData(
            normal_damage=[int(base_damage * atk_value_per) for atk_value_per in normal_attack_value])
        crit_msg = ''
        if is_crit:
            crit_msg = "并发生了会心一击！"
        msg = f"{user.name}发起攻击{crit_msg}"
        fight_event.add_msg(msg)
        user.attack(enemy=target_member, fight_event=fight_event, damage=damage)

    @staticmethod
    def act_base_damage(user, target_member) -> tuple[int, str]:
        """
        获取基础伤害，若要实现无暴击技能，重写此方法
        :param target_member: 攻击目标
        :param user: 使用技能者
        :return:
        """
        base_damage = user.base_damage
        base_damage, is_crit = user.check_crit(base_damage, target_member)
        crit_msg = ''
        if is_crit:
            crit_msg = "并发生了会心一击！"
        return base_damage, crit_msg

    def use_check(self, user, target_member, fight_event: 'FightEvent') -> tuple[str, bool]:
        """
        释放检查，重写此方法可实现特殊释放模式
        :param user: 使用者
        :param target_member: 目标
        :param fight_event: 消息列表
        :return:
        """
        if random.randint(0, 100) > self.use_rate:  # 随机概率释放技能
            return '', False
        mp_cost_num = user.base_mp * self.cost_mp
        if mp_cost_num > user.mp:
            return '', False
        hp_cost_num = self.cost_hp * user.hp
        user.hp -= hp_cost_num
        user.mp -= mp_cost_num
        hp_cost_msg = f"气血{number_to(hp_cost_num)}点，" if hp_cost_num else ''
        mp_cost_msg = f"真元{number_to(mp_cost_num)}点，" if mp_cost_num else ''
        cost_msg = f'消耗{hp_cost_msg}{mp_cost_msg}' if hp_cost_msg or mp_cost_msg else ''
        return cost_msg, True

    def back_skill_list(self, user_skill_list: list):
        """将自身重新排入技能释放轴中"""
        user_skill_list.append(self)
        user_skill_list.pop(0)


class NormalAttack(BaseSkill):
    """未释放神通时的普通攻击"""

    def achieve(self, user, target_member, base_damage, fight_event: 'FightEvent'):
        pass


empty_skill = NormalAttack


class BaseSub:
    """基础辅修技能类"""
    name: str
    """功法名称"""
    is_before_attack_act: bool = False
    """是否有战斗后生效的效果"""
    is_after_attack_act: bool = False
    """是否有战斗前生效的效果"""
    is_just_attack_act: bool = False
    """是否有造成伤害后即时生效的效果"""
    is_final_act: bool = False
    """是否是最后一次生效"""

    def before_attack_act(self,
                          user: 'BaseFightMember',
                          target_member: 'BaseFightMember',
                          fight_event: 'FightEvent'):
        """战斗前生效的效果"""
        ...

    def after_attack_act(self,
                         user: 'BaseFightMember',
                         target_member: 'BaseFightMember',
                         fight_event: 'FightEvent'):
        """战斗后生效的效果"""
        ...

    def just_attack_act(self,
                        user: 'BaseFightMember',
                        target_member: 'BaseFightMember',
                        fight_event: 'FightEvent'):
        """造成伤害后即时生效的效果"""
        ...


class BaseBuff:
    """基础特殊效果类"""
    name: str
    """特殊效果名称"""
    least_turn: int
    """效果余剩回合 初始设置-1则持续时间无限"""
    impose_member: int = None
    """施加者"""
    num: int = 1
    """层数"""
    max_num: int = 1
    """最大层数"""

    def __init__(self, impose_member_id: int):
        """
        :param impose_member_id: 施加该buff的对象
        """
        self.impose_member = impose_member_id

    @abstractmethod
    def act(self,
            effect_user: 'BaseFightMember',
            now_enemy: 'BaseFightMember',
            fight_event: 'FightEvent'):
        """
        特殊效果主动效果
        :param effect_user: buff生效影响目标
        :param now_enemy: buff生效目标当前回合的敌人
        :param fight_event: 消息列表
        :return:
        """
        ...

    @staticmethod
    def damage_change(damage: int, buff_damage_change: BuffIncreaseDict) -> None:
        """
        实现该方法可以增加或翻倍伤害
        :param damage: 原始伤害
        :param buff_damage_change: {'add': '为伤害增加一定数值', 'mul': '为伤害翻倍一定数值'}
        """
        ...

    @staticmethod
    def final_hurt_change(damage: int, buff_final_hurt_change: BuffIncreaseDict) -> None:
        """
        实现该方法可以增加或翻倍最终受到伤害倍率
        :param damage: 原始受到伤害倍率
        :param buff_final_hurt_change: {'add': '增加一定数值', 'mul': '翻倍一定数值'}
        """
        ...

    @staticmethod
    def crit_change(crit_rate: int, buff_crit_change: BuffIncreaseDict):
        """
        实现该方法可以增加或翻倍暴击率
        :param crit_rate: 原始暴击率
        :param buff_crit_change: {'add': '为暴击率增加一定数值（百分比）', 'mul': '为暴击率翻倍一定数值'}
        """
        ...

    @staticmethod
    def burst_change(burst: float, buff_burst_change: BuffIncreaseDict):
        """
        实现该方法可以增加或翻倍暴击伤害
        :param burst: 原始暴击伤害
        :param buff_burst_change: {'add': '为暴击伤害增加一定数值', 'mul': '为暴击伤害翻倍一定数值'}
        """
        ...

    @staticmethod
    def defence_change(defence: float, buff_burst_change: BuffIncreaseDict):
        """
        实现该方法可以增加或翻倍减伤
        :param defence: 原始减伤
        :param buff_burst_change: {'add': '增加一定数值', 'mul': '翻倍一定数值'}
        """
        ...

    @staticmethod
    def skill_value_change(value: list[float]):
        """
        实现该方法可以增加技能倍率
        :param value: 原始倍率列表
        """
        ...

    def add_num(self, need_add_num: int) -> str:
        """
        为效果增加层数
        :param need_add_num: 增加数量
        :return:
        """
        self.num += need_add_num
        if self.num > self.max_num:
            self.num = self.max_num
            return f"叠加了{need_add_num}层{self.name}，{self.name}的叠加达到上限{self.num}层"
        return f"叠加了{need_add_num}层{self.name}（当前{self.num}层）"


class Increase:
    def __init__(self):
        """
        增益字段 (也可以是减益)
        """
        self.atk = 1
        self.crit = 0
        self.burst = 0
        self.hp_steal = 1
        self.mp_steal = 1


class BaseFightMember:
    id: int
    """战斗中序列"""
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
    turn_damage: DamageData
    """本回合造成伤害"""
    sum_damage: DamageData
    """整场战斗造成的总伤害"""
    turn_kill: bool
    """本回合是否有击杀事件发生"""
    main_skill: list[BaseSkill]
    """神通"""
    sub_skill: dict[str, BaseSub]
    """辅修功法"""
    buffs: dict[str, BaseBuff]
    """特殊效果"""
    increase: Increase
    """属性提升（不变常量类）"""
    miss_rate: int
    """空间穿梭（闪避率）"""
    decrease_miss_rate: int
    """空间封锁（减少对方闪避率）"""
    decrease_crit: int
    """减少对方暴击率"""
    soul_damage_add: float
    """灵魂伤害（真实伤害）"""
    decrease_soul_damage: float
    """灵魂抵抗（减少对方真实伤害）"""
    shield: int
    """开局护盾"""
    back_damage: float
    """反伤"""
    ice_mark: float
    """叠标记加敌方受到伤害"""

    def active(self, enemy: 'BaseFightMember', fight_event: 'FightEvent'):
        if not self.status:
            """寄了"""
            return
        if self.rest_turn:
            msg = f"☆ -- {self.name}动弹不得！-- ☆"
            fight_event.msg_list.append(msg)
        else:
            fight_event.msg_list.append(f"☆ -- {self.name}的回合 -- ☆")
        # buff生效

        del_buff_list: list[str] = []
        for buff_name, buff in self.buffs.items():
            buff.least_turn -= 1
            buff.act(self, enemy, fight_event)
            if not buff.least_turn:
                del_buff_list.append(buff_name)
        if del_buff_list:
            for buff_name in del_buff_list:
                del self.buffs[buff_name]

        del_sub_list: list[str] = []
        if self.sub_skill:
            for sub_name, sub in self.sub_skill.items():
                if sub.is_before_attack_act:
                    sub.before_attack_act(self, enemy, fight_event)
                    if sub.is_final_act:
                        del_sub_list.append(sub_name)
        if del_sub_list:
            for sub_name in del_sub_list:
                del self.sub_skill[sub_name]
        if not self.rest_turn:
            if self.main_skill:
                self.main_skill[0].act(self, enemy, fight_event, self.main_skill)
            else:
                empty_skill.normal_attack(self, enemy, fight_event)
        else:
            self.rest_turn -= 1

        del_sub_list: list[str] = []
        if self.sub_skill:
            for sub_name, sub in self.sub_skill.items():
                if sub.is_after_attack_act:
                    sub.after_attack_act(self, enemy, fight_event)
                    if sub.is_final_act:
                        del_sub_list.append(sub_name)
        if del_sub_list:
            for sub_name in del_sub_list:
                del self.sub_skill[sub_name]
        # 重置回合伤害
        self.turn_damage.reset_all()

    def just_attack_act(self, enemy: 'BaseFightMember', fight_event: 'FightEvent'):

        del_sub_list: list[str] = []
        if self.sub_skill:
            for sub_name, sub in self.sub_skill.items():
                if sub.is_just_attack_act:
                    sub.just_attack_act(self, enemy, fight_event)
                    if sub.is_final_act:
                        del_sub_list.append(sub_name)
        if del_sub_list:
            for sub_name in del_sub_list:
                del self.sub_skill[sub_name]

    @abstractmethod
    def hurt(
            self,
            attacker: 'BaseFightMember',
            fight_event: 'FightEvent',
            damage: DamageData,
            armour_break: float = 0):
        """
        受伤接口
        :param attacker: 攻击者
        :param fight_event: 'FightEvent': 消息列表
        :param damage: 伤害
        :param armour_break: 破甲，减伤减少
        """
        ...

    @property
    @abstractmethod
    def base_damage(self) -> int:
        """
        基础伤害
        """
        ...

    @abstractmethod
    def check_crit(self, damage: int, target_member) -> tuple[int, bool]:
        """
        检测是否暴击并输出暴击伤害
        :param target_member: 攻击目标
        :param damage: 原伤害
        :return: 暴击后伤害，是否暴击
        """
        ...

    @abstractmethod
    def attack(
            self,
            enemy,
            fight_event: 'FightEvent',
            damage: DamageData,
            armour_break: float = 0):
        """造成伤害事件
        :param enemy:
        :param armour_break:
        :param fight_event: 'FightEvent':
        :param damage:
        """
        ...

    @abstractmethod
    def impose_effects(
            self,
            enemy,
            buff_id: int,
            fight_event: 'FightEvent',
            num: int = 1,
            must_succeed: bool = False,
            effect_rate_improve: int = 0):
        """
        施加buff动作
        :param enemy: 施加目标
        :param buff_id: 效果id
        :param effect_rate_improve: 额外效果命中
        :param fight_event: 'FightEvent': 消息列表
        :param num: 层数
        :param must_succeed: 是否是必中效果
        :return:
        """
        ...

    @abstractmethod
    def be_back_damage(self,
                       attacker: 'BaseFightMember',
                       fight_event: 'FightEvent',
                       back_damage: int,
                       armour_break: float = 0):
        ...


class FightEvent:
    user_list: dict[int, BaseFightMember] = {}
    msg_list: list[str] = []
    turn_owner: int = 0
    turn_owner_enemy: int = 0
    turn_owner_enemy_all: list[int] = []

    def __init__(self, user_list: dict[int, BaseFightMember]):
        self.user_list = user_list

    def __str__(self):
        return '\r'.join(self.msg_list)

    def add_msg(self, msg):
        self.msg_list.append(msg)

    def find_user(self, user_id: int):
        return self.user_list[user_id]
