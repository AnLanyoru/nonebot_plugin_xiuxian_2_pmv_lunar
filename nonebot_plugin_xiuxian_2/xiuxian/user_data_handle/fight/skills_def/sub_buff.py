from ..fight_base import BaseSub, BaseFightMember
from ....types.skills_info_type import SubBuff


class AtkIncreaseBuff(BaseSub):
    """攻击提升辅修效果"""
    is_after_attack_act: bool = 1
    """是否有战斗前生效的效果"""

    def __init__(self, sub_buff_info: SubBuff):
        self.buff: float = float(sub_buff_info['buff'])
        self.name: str = sub_buff_info['name']

    def before_attack_act(self, user: BaseFightMember, target_member: BaseFightMember, msg_list: list[str]) -> None:
        user.increase.atk *= self.buff / 100
        msg = f"使用功法{self.name}, 攻击力提升{self.buff:.2f}%"
        msg_list.append(msg)
        del self


SUB_BUFF_ACHIEVE = {'1': AtkIncreaseBuff}
