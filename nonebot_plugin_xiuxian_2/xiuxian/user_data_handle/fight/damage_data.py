from ...xiuxian_utils.clean_utils import number_to


class DamageData:
    """伤害类"""
    normal_damage: list[int] = []
    real_damage: list[int] = []
    soul_damage: list[int] = []
    reduce_damage = 0
    type: str = ''

    def __init__(self,
                 normal_damage: list[int] = None,
                 real_damage: list[int] = None,
                 soul_damage: list[int] = None,
                 damage_type: str = ''):
        if soul_damage is None:
            soul_damage = []
        if real_damage is None:
            real_damage = []
        if normal_damage is None:
            normal_damage = []
        self.normal_damage = normal_damage
        self.real_damage = real_damage
        self.soul_damage = soul_damage
        self.type = damage_type

    def __add__(self, other):
        if isinstance(other, DamageData):
            return DamageData(
                self.normal_damage + other.normal_damage,
                self.real_damage + other.real_damage,
                self.soul_damage + other.soul_damage)

    def __iadd__(self, other):
        self.normal_damage.extend(other.normal_damage),
        self.real_damage.extend(other.real_damage),
        self.soul_damage.extend(other.soul_damage)
        return self

    def __isub__(self, other):
        if isinstance(other, DamageData):
            self.reduce_damage += other.all_sum
        elif isinstance(other, int):
            self.reduce_damage += other
        elif isinstance(other, float):
            self.reduce_damage += other
        else:
            raise TypeError(f'伤害类型不能减去{other}')

    def __str__(self):
        normal_damage_msg = '、'.join([number_to(final_normal_damage_per)
                                      for final_normal_damage_per
                                      in self.normal_damage]) + '伤害，' if self.normal_sum else ''
        real_damage_msg = '、'.join([number_to(real_damage_per)
                                    for real_damage_per
                                    in self.real_damage]) + '真实伤害，' if self.real_sum else ''
        soul_damage_msg = '、'.join([number_to(soul_damage_per)
                                    for soul_damage_per
                                    in self.soul_damage]) + '神魂伤害，' if self.soul_sum else ''
        reduce_msg = f"被抵消{number_to(self.reduce_damage)}伤害，" if self.reduce_damage else ''
        damage_msg = f"{normal_damage_msg}{real_damage_msg}{soul_damage_msg}{reduce_msg}"
        return damage_msg

    @property
    def all_sum(self) -> int:
        sum_damage = (sum(self.normal_damage)
                      + sum(self.real_damage)
                      + sum(self.soul_damage)
                      - self.reduce_damage)
        return sum_damage

    @property
    def normal_sum(self) -> int:
        sum_damage = sum(self.normal_damage) - self.reduce_damage
        return sum_damage

    @property
    def real_sum(self) -> int:
        sum_damage = sum(self.real_damage)
        return sum_damage

    @property
    def soul_sum(self) -> int:
        sum_damage = sum(self.soul_damage)
        return sum_damage

    def effect(self, effect_mul: float):
        self.normal_damage = [int(normal_damage_per * effect_mul)
                              for normal_damage_per in self.normal_damage]

    def reset_all(self):
        self.normal_damage = []
        self.real_damage = []
        self.soul_damage = []

    def reset_normal(self):
        self.normal_damage = []

    def reset_real(self):
        self.real_damage = []

    def reset_soul(self):
        self.soul_damage = []
