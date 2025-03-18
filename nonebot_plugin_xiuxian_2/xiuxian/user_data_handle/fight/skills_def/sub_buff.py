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

    def before_attack_act(self, user: BaseFightMember, target_member: BaseFightMember, msg_list: list[str]) -> None:
        user.increase.atk *= 1 + self.buff / 100
        msg = f"使用功法{self.name}, 攻击力提升{self.buff:.2f}%"
        msg_list.append(msg)
        self.is_final_act = True
        return


class HpMpStealSub(BaseSub):
    """攻击提升辅修效果"""
    is_after_attack_act: bool = True
    """是否有战斗前生效的效果"""

    def __init__(self, sub_buff_info: SubBuff):
        self.hp_steal: float = float(sub_buff_info['buff'])
        self.mp_steal: float = float(sub_buff_info['buff2'])
        self.name: str = sub_buff_info['name']

    def before_attack_act(self, user, target_member, msg_list: list[str]):
        msg_list.append(f"使用功法{self.name}, 获得{self.hp_steal:.2f}%气血吸取，{self.mp_steal:.2f}%真元吸取")

    def after_attack_act(self, user: BaseFightMember, target_member: BaseFightMember, msg_list: list[str]) -> None:
        steal_hp = self.hp_steal / 100 * user.turn_damage
        steal_mp = self.mp_steal / 100 * user.turn_damage
        user.hp += steal_hp
        user.mp += steal_mp
        msg = f"吸取气血：{number_to(steal_hp)}， 吸取真元：{number_to(steal_mp)}"
        msg_list.append(msg)
        return


class HpStealSub(BaseSub):
    """攻击提升辅修效果"""
    is_after_attack_act: bool = True
    """是否有战斗前生效的效果"""

    def __init__(self, sub_buff_info: SubBuff):
        self.hp_steal: float = float(sub_buff_info['buff'])
        self.name: str = sub_buff_info['name']

    def before_attack_act(self, user, target_member, msg_list: list[str]):
        msg_list.append(f"使用功法{self.name}, 获得{self.hp_steal:.2f}%气血吸取")

    def after_attack_act(self, user: BaseFightMember, target_member: BaseFightMember, msg_list: list[str]) -> None:
        steal_hp = self.hp_steal / 100 * user.turn_damage
        user.hp += steal_hp
        msg = f"吸取气血：{number_to(steal_hp)}"
        msg_list.append(msg)
        return


class MpStealSub(BaseSub):
    """攻击提升辅修效果"""
    is_after_attack_act: bool = True
    """是否有战斗前生效的效果"""

    def __init__(self, sub_buff_info: SubBuff):
        self.mp_steal: float = float(sub_buff_info['buff'])
        self.name: str = sub_buff_info['name']

    def before_attack_act(self, user, target_member, msg_list: list[str]):
        msg_list.append(f"使用功法{self.name}, 获得{self.mp_steal:.2f}%真元吸取")

    def after_attack_act(self, user: BaseFightMember, target_member: BaseFightMember, msg_list: list[str]) -> None:
        steal_mp = self.mp_steal / 100 * user.turn_damage
        user.mp += steal_mp
        msg = f"吸取真元：{number_to(steal_mp)}"
        msg_list.append(msg)
        return


SUB_BUFF_ACHIEVE = {'1': AtkIncreaseBuff,
                    '6': HpStealSub,
                    '7': MpStealSub,
                    '9': HpMpStealSub}
