from ....types.skills_info_type import BuffIncreaseDict
from ..fight_base import BaseBuff, BaseFightMember


class AtkIncrease(BaseBuff):
    name = '攻击伤害附加'
    least_turn = 0
    buff_value: float = 0

    def act(self, effect_user, now_enemy, msg_list: list[str]):
        msg = f"{effect_user.name}的{self.buff_value:.2f}倍攻击伤害附加效果：{self.name}，余剩{self.least_turn}回合"
        msg_list.append(msg)

    def skill_value_change(self, attack_value: list[float]):
        attack_value.append(self.buff_value)


class DefenceIncrease(BaseBuff):
    name = '减伤增加'
    least_turn = 0
    buff_value: float = 0

    def act(self, effect_user, now_enemy, msg_list: list[str]):
        msg = f"{effect_user.name}的{self.buff_value * 100:.2f}%减伤增加效果：{self.name}，余剩{self.least_turn}回合"
        msg_list.append(msg)

    def defence_change(self, defence: float, buff_defence_change: BuffIncreaseDict):
        buff_defence_change["add"] += self.buff_value



class ContinueDamage(BaseBuff):
    name = '无'
    least_turn = 0

    def __init__(self, impose_member: BaseFightMember):
        super().__init__(impose_member)
        self.continue_damage = 0

    def act(self,
            effect_user: BaseFightMember,
            now_enemy: BaseFightMember,
            msg_list: list[str]):
        msg = f"{self.impose_member.name}对{effect_user.name}施加的持续伤害{self.name}生效，余剩{self.least_turn}回合"
        msg_list.append(msg)
        effect_user.hurt(
            self.impose_member,
            msg_list,
            normal_damage=[self.continue_damage],
            armour_break=0.2)


class Known(BaseBuff):
    num = 0
    max_num = 42
    least_turn = -1
    name = '解读'

    def act(self, effect_user, now_enemy, msg_list: list[str]):
        pass


class IceMarkCount(BaseBuff):
    num = 0
    max_num = 6
    least_turn = -1
    effect_value = 0
    name = '冰之印记'

    def act(self, effect_user: BaseFightMember, now_enemy: BaseFightMember, msg_list: list[str]):
        msg_list.append(f"{effect_user.name}获得了一层冰之印记，当前（{self.num}/6层）")
        self.num += 1
        happened_msg = ''
        if self.num == 6:
            ice_mark = IceMark(effect_user)
            ice_mark.effect_value = self.effect_value
            now_enemy.buffs[f'{self.name}&{effect_user.name}'] = ice_mark
            self.least_turn = 0
            happened_msg = f"冰之印记生效，使{now_enemy.name}受到伤害增加{self.effect_value * 100:.2f}%"
            msg_list.append(happened_msg)


class IceMark(BaseBuff):
    num = 1
    max_num = 1
    least_turn = -1
    name = '冰之印记'
    effect_value = 0

    def act(self, effect_user, now_enemy, msg_list: list[str]):
        pass

    def final_hurt_change(self, damage: int, buff_final_hurt_change: BuffIncreaseDict) -> None:
        """
        实现该方法可以增加或翻倍最终受到伤害倍率
        :param damage: 原始受到伤害倍率
        :param buff_final_hurt_change: {'add': '增加一定数值', 'mul': '翻倍一定数值'}
        """
        buff_final_hurt_change['add'] += self.effect_value


BUFF_ACHIEVE = {1: AtkIncrease,
                2: DefenceIncrease,
                3: ContinueDamage,
                10: IceMarkCount,
                11: IceMark,
                1000: Known}
