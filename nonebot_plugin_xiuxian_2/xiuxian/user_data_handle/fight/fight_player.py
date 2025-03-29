from __future__ import annotations

import random
from .damage_data import DamageData
from .fight_base import BaseFightMember, Increase, FightEvent
from .skill_register import register_skills, register_sub, register_suits_buff, register_suits_sub
from .skills_def.buff_def import BUFF_ACHIEVE
from ...types.user_info import UserFightInfo
from ...xiuxian_utils.clean_utils import number_to


class PlayerFight(BaseFightMember):

    def __init__(self, user_fight_info: UserFightInfo, team):
        """实例化"""
        self.team = team
        self.id = user_fight_info['user_id']
        self.name = user_fight_info['user_name']
        self.hp = user_fight_info['fight_hp']
        self.hp_max = user_fight_info['max_hp']
        self.mp = user_fight_info['fight_mp']
        self.base_mp = user_fight_info['base_mp']
        self.mp_max = user_fight_info['max_mp']
        self.atk = user_fight_info['atk']
        self.crit = user_fight_info['crit']
        self.burst = user_fight_info['burst']
        self.defence = user_fight_info['defence']
        self.miss_rate: int = user_fight_info['miss_rate']
        """空间穿梭（闪避率）"""
        self.decrease_miss_rate: int = user_fight_info['decrease_miss_rate']
        """空间封锁（减少对方闪避率）"""
        self.decrease_crit: int = user_fight_info['decrease_crit']
        """减少对方暴击率"""
        self.soul_damage_add: float = user_fight_info['soul_damage_add']
        """灵魂伤害（真实伤害）"""
        self.decrease_soul_damage: float = user_fight_info['decrease_soul_damage']
        """灵魂抵抗（减少对方真实伤害）"""
        self.shield: int = int(user_fight_info['shield'] * self.hp_max)
        """开局护盾"""
        self.back_damage: float = user_fight_info['back_damage']
        """反伤"""
        self.main_skill = register_skills(user_fight_info['sec_buff_info'])
        self.sub_skill = register_sub(user_fight_info['sub_buff_info'])
        self.buffs.update(register_suits_buff(self.id, user_fight_info['new_equipment_buff']))
        self.sub_skill.update(register_suits_sub(user_fight_info['new_equipment_buff']))
        self.increase = Increase()

    @property
    def base_damage(self) -> int:
        damage = self.atk * self.increase.atk
        buff_damage_change = {'add': 0,
                              'mul': 1}
        for buff in self.buffs.values():
            buff.damage_change(damage, buff_damage_change)
        damage += buff_damage_change['add']
        damage *= buff_damage_change['mul']
        return damage

    @property
    def base_defence(self):
        defence = self.defence
        buff_defence_change = {'add': 0,
                               'mul': 1}
        for buff in self.buffs.values():
            buff.defence_change(defence, buff_defence_change)
        defence = min(max(defence - buff_defence_change['add'], 0.1), defence)
        defence *= buff_defence_change['mul']
        return defence

    @property
    def final_hurt_change(self):
        final_hurt_change = 1
        buff_final_hurt_change = {'add': 0,
                                  'mul': 1}
        for buff in self.buffs.values():
            buff.final_hurt_change(final_hurt_change, buff_final_hurt_change)
        final_hurt_change = max(final_hurt_change + buff_final_hurt_change['add'], 0)
        final_hurt_change *= buff_final_hurt_change['mul']
        return final_hurt_change

    def check_crit(self, damage: int, target_member: BaseFightMember) -> tuple[int, bool]:
        """
        检测是否暴击并输出暴击伤害
        :param target_member: 攻击目标
        :param damage: 原伤害
        :return: 暴击后伤害，是否暴击
        """
        crit_rate = self.crit + self.increase.crit
        buff_crit_change = {'add': 0,
                            'mul': 1}
        for buff in self.buffs.values():
            buff.crit_change(crit_rate, buff_crit_change)
        crit_rate += buff_crit_change['add']
        crit_rate *= buff_crit_change['mul']

        burst = self.burst + self.increase.burst
        buff_burst_change = {'add': 0,
                             'mul': 1}
        for buff in self.buffs.values():
            buff.burst_change(burst, buff_burst_change)
        burst += buff_burst_change['add']
        burst *= buff_burst_change['mul']

        if random.randint(1, 100) <= (crit_rate - target_member.decrease_crit):  # 会心判断
            return int(damage * burst), True
        return damage, False

    def check_shield(self, damage: DamageData):
        sum_final_normal_damage = damage.normal_sum
        shield_msg = ''
        if self.shield > 0 and sum_final_normal_damage:
            origin_shield = self.shield
            origin_shield -= sum_final_normal_damage
            if origin_shield > 0:
                self.shield -= sum_final_normal_damage
                shield_msg = (f"{self.name}的护盾抵消了"
                              f"所有{number_to(sum_final_normal_damage)}普通伤害，"
                              f"余剩护盾量{number_to(self.shield)}")
                damage.reset_normal()
            else:
                damage -= self.shield
                shield_msg = (f"{self.name}的护盾抵消了"
                              f"{number_to(self.shield)}普通伤害，"
                              f"余剩护盾量0")
                self.shield = 0
        return shield_msg

    def attack(self,
               enemy: BaseFightMember,
               fight_event,
               damage,
               armour_break: float = 0):
        """
        造成伤害接口
        :param armour_break: 破甲
        :param damage: 伤害
        :param enemy: 伤害目标
        :param fight_event: 'FightEvent': 战斗消息列表
        :return:
        """
        armour_break = armour_break + self.armour_break
        enemy.hurt(
            attacker=self,
            fight_event=fight_event,
            damage=damage,
            armour_break=armour_break)

    def hurt(self,
             attacker: BaseFightMember,
             fight_event: FightEvent,
             damage: DamageData,
             armour_break: float = 0):
        """
        受伤接口
        future: 护盾系统
        :param damage:
        :param attacker: 攻击者
        :param fight_event: FightEvent: 战斗信息列表
        :param armour_break: 受到的破甲
        :return:
        """
        defence = self.base_defence + armour_break
        damage.soul_damage.append(int(
            damage.normal_sum * max(attacker.soul_damage_add - self.decrease_soul_damage, 0)))
        final_hurt_change = self.final_hurt_change
        damage.effect(defence * final_hurt_change)
        if random.randint(1, 100) <= (self.miss_rate - attacker.decrease_miss_rate):
            damage.reset_normal()
            fight_event.add_msg(f"{self.name}催动空间法则，躲开了此次攻击")
        shield_msg = self.check_shield(damage)
        if shield_msg:
            fight_event.add_msg(shield_msg)
        if self.back_damage and damage.normal_sum:
            back_damage = int(damage.normal_sum * self.back_damage)
            attacker.be_back_damage(self, fight_event, back_damage)
        self.hp -= damage.all_sum
        attacker.just_damage = damage
        attacker.turn_damage += damage
        attacker.sum_damage += damage
        if not damage.all_sum:
            msg = f"未对{self.name}造成伤害！！"
            fight_event.add_msg(msg)
            return
        msg = (f"对{self.name}造成了"
               f"{damage}\r"
               f"总计造成{number_to(damage.all_sum)}伤害！")
        fight_event.add_msg(msg)
        attacker.just_attack_act(self, fight_event)
        fight_event.add_msg(f"{self.name}余剩气血{number_to(self.hp)}({self.hp_percent_str})。")
        self.be_hurt_buff_act(attacker, fight_event)
        if self.hp < 1:
            self.status = 0
            msg = f"{self.name}失去战斗能力！"
            fight_event.add_msg(msg)
        return

    def be_back_damage(self,
                       attacker: BaseFightMember,
                       fight_event,
                       back_damage: int,
                       armour_break: float = 0):
        defence = self.base_defence + armour_break
        back_damage *= defence
        attacker.turn_damage.normal_damage.append(back_damage)
        attacker.sum_damage.normal_damage.append(back_damage)
        self.hp -= back_damage
        fight_event.add_msg(f"{attacker.name}逆乱因果，转嫁伤害对{self.name}造成{number_to(back_damage)}点伤害")
        if self.hp < 1:
            self.status = 0
            msg = f"{self.name}失去战斗能力！"
            fight_event.add_msg(msg)

    def impose_effects(
            self,
            enemy: BaseFightMember,
            buff_id: int,
            fight_event,
            num: int = 1,
            must_succeed: bool = False,
            effect_rate_improve: int = 0):
        buff_achieve = BUFF_ACHIEVE[buff_id]
        buff_name = buff_achieve.name
        if buff_name not in enemy.buffs:
            enemy.buffs[buff_name] = buff_achieve(self)
        buff_msg = enemy.buffs[buff_name].add_num(num)
        fight_event.add_msg(f"并为{enemy.name}{buff_msg}")
