import random

from .fight_base import BaseFightMember, Increase
from .skill_register import register_skills, register_sub
from .skills_def.buff_def import BUFF_ACHIEVE
from ...types.user_info import UserFightInfo
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
        self.rest_turn = 0
        self.armour_break = 0
        self.turn_damage: int = 0
        self.sum_damage: int = 0
        self.turn_kill = False
        self.main_skill = register_skills(user_fight_info['sec_buff_info'])
        self.sub_skill = register_sub(user_fight_info['sub_buff_info'])
        self.buffs = {}
        self.increase = Increase()
        if user_fight_info['ice_mark']:
            ice_mark = BUFF_ACHIEVE[10](self)
            ice_mark.effect_value = user_fight_info['ice_mark']
            self.buffs[ice_mark.name] = ice_mark

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
        if real_damage is None:
            real_damage = [0]
        if normal_damage is None:
            normal_damage = [0]
        defence = self.base_defence + armour_break
        soul_damage = int(sum(normal_damage) * max(attacker.soul_damage_add - self.decrease_soul_damage, 0))
        final_hurt_change = self.final_hurt_change
        final_normal_damage = [int(normal_damage_per * defence * final_hurt_change)
                               for normal_damage_per in normal_damage]
        sum_real_damage = sum(real_damage)
        sum_final_normal_damage = sum(final_normal_damage)
        if random.randint(1, 100) <= (self.miss_rate - attacker.decrease_miss_rate):
            sum_real_damage = 0
            sum_final_normal_damage = 0
            msg_list.append(f"{self.name}催动空间法则，躲开了此次攻击")
        if self.shield > 0 and sum_final_normal_damage:
            self.shield -= sum_final_normal_damage
            if self.shield > 0:
                msg_list.append(f"{self.name}的护盾抵消了"
                                f"所有{number_to(sum_final_normal_damage)}普通伤害，"
                                f"余剩护盾量{number_to(self.shield)}")
                sum_final_normal_damage = 0
            else:
                sum_final_normal_damage -= self.shield
                self.shield = 0
                msg_list.append(f"{self.name}的护盾抵消了"
                                f"{number_to(self.shield)}普通伤害，"
                                f"余剩护盾量0")
        if self.back_damage and sum_final_normal_damage:
            back_damage = int(sum_final_normal_damage * self.back_damage)
            attacker.be_back_damage(self, msg_list, back_damage)
        sum_damage = sum_real_damage + sum_final_normal_damage + soul_damage
        self.hp -= sum_damage
        attacker.turn_damage += sum_damage
        attacker.sum_damage += sum_damage
        normal_damage_msg = '、'.join([number_to(final_normal_damage_per)
                                      for final_normal_damage_per
                                      in final_normal_damage]) + '伤害，' if sum_final_normal_damage else ''
        real_damage_msg = '、'.join([number_to(real_damage_per)
                                    for real_damage_per
                                    in real_damage]) + '真实伤害，' if sum_real_damage else ''
        soul_damage_msg = f"{number_to(soul_damage)}灵魂伤害，" if soul_damage else ''
        if not (sum_real_damage or sum_final_normal_damage or soul_damage_msg):
            msg = f"未对{self.name}造成伤害！！"
            msg_list.append(msg)
            return
        msg = (f"对{self.name}造成了"
               f"{normal_damage_msg}{real_damage_msg}{soul_damage_msg}"
               f"总计{number_to(sum_damage)}伤害！\r"
               f"{self.name}余剩气血{number_to(self.hp)}。")
        msg_list.append(msg)
        if self.hp < 1:
            self.status = 0
            msg = f"{self.name}失去战斗能力！"
            msg_list.append(msg)
        return

    def be_back_damage(self,
                       attacker: BaseFightMember,
                       msg_list: list[str],
                       back_damage: int = None,
                       armour_break: float = 0):
        defence = self.base_defence + armour_break
        back_damage *= defence
        self.hp -= back_damage
        msg_list.append(f"{attacker.name}逆乱因果，转嫁伤害对{self.name}造成{number_to(back_damage)}点伤害")
        if self.hp < 1:
            self.status = 0
            msg = f"{self.name}失去战斗能力！"
            msg_list.append(msg)

    def impose_effects(
            self,
            enemy: BaseFightMember,
            buff_id: int,
            msg_list: list[str],
            num: int = 1,
            must_succeed: bool = False,
            effect_rate_improve: int = 0):
        buff_achieve = BUFF_ACHIEVE[buff_id]
        buff_name = buff_achieve.name
        if buff_name not in enemy.buffs:
            enemy.buffs[buff_name] = buff_achieve(self)
        buff_msg = enemy.buffs[buff_name].add_num(num)
        msg_list.append(f"并为{enemy.name}{buff_msg}")
