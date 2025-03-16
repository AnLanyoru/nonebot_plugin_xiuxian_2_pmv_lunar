from ..fight_base import BaseFightMember, BaseSkill
from ....types.skills_info_type import SecBuff


class DirectDamageSkill(BaseSkill):
    """直接伤害"""

    def __init__(self, sec_buff_info: SecBuff):
        self.atk_value: list[float] = sec_buff_info['atkvalue']
        self.desc = sec_buff_info['desc']
        self.cost_hp = sec_buff_info['hpcost']
        self.cost_mp = sec_buff_info['mpcost']
        self.use_rate = sec_buff_info['rate']
        self.rest_turn = sec_buff_info['turncost']

    def achieve(self,
                user: BaseFightMember,
                target_member: BaseFightMember,
                msg_list: list[str]):
        """行动实现"""
        base_damage = user.base_damage
        normal_damages = [int(base_damage * atk_value_per) for atk_value_per in self.atk_value]
        user.attack(enemy=target_member, normal_damage=normal_damages, msg_list=msg_list)


SEC_BUFF_ACHIEVE = {'1': DirectDamageSkill}
