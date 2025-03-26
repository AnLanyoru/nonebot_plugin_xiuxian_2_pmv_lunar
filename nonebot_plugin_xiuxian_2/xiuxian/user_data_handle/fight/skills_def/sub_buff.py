from ..fight_base import BaseSub, BaseFightMember
from ....types.skills_info_type import SubBuff
from ....xiuxian_utils.clean_utils import number_to


class AtkIncreaseBuff(BaseSub):
    """攻击提升辅修效果"""
    is_before_attack_act: bool = True
    """是否有战斗前生效的效果"""

    def __init__(self, sub_buff_info: SubBuff):
        self.buff: float = float(sub_buff_info['buff'])
        self.name: str = sub_buff_info['name']

    def before_attack_act(self, user: BaseFightMember, target_member: BaseFightMember, fight_event) -> None:
        user.increase.atk *= 1 + self.buff / 100
        msg = f"使用功法{self.name}, 攻击力提升{self.buff:.2f}%"
        fight_event.add_msg(msg)
        self.is_final_act = True
        return


class CritIncreaseBuff(BaseSub):
    """暴击率增加辅修效果"""
    is_before_attack_act: bool = True
    """是否有战斗前生效的效果"""

    def __init__(self, sub_buff_info: SubBuff):
        self.buff: float = float(sub_buff_info['buff'])
        self.name: str = sub_buff_info['name']

    def before_attack_act(self, user: BaseFightMember, target_member: BaseFightMember, fight_event) -> None:
        user.increase.crit += self.buff
        msg = f"使用功法{self.name}, 暴击率增加{self.buff:.2f}%"
        fight_event.add_msg(msg)
        self.is_final_act = True
        return


class BurstIncreaseBuff(BaseSub):
    """暴击伤害增加辅修效果"""
    is_before_attack_act: bool = True
    """是否有战斗前生效的效果"""

    def __init__(self, sub_buff_info: SubBuff):
        self.buff: float = float(sub_buff_info['buff'])
        self.name: str = sub_buff_info['name']

    def before_attack_act(self, user: BaseFightMember, target_member: BaseFightMember, fight_event) -> None:
        user.increase.burst += self.buff / 100
        msg = f"使用功法{self.name}, 暴击伤害增加{self.buff:.2f}%"
        fight_event.add_msg(msg)
        self.is_final_act = True
        return


class HpMpStealSub(BaseSub):
    """攻击提升辅修效果"""
    is_just_attack_act: bool = True
    is_before_attack_act = True
    """是否有战斗前生效的效果"""
    hp_steal: float = 0
    mp_steal: float = 0

    def __init__(self, sub_buff_info: SubBuff):
        buff_type = sub_buff_info['buff_type']
        if buff_type == '9':
            self.hp_steal: float = float(sub_buff_info['buff'])
            self.mp_steal: float = float(sub_buff_info['buff2'])
        elif buff_type == '6':
            self.hp_steal: float = float(sub_buff_info['buff'])
        elif buff_type == '7':
            self.mp_steal: float = float(sub_buff_info['buff'])

        self.name: str = sub_buff_info['name']

    def before_attack_act(self, user, target_member, fight_event):
        steal_msg = []
        if self.hp_steal:
            steal_msg.append(f"获得{self.hp_steal:.2f}%气血吸取")
        if self.mp_steal:
            steal_msg.append(f"{self.mp_steal:.2f}%真元吸取")
        steal_msg = '、'.join(steal_msg)
        fight_event.add_msg(f"使用功法{self.name}, 获得{steal_msg}")

    def just_attack_act(self, user: BaseFightMember, target_member: BaseFightMember, fight_event) -> None:
        if not (sum_normal_damage := user.turn_damage.normal_sum):
            return
        steal_hp = self.hp_steal / 100 * sum_normal_damage
        steal_mp = self.mp_steal / 100 * sum_normal_damage
        steal_hp = steal_hp if steal_hp + user.hp < user.hp_max else max(user.hp_max - user.hp, 0)
        steal_mp = steal_mp if steal_mp + user.mp < user.mp_max else max(user.mp_max - user.mp, 0)
        user.hp += steal_hp
        user.mp += steal_mp
        steal_msg = []
        if self.hp_steal:
            steal_msg.append(f"吸取气血：{number_to(steal_hp)}")
        if self.mp_steal:
            steal_msg.append(f"吸取真元：{number_to(steal_mp)}")
        steal_msg = '、'.join(steal_msg)
        msg = f"{user.name}从造成伤害中{steal_msg}"
        fight_event.add_msg(msg)
        return


class HPMPRecoverBuff(BaseSub):
    """攻击提升辅修效果"""
    is_after_attack_act: bool = True
    """是否有攻击后生效的效果"""
    hp_steal: float = 0
    mp_steal: float = 0

    def __init__(self, sub_buff_info: SubBuff):
        buff_type = sub_buff_info['buff_type']
        if buff_type == '4':
            self.hp_steal: float = float(sub_buff_info['buff'])
        elif buff_type == '5':
            self.mp_steal: float = float(sub_buff_info['buff'])

        self.name: str = sub_buff_info['name']

    def after_attack_act(self, user: BaseFightMember, target_member: BaseFightMember, fight_event) -> None:
        steal_hp = self.hp_steal / 100 * user.hp_max
        steal_mp = self.mp_steal / 100 * user.mp_max
        steal_hp = steal_hp if steal_hp + user.hp < user.hp_max else max(user.hp_max - user.hp, 0)
        steal_mp = steal_mp if steal_mp + user.mp < user.mp_max else max(user.mp_max - user.mp, 0)
        user.hp += steal_hp
        user.mp += steal_mp
        steal_msg = []
        if self.hp_steal:
            steal_msg.append(f"恢复气血：{number_to(steal_hp)}")
        if self.mp_steal:
            steal_msg.append(f"恢复真元：{number_to(steal_mp)}")
        steal_msg = '、'.join(steal_msg)
        msg = f"{user.name}通过功法{self.name}:{steal_msg}"
        fight_event.add_msg(msg)
        return


SUB_BUFF_ACHIEVE = {'1': AtkIncreaseBuff,
                    '2': CritIncreaseBuff,
                    '3': BurstIncreaseBuff,
                    '4': HPMPRecoverBuff,
                    '5': HPMPRecoverBuff,
                    '6': HpMpStealSub,
                    '7': HpMpStealSub,
                    '9': HpMpStealSub}

SUITS_BUFF_ACHIEVE = {}
