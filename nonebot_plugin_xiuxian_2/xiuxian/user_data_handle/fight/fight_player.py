from .fight_base import Increase
from .fight_member import FightMember
from .skill_register import register_skills, register_sub, register_suits_buff, register_suits_sub
from ...types.user_info import UserFightInfo


class PlayerFight(FightMember):

    def __init__(self, user_fight_info: UserFightInfo, team):
        """实例化"""
        super().__init__()
        self.team = team
        self.id = str(user_fight_info['user_id'])
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
