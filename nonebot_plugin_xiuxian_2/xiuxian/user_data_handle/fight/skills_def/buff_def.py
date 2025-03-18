from ..fight_base import BaseBuff, BaseFightMember


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


BUFF_ACHIEVE = {1: ContinueDamage,
                1000: Known}
