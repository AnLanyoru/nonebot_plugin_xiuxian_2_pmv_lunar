from ..damage_data import DamageData
from ....types.skills_info_type import BuffIncreaseDict
from ..fight_base import BaseBuff, BaseFightMember, FightEvent
from ....xiuxian_utils.clean_utils import number_to


class AtkIncrease(BaseBuff):
    name = '攻击伤害附加'
    least_turn = 0
    buff_value: float = 0

    def act(self, effect_user, now_enemy, fight_event):
        msg = f"{effect_user.name}的{self.buff_value:.2f}倍攻击伤害附加效果：{self.name}，余剩{self.least_turn}回合"
        fight_event.add_msg(msg)

    def skill_value_change(self, attack_value: list[float]):
        attack_value.append(self.buff_value)


class DefenceIncrease(BaseBuff):
    name = '减伤增加'
    least_turn = 0
    buff_value: float = 0

    def act(self, effect_user, now_enemy, fight_event):
        msg = f"{effect_user.name}的{self.buff_value * 100:.2f}%减伤增加效果：{self.name}，余剩{self.least_turn}回合"
        fight_event.add_msg(msg)

    def defence_change(self, defence: float, buff_defence_change: BuffIncreaseDict):
        buff_defence_change["add"] += self.buff_value


class FinalDamageIncrease(BaseBuff):
    name = '最终伤害增加'
    least_turn = 0
    buff_value: float = 0
    tips = 1

    def act(self, effect_user, now_enemy, fight_event):
        if self.tips:
            msg = f"{effect_user.name}获得了{self.buff_value * 100:.2f}%{self.name}效果"
            fight_event.add_msg(msg)
            self.tips = 0

    def damage_change(self, damage: int, buff_damage_change: BuffIncreaseDict) -> None:
        buff_damage_change["mul"] *= self.buff_value


class ContinueDamage(BaseBuff):
    name = '无'
    least_turn = 0

    def __init__(self, impose_member: str):
        super().__init__(impose_member)
        self.continue_damage = 0

    def act(self,
            effect_user: BaseFightMember,
            now_enemy: BaseFightMember,
            fight_event):
        impose_member = fight_event.find_user(self.impose_member)
        least_turn_msg = f"，余剩{self.least_turn}回合" if self.least_turn > -1 else ''
        msg = f"{impose_member.name}对{effect_user.name}施加的持续伤害{self.name}生效{least_turn_msg}"
        fight_event.add_msg(msg)
        effect_user.hurt(
            impose_member,
            fight_event,
            damage=DamageData(normal_damage=[self.continue_damage]),
            armour_break=0.2)


class IceMarkCount(BaseBuff):
    num = 0
    max_num = 6
    least_turn = -1
    effect_value = 0
    name = '冰之印记'

    def act(self, effect_user, now_enemy, fight_event):
        self.num += 1
        fight_event.add_msg(f"{effect_user.name}获得了一层冰之印记，当前（{self.num}/6层）")
        if self.num == 6:
            ice_mark = IceMark(effect_user.id)
            ice_mark.effect_value = self.effect_value
            now_enemy.buffs[f'{self.name}&{effect_user.name}'] = ice_mark
            self.least_turn = 0
            happened_msg = f"冰之印记生效，使{now_enemy.name}受到伤害增加{self.effect_value * 100:.2f}%"
            fight_event.add_msg(happened_msg)


class IceMark(BaseBuff):
    num = 1
    max_num = 1
    least_turn = -1
    name = '冰之印记'
    effect_value = 0

    def act(self, effect_user, now_enemy, fight_event):
        pass

    def final_hurt_change(self, damage: int, buff_final_hurt_change: BuffIncreaseDict) -> None:
        """
        实现该方法可以增加或翻倍最终受到伤害倍率
        :param damage: 原始受到伤害倍率
        :param buff_final_hurt_change: {'add': '增加一定数值', 'mul': '翻倍一定数值'}
        """
        buff_final_hurt_change['add'] += self.effect_value


class FireDotCount(BaseBuff):
    num = 0
    max_num = 6
    least_turn = -1
    effect_value = 0
    name = '炽焰印记'

    def act(self, effect_user, now_enemy, fight_event):
        if self.num == 6:
            dot = ContinueDamage(effect_user.id)
            dot.continue_damage = self.effect_value * effect_user.base_damage
            now_enemy.buffs[f'{self.name}&{effect_user.name}'] = dot
            self.least_turn = 0
            happened_msg = f"炽焰印记爆发，使{now_enemy.name}每回合受到{number_to(dot.continue_damage)}持续伤害"
            fight_event.add_msg(happened_msg)

    def be_hurt_act(self,
                    effect_user: BaseFightMember,
                    now_enemy: BaseFightMember,
                    fight_event: FightEvent):
        self.num += 1
        fight_event.add_msg(f"{effect_user.name}获得了一层炽焰印记，当前（{self.num}/6层）")


class SolarCrowPower(BaseBuff):
    """金乌之力"""
    num = 1
    max_num = 1
    least_turn = -1
    effect_num = 1
    effect_value = 0
    effect_save_shield = 0
    name = '金乌之力'

    def act(self,
            effect_user: 'BaseFightMember',
            now_enemy: 'BaseFightMember',
            fight_event: 'FightEvent'):
        if not self.effect_num:
            if effect_user.shield > 0:
                fight_event.add_msg(f"{effect_user.name}的金乌之力提供25%伤害加成")
            else:
                fight_event.add_msg(f"{effect_user.name}的金乌之力破碎失去25%伤害加成")
                self.least_turn = 0

    def be_hurt_act(self,
                    effect_user: 'BaseFightMember',
                    now_enemy: 'BaseFightMember',
                    fight_event: 'FightEvent'):
        if self.effect_num:
            if effect_user.hp_percent < 0.5:
                self.effect_num -= 1
                self.effect_save_shield = int(effect_user.hp_max * self.effect_value)
                effect_user.shield += self.effect_save_shield
                fight_event.add_msg(
                    f"{effect_user.name}的金乌之力爆发，"
                    f"获得{number_to(self.effect_save_shield)}点护盾，"
                    f"护盾存在期间提供25%伤害加成")

    def damage_change(self, damage: int, buff_damage_change: BuffIncreaseDict) -> None:
        if not self.effect_num:
            buff_damage_change['add'] += 0.25


class FireRebirth(BaseBuff):
    num = 1
    max_num = 1
    least_turn = -1
    effect_num = 1
    effect_value = 0
    name = '炎魔之力'

    def be_hurt_act(self,
                    effect_user: 'BaseFightMember',
                    now_enemy: 'BaseFightMember',
                    fight_event: 'FightEvent'):
        if self.effect_num:
            if effect_user.hp_percent < 0.5:
                self.effect_num -= 1
                effect_value = int(effect_user.hp_max * self.effect_value)
                effect_user.hp += effect_value
                fight_event.add_msg(
                    f"{effect_user.name}的{self.name}爆发，"
                    f"恢复{number_to(effect_value)}点生命值")


class FireDamageIncrease(BaseBuff):
    num = 1
    max_num = 1
    least_turn = -1
    effect_num = 1
    effect_value = 0
    name = '烈火焚天'

    def act(self,
            effect_user: 'BaseFightMember',
            now_enemy: 'BaseFightMember',
            fight_event: 'FightEvent'):
        if self.effect_num:
            self.effect_num = 0
            fight_event.add_msg(f"{effect_user.name}的烈火焚天生效，"
                                f"伤害提升{self.effect_value * 100:.2f}%")

    def damage_change(self, damage: int, buff_damage_change: BuffIncreaseDict) -> None:
        buff_damage_change['add'] += self.effect_value


class LightPower(BaseBuff):
    num = 1
    max_num = 1
    least_turn = -1
    effect_num = 1
    effect_value = 0
    name = '雷霆神力'

    def be_hurt_act(self,
                    effect_user: 'BaseFightMember',
                    now_enemy: 'BaseFightMember',
                    fight_event: 'FightEvent'):
        if self.effect_num:
            if effect_user.hp_percent < 0.5:
                self.effect_num -= 1
                fight_event.add_msg(
                    f"{effect_user.name}的{self.name}爆发，"
                    f"伤害提升{self.effect_value * 100:.2f}%")

    def damage_change(self, damage: int, buff_damage_change: BuffIncreaseDict) -> None:
        if not self.effect_num:
            buff_damage_change['add'] += self.effect_value


class HaoTianPower(BaseBuff):
    num = 1
    max_num = 1
    least_turn = -1
    effect_value = 0
    real_effect_value = 0
    name = '昊天神力'

    def act(self,
            effect_user: 'BaseFightMember',
            now_enemy: 'BaseFightMember',
            fight_event: 'FightEvent'):
        self.real_effect_value = ((1 - effect_user.hp_percent) // 0.1) * self.effect_value
        if self.real_effect_value > 0:
            fight_event.add_msg(f"{effect_user.name}的昊天神力使其"
                                f"伤害提升{self.real_effect_value * 100:.2f}%")

    def damage_change(self, damage: int, buff_damage_change: BuffIncreaseDict) -> None:
        buff_damage_change['add'] += self.real_effect_value


class StarSoul(BaseBuff):
    num = 1
    max_num = 1
    least_turn = -1
    effect_num = 1
    effect_value = 0
    name = '星魂之力'

    def act(self,
            effect_user: 'BaseFightMember',
            now_enemy: 'BaseFightMember',
            fight_event: 'FightEvent'):
        if effect_user.hp_percent > 0.5:
            self.effect_num = 1
            fight_event.add_msg(
                f"{effect_user.name}的{self.name}使其"
                f"伤害提升{self.effect_value * 100:.2f}%")
        else:
            self.effect_num = 0
            fight_event.add_msg(
                f"{effect_user.name}的{self.name}失效，失去伤害提升效果")

    def final_hurt_change(self, damage: int, buff_final_hurt_change: BuffIncreaseDict) -> None:
        if self.effect_num:
            buff_final_hurt_change['add'] += self.effect_value


BUFF_ACHIEVE = {1: AtkIncrease,
                2: DefenceIncrease,
                3: ContinueDamage,
                '增伤': FinalDamageIncrease,
                '冰之印记': IceMarkCount,
                11: IceMark,
                '炽焰': FireDotCount,
                '金乌': SolarCrowPower,
                '炎魔': FireRebirth,
                '烈火焚天': FireDamageIncrease,
                '雷霆': LightPower,
                '昊天神力': HaoTianPower,
                '星魂之力': StarSoul,
                }


def get_base_buff(buff_id: int, user_id: str) -> BaseBuff:
    return BUFF_ACHIEVE[buff_id](user_id)
