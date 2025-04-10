from .fight_base import BaseSub, BaseSkill
from .skills_def.buff_def import get_base_buff, BUFF_ACHIEVE
from .skills_def.sec_buff import SEC_BUFF_ACHIEVE
from .skills_def.sub_buff import SUB_BUFF_ACHIEVE, SUITS_BUFF_ACHIEVE
from ...types.error import UndefinedError
from ...types.skills_info_type import SecBuff, SubBuff


def sub_buff_register(skill: SubBuff) -> BaseSub:
    sub_buff_type = skill['buff_type']
    if sub_buff_type not in SUB_BUFF_ACHIEVE:
        raise UndefinedError(f"未定义的辅修效果类型: {sub_buff_type}, 请在skills_def下完善定义")
    achieve = SUB_BUFF_ACHIEVE[sub_buff_type]
    return achieve(skill)


def sec_buff_register(skill: SecBuff):
    sec_buff_type = skill['skill_type']
    if sec_buff_type not in SEC_BUFF_ACHIEVE:
        raise UndefinedError(f"未定义的神通效果类型: {sec_buff_type}, 请在skills_def下完善定义")
    achieve = SEC_BUFF_ACHIEVE[sec_buff_type]
    return achieve(skill)


def get_suits_buff_sub_type(suits_name: str, suits_value):
    achieve = SUITS_BUFF_ACHIEVE[suits_name]
    return achieve(suits_name, suits_value)
    


REGISTER_TYPE_DEF = {
    "辅修功法": sub_buff_register,
    "神通": sec_buff_register}


def register_skills(skills: SecBuff | list[SecBuff]) -> list[BaseSkill]:
    """技能效果注册工具，统一初始化接口"""
    # 分流列表与单个对象
    registry = []
    if not skills:
        return registry
    if isinstance(skills, dict):
        registered_skill = REGISTER_TYPE_DEF[skills['item_type']](skills)
        registry.append(registered_skill)
        return registry
    for skill_per in skills:
        registered_skill = REGISTER_TYPE_DEF[skill_per['item_type']](skill_per)
        registry.append(registered_skill)
    return registry


def register_sub(skills: SubBuff | list[SubBuff]) -> dict[str, BaseSub]:
    """辅修效果注册工具，统一初始化接口"""
    # 分流列表与单个对象
    registry = {}
    if not skills:
        return registry
    if isinstance(skills, dict):
        registered_skill = REGISTER_TYPE_DEF[skills['item_type']](skills)
        registry[skills['name']] = registered_skill
        return registry
    for skill_per in skills:
        registered_skill = REGISTER_TYPE_DEF[skill_per['item_type']](skill_per)
        registry[skill_per['name']] = registered_skill
    return registry


def register_suits_buff(user_id, new_equipment_buff):
    buffs = {}
    for new_equipment_buff_type in new_equipment_buff:
        if new_equipment_buff_type in BUFF_ACHIEVE:
            buff = get_base_buff(new_equipment_buff_type, user_id)
            buff.effect_value = new_equipment_buff[new_equipment_buff_type]
            buffs[buff.name] = buff
    return buffs


def register_suits_sub(new_equipment_buff):
    suits_sub = {}
    for new_equipment_buff_type in new_equipment_buff:
        if new_equipment_buff_type in SUITS_BUFF_ACHIEVE:
            sub = get_suits_buff_sub_type(new_equipment_buff_type, new_equipment_buff[new_equipment_buff_type])
            suits_sub[new_equipment_buff_type] = sub
    return suits_sub
