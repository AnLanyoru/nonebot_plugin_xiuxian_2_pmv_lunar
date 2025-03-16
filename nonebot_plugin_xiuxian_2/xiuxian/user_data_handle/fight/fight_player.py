import random

from .fight_base import BaseFightMember, Increase
from .skill_register import register_skills
from ...types import UserFightInfo
from ...xiuxian_utils.clean_utils import number_to


class PlayerFight(BaseFightMember):

    def __init__(self, user_fight_info: UserFightInfo, team):
        """实例化"""
        self.team = team
        self.status = 1
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
        self.rest_turn = 0
        self.armour_break = 0
        self.turn_damage: int = 0
        self.sum_damage: int = 0
        self.main_skill = register_skills(user_fight_info['sec_buff_info'])
        self.sub_skill = register_skills(user_fight_info['sub_buff_info'])
        self.buffs = []
        self.increase = Increase()

    @property
    def base_damage(self) -> int:
        damage = self.atk * self.increase.atk
        buff_damage_change = {'add': 0,
                              'mul': 0}
        for buff in self.buffs:
            buff.damage_change(damage, buff_damage_change)
        damage += buff_damage_change['add']
        damage *= buff_damage_change['mul']
        return damage

    def check_crit(self, damage: int) -> tuple[int, bool]:
        """
        检测是否暴击并输出暴击伤害
        :param damage: 原伤害
        :return: 暴击后伤害，是否暴击
        """
        crit_rate = self.crit + self.increase.crit
        buff_crit_change = {'add': 0,
                            'mul': 0}
        for buff in self.buffs:
            buff.crit_change(crit_rate, buff_crit_change)
        crit_rate += buff_crit_change['add']
        crit_rate *= buff_crit_change['mul']

        burst = self.burst + self.increase.burst
        buff_burst_change = {'add': 0,
                             'mul': 0}
        for buff in self.buffs:
            buff.burst_change(burst, buff_burst_change)
        burst += buff_burst_change['add']
        burst *= buff_burst_change['mul']

        if random.randint(0, 100) <= crit_rate:  # 会心判断
            return int(damage * burst), True
        return damage, False

    def attack(
            self,
            enemy: BaseFightMember,
            msg_list: list[str],
            normal_damage: list[int] = None,
            real_damage: list[int] = None,
            temp_armour_break: float = 0):
        """
        造成伤害接口
        :param enemy: 伤害目标
        :param msg_list: 战斗消息列表
        :param normal_damage: 造成的普通伤害
        :param real_damage: 造成的真实伤害
        :param temp_armour_break: 临时破甲提升
        :return:
        """
        armour_break = temp_armour_break + self.armour_break
        enemy.hurt(
            attacker=self,
            msg_list=msg_list,
            normal_damage=normal_damage,
            real_damage=real_damage,
            armour_break=armour_break)

    def hurt(self,
             attacker: BaseFightMember,
             msg_list: list[str],
             normal_damage: list[int] = None,
             real_damage: list[int] = None,
             armour_break: float = 0):
        """
        受伤接口
        future: 护盾系统
        :param attacker: 攻击者
        :param msg_list: 战斗信息列表
        :param normal_damage: 造成的普通伤害
        :param real_damage: 造成的真实伤害
        :param armour_break: 受到的破甲
        :return:
        """
        defence = self.defence
        buff_defence_change = {'add': 0,
                               'mul': 0}
        for buff in self.buffs:
            buff.burst_change(defence, buff_defence_change)
        defence += buff_defence_change['add']
        defence *= buff_defence_change['mul']
        final_normal_damage = [int(normal_damage_per * defence) for normal_damage_per in normal_damage]
        sum_damage = sum(real_damage) + sum(final_normal_damage)
        self.hp -= sum_damage
        attacker.turn_damage += sum_damage
        attacker.sum_damage += sum_damage
        normal_damage_msg = '、'.join([number_to(final_normal_damage_per)
                                      for final_normal_damage_per
                                      in final_normal_damage]) + '伤害!' if final_normal_damage else ''
        real_damage_msg = '、'.join([number_to(real_damage_per)
                                    for real_damage_per
                                    in real_damage]) + '真实伤害!' if real_damage else ''
        if not (normal_damage_msg or real_damage_msg):
            msg = f"未对{self.name}造成伤害！！"
            msg_list.append(msg)
            return
        msg = f"对{self.name}造成了{normal_damage_msg}{real_damage_msg}，总计{number_to(sum_damage)}伤害"
        msg_list.append(msg)
        if self.hp < 1:
            self.status = 0
            msg = f"{self.name}失去战斗能力！"
            msg_list.append(msg)
        return
