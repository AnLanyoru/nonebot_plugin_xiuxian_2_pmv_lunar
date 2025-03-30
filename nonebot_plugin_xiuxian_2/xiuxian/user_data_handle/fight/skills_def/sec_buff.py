import random

from .buff_def import get_base_buff
from ..damage_data import DamageData
from ..fight_base import BaseFightMember, BaseSkill
from ....types.error import UndefinedError
from ....types.skills_info_type import SecBuff
from ....xiuxian_utils.clean_utils import number_to
from ....xiuxian_utils.item_json import items


class DirectDamageSkill(BaseSkill):
    """直接伤害"""

    def __init__(self, sec_buff_info: SecBuff):
        super().__init__(sec_buff_info)
        self.atk_value: list[float] = sec_buff_info['atkvalue']
        self.rest_turn = sec_buff_info['turncost']

    def achieve(self,
                user: BaseFightMember,
                target_member: BaseFightMember,
                base_damage: int,
                fight_event):
        """行动实现"""
        temp_atk_value = self.atk_value.copy()
        for buff in user.buffs.values():
            buff.skill_value_change(temp_atk_value)
        damage = DamageData(normal_damage=[int(base_damage * atk_value_per) for atk_value_per in temp_atk_value])
        user.attack(enemy=target_member, fight_event=fight_event, damage=damage)


class ContinueDamageSkill(BaseSkill):
    """
    持续伤害
    """

    def __init__(self, sec_buff_info: SecBuff):
        super().__init__(sec_buff_info)
        self.atk_value: float = sec_buff_info['atkvalue']
        self.continue_turn = sec_buff_info['turncost'] + 1

    @staticmethod
    def act_base_damage(user, target_member) -> tuple[int, str]:
        """不检定暴击效果"""
        base_damage = user.base_damage
        crit_msg = ''
        return base_damage, crit_msg

    def achieve(self,
                user: BaseFightMember,
                target_member: BaseFightMember,
                base_damage: int,
                fight_event):
        """行动实现"""
        buff_obj = get_base_buff(3, user.id)
        buff_obj.name = self.name
        buff_obj.continue_damage = int(base_damage * self.atk_value)
        buff_obj.least_turn = self.continue_turn
        target_member.buffs[buff_obj.name] = buff_obj
        fight_event.add_msg(f"使{target_member.name}"
                            f"每回合受到{number_to(buff_obj.continue_damage)}点伤害，"
                            f"持续{buff_obj.least_turn - 1}回合")
        self.normal_attack(user, target_member, fight_event)

    def use_check(self, user, target_member, fight_event) -> tuple[str, bool]:
        if self.name in target_member.buffs:
            return '', False
        return super().use_check(user, target_member, fight_event)


class MakeBuffSkill(BaseSkill):
    """
    给自己上buff
    """

    def __init__(self, sec_buff_info: SecBuff):
        super().__init__(sec_buff_info)
        self.buff_type = sec_buff_info['bufftype']
        self.buff_value: float = sec_buff_info['buffvalue']
        self.continue_turn = sec_buff_info['turncost'] + 1

    @staticmethod
    def act_base_damage(user, target_member) -> tuple[int, str]:
        """不检定暴击效果"""
        return 0, ''

    def achieve(self,
                user: BaseFightMember,
                target_member: BaseFightMember,
                base_damage: int,
                fight_event):
        """行动实现"""
        if self.buff_type not in [1, 2]:
            raise UndefinedError(f"未定义的神通buff类型: <buff_type {self.buff_type}>")
        buff_obj = get_base_buff(self.buff_type, user.id)
        if self.buff_type == 1:
            buff_msg = f"{self.buff_value:.2f}倍{buff_obj.name}"
        else:
            buff_msg = f"{self.buff_value * 100:.2f}%{buff_obj.name}"
        buff_obj.name = self.name
        buff_obj.buff_value = self.buff_value
        buff_obj.least_turn = self.continue_turn
        user.buffs[buff_obj.name] = buff_obj
        fight_event.add_msg(f"{user.name}获得了{buff_msg},"
                            f"持续{buff_obj.least_turn - 1}回合")
        self.normal_attack(user, target_member, fight_event)

    def use_check(self, user, target_member, fight_event) -> tuple[str, bool]:
        if self.name in user.buffs:
            return '', False
        return super().use_check(user, target_member, fight_event)


class SealSkill(BaseSkill):
    """
    持续伤害
    """

    def __init__(self, sec_buff_info: SecBuff):
        super().__init__(sec_buff_info)
        self.success_rate = sec_buff_info['success']
        self.seal_turn = sec_buff_info['turncost']

    @staticmethod
    def act_base_damage(user, target_member) -> tuple[int, str]:
        """不检定暴击效果"""
        return 0, ''

    def achieve(self,
                user: BaseFightMember,
                target_member: BaseFightMember,
                base_damage: int,
                fight_event):
        """行动实现"""
        if random.randint(0, 100) > self.success_rate:  # 随机概率释放技能
            msg = f"将{target_member.name}四周空间封禁，但被其身法躲避"
        else:
            msg = f"将{target_member.name}四周空间封禁，将其禁锢在原地{self.seal_turn}回合无法动弹！"
            target_member.rest_turn += self.seal_turn
        fight_event.add_msg(msg)
        self.normal_attack(user, target_member, fight_event)

    def use_check(self, user, target_member: BaseFightMember, fight_event) -> tuple[str, bool]:
        if target_member.rest_turn:
            return '', False
        return super().use_check(user, target_member, fight_event)


SEC_BUFF_ACHIEVE = {1: DirectDamageSkill,
                    2: ContinueDamageSkill,
                    3: MakeBuffSkill,
                    4: SealSkill,
                    }
