from ..xiuxian_config import XiuConfig
from ..xiuxian_data.data.境界_data import level_data
from ..xiuxian_place import place
from ..xiuxian_utils.other_set import OtherSet
from ..xiuxian_utils.xiuxian2_handle import (
    sql_message, UserBuffDate,
    xiuxian_impart
)


async def exp_up_by_time(user_info, exp_time) -> tuple[str, int, dict]:
    """
    根据时间为用户增加修为
    :param user_info: 用户信息，推荐使用依赖注入获取
    :param exp_time: 修炼时间，分钟
    :return: 修为是否上限，增加修为量，恢复状态信息
    """

    user_id = user_info['user_id']
    level = user_info['level']
    use_exp = user_info['exp']
    # 获取下个境界需要的修为: 下境界需要修为 * 闭关上限
    max_exp = int(await OtherSet().set_closing_type(level)) * XiuConfig().closing_exp_upper_limit
    user_get_exp_max = max_exp - use_exp

    # 校验当当前修为超出上限的问题，不可为负数
    user_get_exp_max = max(user_get_exp_max, 0)

    root_rate = await sql_message.get_root_rate(user_info['root_type'])  # 灵根倍率
    realm_rate = level_data[level]["spend"]  # 境界倍率

    # 功法修炼加成
    user_buff_data = UserBuffDate(user_id)
    main_buff_data = await user_buff_data.get_user_main_buff_data()
    main_buff_rate_buff = main_buff_data['ratebuff'] if main_buff_data is not None else 0  # 功法修炼倍率
    main_buff_clo_exp = main_buff_data['clo_exp'] if main_buff_data is not None else 0  # 功法闭关经验

    # 位面灵气加成
    place_id = await place.get_now_place_id(user_id)
    world_id = place.get_world_id(place_id)
    world_buff = world_id * 0.6

    # 计算传承增益
    impart_data = await xiuxian_impart.get_user_info_with_id(user_id)
    impart_exp_up = impart_data['impart_exp_up'] if impart_data is not None else 0
    user_buff_data = await UserBuffDate(user_id).buff_info

    # 闭关获取的修为倍率
    exp = (int(
        XiuConfig().closing_exp
        * root_rate
        * realm_rate
        * (1 + main_buff_rate_buff)
        * (1 + main_buff_clo_exp)
        * (1 + impart_exp_up + user_buff_data['blessed_spot'])
        * (1 + world_buff))
           * exp_time)

    await sql_message.update_power2(user_id)  # 更新战力

    # 用户获取的修为是否到达上限
    if exp >= user_get_exp_max:
        exp = user_get_exp_max
        await sql_message.update_exp(user_id, user_get_exp_max)
        is_full = "本次修炼达到上限，"
    else:
        await sql_message.update_exp(user_id, exp)
        is_full = ''

    result_msg, result_hp_mp = await OtherSet().send_hp_mp(user_id, exp_time)
    await sql_message.update_user_attribute(user_id, result_hp_mp[0], result_hp_mp[1], int(result_hp_mp[2] / 10))
    return is_full, exp, result_msg


async def exp_up_by_time_no_buff(user_info, exp_time) -> tuple[str, int, dict]:
    """
    根据时间为用户增加修为
    :param user_info: 用户信息，推荐使用依赖注入获取
    :param exp_time: 修炼时间，分钟
    :return: 修为是否上限，增加修为量，恢复状态信息
    """

    user_id = user_info['user_id']
    level = user_info['level']
    use_exp = user_info['exp']
    # 获取下个境界需要的修为: 下境界需要修为 * 闭关上限
    max_exp = int(await OtherSet().set_closing_type(level)) * XiuConfig().closing_exp_upper_limit
    user_get_exp_max = max_exp - use_exp

    # 校验当当前修为超出上限的问题，不可为负数
    user_get_exp_max = max(user_get_exp_max, 0)

    root_rate = await sql_message.get_root_rate(user_info['root_type'])  # 灵根倍率
    realm_rate = level_data[level]["spend"]  # 境界倍率

    # 功法修炼加成
    user_buff_data = UserBuffDate(user_id)
    main_buff_data = await user_buff_data.get_user_main_buff_data()
    main_buff_rate_buff = main_buff_data['ratebuff'] if main_buff_data is not None else 0  # 功法修炼倍率

    # 位面灵气加成
    place_id = await place.get_now_place_id(user_id)
    world_id = place.get_world_id(place_id)
    world_buff = world_id * 0.6

    # 计算传承增益
    user_buff_data = await UserBuffDate(user_id).buff_info

    # 闭关获取的修为倍率
    exp = (int(
        XiuConfig().closing_exp
        * root_rate
        * realm_rate
        * (1 + main_buff_rate_buff)
        * (1 + user_buff_data['blessed_spot'])
        * (1 + world_buff))
           * exp_time * 6)

    await sql_message.update_power2(user_id)  # 更新战力

    # 用户获取的修为是否到达上限
    if exp >= user_get_exp_max:
        exp = user_get_exp_max
        await sql_message.update_exp(user_id, user_get_exp_max)
        is_full = "本次修炼达到上限，"
    else:
        await sql_message.update_exp(user_id, exp)
        is_full = ''

    result_msg, result_hp_mp = await OtherSet().send_hp_mp(user_id, exp_time)
    await sql_message.update_user_attribute(user_id, result_hp_mp[0], result_hp_mp[1], int(result_hp_mp[2] / 10))
    return is_full, exp, result_msg
