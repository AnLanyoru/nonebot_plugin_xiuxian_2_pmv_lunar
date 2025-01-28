import random

from .other_set import OtherSet
from .utils import number_to
from .xiuxian2_handle import sql_message, UserBuffDate, xiuxian_impart
from ..user_data_handle import UserBuffData, temp_buff_def
from ..xiuxian_config import convert_rank


class BossBuff:
    def __init__(self):
        self.boss_zs = 0
        self.boss_hx = 0
        self.boss_bs = 0
        self.boss_xx = 0
        self.boss_jg = 0
        self.boss_jh = 0
        self.boss_jb = 0
        self.boss_xl = 0


class UserRandomBuff:
    def __init__(self):
        self.random_break = 0
        self.random_xx = 0
        self.random_hx = 0
        self.random_def = 0


empty_boss_buff = BossBuff()
empty_ussr_random_buff = UserRandomBuff()


async def player_fight(player1: dict, player2: dict, type_in, bot_id):
    """
    回合制战斗
    type_in : 1-切磋，不消耗气血、真元
              2-战斗，消耗气血、真元
    数据示例：
    {"user_id": None,"道号": None, "气血": None, "攻击": None, "真元": None, '会心':None, 'exp':None}
    """
    user1_buff_date = UserBuffDate(player1['user_id'])  # 1号的buff信息

    user2_buff_date = UserBuffDate(player2['user_id'])  # 2号的buff信息

    player1_skil_open = False
    player2_skil_open = False

    if (user1_skill_date := await user1_buff_date.get_user_sec_buff_data()) is not None:
        player1_skil_open = True

    if (user2_skill_date := await user2_buff_date.get_user_sec_buff_data()) is not None:
        player2_skil_open = True

    player1_sub_open = False  # 辅修功法14
    player2_sub_open = False

    if (user1_sub_buff_date := await user1_buff_date.get_user_sub_buff_data()) is not None:
        player1_sub_open = True

    if (user2_sub_buff_date := await user2_buff_date.get_user_sub_buff_data()) is not None:
        player2_sub_open = True

    play_list = []
    suc = None
    is_sql = False
    if type_in == 2:
        is_sql = True
    user1_turn_skip = True
    user2_turn_skip = True

    player1_turn_cost = 0  # 先设定为初始值 0
    player2_turn_cost = 0
    player1_f_js = await get_user_def_buff(player1['user_id'])
    player2_f_js = await get_user_def_buff(player2['user_id'])
    player1_js = player1_f_js
    player2_js = player2_f_js
    user1_skill_sh = 0
    user2_skill_sh = 0
    user1_buff_turn = True
    user2_buff_turn = True

    user1_battle_buff_date = UserBattleBuffDate(player1['user_id'])  # 1号的战斗buff信息
    user2_battle_buff_date = UserBattleBuffDate(player2['user_id'])  # 2号的战斗buff信息

    for i in range(15):

        user1_battle_buff_date, user2_battle_buff_date, msg = start_sub_buff_handle(
            player1_sub_open, user1_sub_buff_date, user1_battle_buff_date,
            player2_sub_open, user2_sub_buff_date, user2_battle_buff_date)
        if msg:
            play_list.append(msg)  # 辅修功法14

        player2_health_temp = player2['气血']
        if player1_skil_open:  # 是否开启技能
            if user1_turn_skip:  # 无需跳过回合
                play_list.append(f"☆------{player1['道号']}的回合------☆")
                user1_hp_cost, user1_mp_cost, user1_skill_type, skill_rate = await get_skill_hp_mp_data(player1,
                                                                                                        user1_skill_date)
                if player1_turn_cost == 0:  # 没有持续性技能生效
                    player1_js = player1_f_js  # 没有持续性技能生效,减伤恢复
                    if is_enable_user_skill(player1, user1_hp_cost, user1_mp_cost, player1_turn_cost,
                                            skill_rate):  # 满足技能要求，#此处为技能的第一次释放
                        skill_msg, user1_skill_sh, player1_turn_cost = await get_skill_sh_data(player1,
                                                                                               user1_skill_date,
                                                                                               player2_js)
                        if user1_skill_type == 1:  # 直接伤害类技能
                            play_list.append(skill_msg)
                            player1 = calculate_skill_cost(player1, user1_hp_cost, user1_mp_cost)
                            player2['气血'] = player2['气血'] - int(user1_skill_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                            play_list.append(
                                f"{player2['道号']}剩余血量{number_to(player2['气血'])}")

                        elif user1_skill_type == 2:  # 持续性伤害技能
                            play_list.append(skill_msg)
                            player1 = calculate_skill_cost(player1, user1_hp_cost, user1_mp_cost)
                            player2['气血'] = player2['气血'] - int(
                                user1_skill_sh * (0.2 + player2_js))  # 玩家1的伤害 * 玩家2的减伤
                            play_list.append(
                                f"{player2['道号']}剩余血量{number_to(player2['气血'])}")

                        elif user1_skill_type == 3:  # buff类技能
                            user1_buff_type = user1_skill_date['bufftype']
                            if user1_buff_type == 1:  # 攻击类buff
                                is_crit, player1_sh = await get_turnatk(player1, user1_skill_sh,
                                                                        user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                                if is_crit:
                                    msg1 = "{}发起会心一击，造成了{}伤害"
                                else:
                                    msg1 = "{}发起攻击，造成了{}伤害"
                                player1 = calculate_skill_cost(player1, user1_hp_cost, user1_mp_cost)
                                play_list.append(skill_msg)
                                play_list.append(
                                    msg1.format(player1['道号'], number_to(player1_sh * player2_js)))
                                player2['气血'] = player2['气血'] - int(player1_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                                play_list.append(
                                    f"{player2['道号']}剩余血量{number_to(player2['气血'])}")

                            elif user1_buff_type == 2:  # 减伤类buff,需要在player2处判断
                                is_crit, player1_sh = await get_turnatk(player1, 0,
                                                                        user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                                if is_crit:
                                    msg1 = "{}发起会心一击，造成了{}伤害"
                                else:
                                    msg1 = "{}发起攻击，造成了{}伤害"

                                player1 = calculate_skill_cost(player1, user1_hp_cost, user1_mp_cost)
                                play_list.append(skill_msg)
                                play_list.append(
                                    msg1.format(player1['道号'], number_to(player1_sh * player2_js)))
                                player2['气血'] = player2['气血'] - int(player1_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                                play_list.append(f"{player2['道号']}剩余血量{number_to(player2['气血'])}")
                                player1_js = player1_f_js - user1_skill_sh if player1_f_js - user1_skill_sh > 0.1 else 0.1

                        elif user1_skill_type == 4:  # 封印类技能
                            play_list.append(skill_msg)
                            player1 = calculate_skill_cost(player1, user1_hp_cost, user1_mp_cost)

                            if user1_skill_sh:  # 命中
                                user2_turn_skip = False
                                user2_buff_turn = False

                    else:  # 没放技能，打一拳
                        is_crit, player1_sh = await get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if is_crit:
                            msg1 = "{}发起会心一击，造成了{}伤害"
                        else:
                            msg1 = "{}发起攻击，造成了{}伤害"
                        play_list.append(msg1.format(player1['道号'], number_to(player1_sh * player2_js)))
                        player2['气血'] = player2['气血'] - int(player1_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                        play_list.append(f"{player2['道号']}剩余血量{number_to(player2['气血'])}")

                else:  # 持续性技能判断,不是第一次
                    if user1_skill_type == 2:  # 持续性伤害技能
                        player1_turn_cost = player1_turn_cost - 1
                        skill_msg = get_persistent_skill_msg(player1['道号'], user1_skill_date['name'], user1_skill_sh,
                                                             player2_js, player1_turn_cost)
                        play_list.append(skill_msg)
                        is_crit, player1_sh = await get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if is_crit:
                            msg1 = "{}发起会心一击，造成了{}伤害"
                        else:
                            msg1 = "{}发起攻击，造成了{}伤害"
                        play_list.append(msg1.format(player1['道号'], number_to(player1_sh * player2_js)))
                        # 玩家1的伤害 * 玩家2的减伤,持续性伤害不影响普攻
                        player2['气血'] = player2['气血'] - int(
                            (user1_skill_sh * (0.2 + player2_js)) + (player1_sh * player2_js))
                        play_list.append(f"{player2['道号']}剩余血量{number_to(player2['气血'])}")

                    elif user1_skill_type == 3:  # buff类技能
                        user1_buff_type = user1_skill_date['bufftype']
                        if user1_buff_type == 1:  # 攻击类buff
                            is_crit, player1_sh = await get_turnatk(player1, user1_skill_sh,
                                                                    user1_battle_buff_date)  # 判定是否暴击 辅修功法14

                            if is_crit:
                                msg1 = "{}发起会心一击，造成了{}伤害"
                            else:
                                msg1 = "{}发起攻击，造成了{}伤害"

                            player1_turn_cost = player1_turn_cost - 1
                            play_list.append(f"{user1_skill_date['name']}增伤剩余:{player1_turn_cost}回合")
                            play_list.append(
                                msg1.format(player1['道号'], number_to(player1_sh * player2_js)))
                            player2['气血'] = player2['气血'] - int(player1_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                            play_list.append(f"{player2['道号']}剩余血量{number_to(player2['气血'])}")

                        elif user1_buff_type == 2:  # 减伤类buff,需要在player2处判断
                            is_crit, player1_sh = await get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                            if is_crit:
                                msg1 = "{}发起会心一击，造成了{}伤害"
                            else:
                                msg1 = "{}发起攻击，造成了{}伤害"

                            player1_turn_cost = player1_turn_cost - 1
                            play_list.append(f"{user1_skill_date['name']}减伤剩余{player1_turn_cost}回合")
                            play_list.append(msg1.format(player1['道号'], number_to(player1_sh * player2_js)))
                            player2['气血'] = player2['气血'] - int(player1_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                            play_list.append(
                                f"{player2['道号']}剩余血量{number_to(player2['气血'])}")
                            player1_js = player1_f_js - user1_skill_sh if player1_f_js - user1_skill_sh > 0.1 else 0.1

                    elif user1_skill_type == 4:  # 封印类技能
                        player1_turn_cost = player1_turn_cost - 1
                        skill_msg = get_persistent_skill_msg(player1['道号'], user1_skill_date['name'], user1_skill_sh,
                                                             player2_js, player1_turn_cost)
                        play_list.append(skill_msg)
                        is_crit, player1_sh = await get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if is_crit:
                            msg1 = "{}发起会心一击，造成了{}伤害"
                        else:
                            msg1 = "{}发起攻击，造成了{}伤害"
                        play_list.append(msg1.format(player1['道号'], number_to(player1_sh * player2_js)))

                        player2['气血'] = player2['气血'] - int(player1_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                        play_list.append(f"{player2['道号']}剩余血量{number_to(player2['气血'])}")
                        if player1_turn_cost == 0:  # 封印时间到
                            user2_turn_skip = True
                            user2_buff_turn = True

            else:  # 休息回合-1
                play_list.append(f"☆------{player1['道号']}动弹不得！------☆")
                if player1_turn_cost > 0:
                    player1_turn_cost -= 1
                if player1_turn_cost == 0 and user1_buff_turn:
                    user1_turn_skip = True

        else:  # 没有技能的derB
            if user1_turn_skip:
                play_list.append(f"☆------{player1['道号']}的回合------☆")
                is_crit, player1_sh = await get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                if is_crit:
                    msg1 = "{}发起会心一击，造成了{}伤害"
                else:
                    msg1 = "{}发起攻击，造成了{}伤害"
                play_list.append(msg1.format(player1['道号'], number_to(player1_sh * player2_js)))
                player2['气血'] = player2['气血'] - player1_sh * player2_js
                play_list.append(f"{player2['道号']}剩余血量{number_to(player2['气血'])}")

            else:
                play_list.append(f"☆------{player1['道号']}动弹不得！------☆")

        ## 自己回合结束 处理 辅修功法14
        player1, boss, msg = after_atk_sub_buff_handle(player1_sub_open, player1, user1_sub_buff_date,
                                                       player2_health_temp - player2['气血'],
                                                       player2)
        if msg:
            play_list.append(msg)

        if player2['气血'] <= 0:  # 玩家2气血小于0，结算
            play_list.append(f"{player1['道号']}胜利")
            suc = f"{player1['道号']}"
            break

        if player1_turn_cost < 0:  # 休息为负数，如果休息，则跳过回合，正常是0
            user1_turn_skip = False
            player1_turn_cost += 1

        player1_health_temp = player1['气血']  # 辅修功法14
        if player2_skil_open:  # 有技能
            if user2_turn_skip:  # 玩家2无需跳过回合
                play_list.append(f"☆------{player2['道号']}的回合------☆")
                user2_hp_cost, user2_mp_cost, user2_skill_type, skill_rate = await get_skill_hp_mp_data(player2,
                                                                                                        user2_skill_date)
                if player2_turn_cost == 0:  # 没有持续性技能生效
                    player2_js = player2_f_js
                    if is_enable_user_skill(player2, user2_hp_cost, user2_mp_cost, player2_turn_cost,
                                            skill_rate):  # 满足技能要求，#此处为技能的第一次释放
                        skill_msg, user2_skill_sh, player2_turn_cost = await get_skill_sh_data(player2,
                                                                                               user2_skill_date,
                                                                                               player1_js)
                        if user2_skill_type == 1:  # 直接伤害类技能
                            play_list.append(skill_msg)
                            player1['气血'] = player1['气血'] - int(user2_skill_sh * player1_js)  # 玩家2的伤害 * 玩家1的减伤
                            play_list.append(f"{player1['道号']}剩余血量{number_to(player1['气血'])}")
                            player2 = calculate_skill_cost(player2, user2_hp_cost, user2_mp_cost)

                        elif user2_skill_type == 2:  # 持续性伤害技能
                            play_list.append(skill_msg)
                            player1['气血'] = player1['气血'] - int(
                                user2_skill_sh * (0.2 + player1_js))  # 玩家2的伤害 * 玩家1的减伤-持续伤害破甲
                            play_list.append(f"{player1['道号']}剩余血量{number_to(player1['气血'])}")
                            player2 = calculate_skill_cost(player2, user2_hp_cost, user2_mp_cost)

                        elif user2_skill_type == 3:  # buff类技能
                            user2_buff_type = user2_skill_date['bufftype']
                            if user2_buff_type == 1:  # 攻击类buff
                                is_crit, player2_sh = await get_turnatk(player2, user2_skill_sh,
                                                                        user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                                if is_crit:
                                    msg2 = "{}发起会心一击，造成了{}伤害"
                                else:
                                    msg2 = "{}发起攻击，造成了{}伤害"

                                play_list.append(skill_msg)
                                play_list.append(msg2.format(player2['道号'], number_to(player2_sh * player1_js)))
                                player1['气血'] = player1['气血'] - int(player2_sh * player1_js)
                                play_list.append(f"{player1['道号']}剩余血量{number_to(player1['气血'])}")
                                player2 = calculate_skill_cost(player2, user2_hp_cost, user2_mp_cost)

                            elif user2_buff_type == 2:  # 减伤类buff,需要在player2处判断
                                is_crit, player2_sh = await get_turnatk(player2, 0,
                                                                        user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                                if is_crit:
                                    msg2 = "{}发起会心一击，造成了{}伤害"
                                else:
                                    msg2 = "{}发起攻击，造成了{}伤害"
                                play_list.append(skill_msg)
                                play_list.append(msg2.format(player2['道号'], number_to(player2_sh * player1_js)))
                                player1['气血'] = player1['气血'] - int(player2_sh * player1_js)
                                play_list.append(f"{player1['道号']}剩余血量{number_to(player1['气血'])}")
                                player2_js = player2_f_js - user2_skill_sh if player2_f_js - user2_skill_sh > 0.1 else 0.1
                                player2 = calculate_skill_cost(player2, user2_hp_cost, user2_mp_cost)

                        elif user2_skill_type == 4:  # 封印类技能
                            play_list.append(skill_msg)
                            player2 = calculate_skill_cost(player2, user2_hp_cost, user2_mp_cost)

                            if user2_skill_sh:  # 命中
                                user1_turn_skip = False
                                user1_buff_turn = False

                    else:  # 没放技能
                        is_crit, player2_sh = await get_turnatk(player2, 0, user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if is_crit:
                            msg2 = "{}发起会心一击，造成了{}伤害"
                        else:
                            msg2 = "{}发起攻击，造成了{}伤害"
                        play_list.append(msg2.format(player2['道号'], number_to(player2_sh * player1_js)))
                        player1['气血'] = player1['气血'] - int(player2_sh * player1_js)  # 玩家2的伤害 * 玩家1的减伤
                        play_list.append(f"{player1['道号']}剩余血量{number_to(player1['气血'])}")

                else:  # 持续性技能判断,不是第一次
                    if user2_skill_type == 2:  # 持续性伤害技能
                        player2_turn_cost = player2_turn_cost - 1
                        skill_msg = get_persistent_skill_msg(player2['道号'], user2_skill_date['name'], user2_skill_sh,
                                                             player1_js, player2_turn_cost)
                        play_list.append(skill_msg)

                        is_crit, player2_sh = await get_turnatk(player2, 0, user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if is_crit:
                            msg2 = "{}发起会心一击，造成了{}伤害"
                        else:
                            msg2 = "{}发起攻击，造成了{}伤害"

                        play_list.append(msg2.format(player2['道号'], number_to(player2_sh * player1_js)))
                        player1['气血'] = player1['气血'] - int(
                            (user2_skill_sh * (0.2 + player1_js)) + (player2_sh * player1_js))
                        play_list.append(f"{player1['道号']}剩余血量{number_to(player1['气血'])}")

                    elif user2_skill_type == 3:  # buff类技能
                        user2_buff_type = user2_skill_date['bufftype']
                        if user2_buff_type == 1:  # 攻击类buff
                            is_crit, player2_sh = await get_turnatk(player2, user2_skill_sh,
                                                                    user2_battle_buff_date)  # 判定是否暴击 辅修功法14

                            if is_crit:
                                msg2 = "{}发起会心一击，造成了{}伤害"
                            else:
                                msg2 = "{}发起攻击，造成了{}伤害"
                            player2_turn_cost = player2_turn_cost - 1
                            play_list.append(f"{user2_skill_date['name']}增伤剩余{player2_turn_cost}回合")
                            play_list.append(msg2.format(player2['道号'], number_to(player2_sh * player1_js)))
                            player1['气血'] = player1['气血'] - int(player2_sh * player1_js)  # 玩家2的伤害 * 玩家1的减伤
                            play_list.append(f"{player1['道号']}剩余血量{number_to(player1['气血'])}")

                        elif user2_buff_type == 2:  # 减伤类buff,需要在player2处判断
                            is_crit, player2_sh = await get_turnatk(player2, 0, user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                            if is_crit:
                                msg2 = "{}发起会心一击，造成了{}伤害"
                            else:
                                msg2 = "{}发起攻击，造成了{}伤害"

                            player2_turn_cost = player2_turn_cost - 1
                            play_list.append(f"{user2_skill_date['name']}减伤剩余{player2_turn_cost}回合！")
                            play_list.append(
                                msg2.format(player2['道号'], number_to(player2_sh * player1_js)))
                            player1['气血'] = player1['气血'] - int(player2_sh * player1_js)  # 玩家1的伤害 * 玩家2的减伤
                            play_list.append(f"{player1['道号']}剩余血量{number_to(player1['气血'])}")

                            player2_js = player2_f_js - user2_skill_sh if player2_f_js - user2_skill_sh > 0.1 else 0.1

                    elif user2_skill_type == 4:  # 封印类技能
                        player2_turn_cost = player2_turn_cost - 1
                        skill_msg = get_persistent_skill_msg(player2['道号'], user2_skill_date['name'], user2_skill_sh,
                                                             player1_js, player2_turn_cost)
                        play_list.append(skill_msg)

                        is_crit, player2_sh = await get_turnatk(player2, 0, user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if is_crit:
                            msg2 = "{}发起会心一击，造成了{}伤害"
                        else:
                            msg2 = "{}发起攻击，造成了{}伤害"
                        play_list.append(msg2.format(player2['道号'], number_to(player2_sh * player1_js)))
                        player1['气血'] = player1['气血'] - int(player2_sh * player1_js)  # 玩家1的伤害 * 玩家2的减伤
                        play_list.append(f"{player1['道号']}剩余血量{number_to(player1['气血'])}")

                        if player2_turn_cost == 0:  # 封印时间到
                            user1_turn_skip = True
                            user1_buff_turn = True

            else:  # 休息回合-1
                play_list.append(f"☆------{player2['道号']}动弹不得！------☆")
                if player2_turn_cost > 0:
                    player2_turn_cost -= 1
                if player2_turn_cost == 0 and user2_buff_turn:
                    user2_turn_skip = True
        else:  # 没有技能的derB
            if user2_turn_skip:
                play_list.append(f"☆------{player2['道号']}的回合------☆")
                is_crit, player2_sh = await get_turnatk(player2, 0, user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                if is_crit:
                    msg2 = "{}发起会心一击，造成了{}伤害"
                else:
                    msg2 = "{}发起攻击，造成了{}伤害"
                play_list.append(msg2.format(player2['道号'], number_to(player2_sh * player1_js)))
                player1['气血'] = player1['气血'] - player2_sh * player1_js
                play_list.append(f"{player1['道号']}剩余血量{number_to(player1['气血'])}")

            else:
                play_list.append(f"☆------{player2['道号']}动弹不得！------☆")

        if player1['气血'] <= 0:  # 玩家1气血小于0，结算
            play_list.append(f"{player2['道号']}胜利")
            suc = f"{player2['道号']}"
            break

        # 对方回合结束 处理 辅修功法14
        player2, player1, msg = after_atk_sub_buff_handle(player2_sub_open, player2,
                                                          user2_sub_buff_date,
                                                          player1_health_temp - player1['气血'], player1)
        if msg:
            play_list.append(msg)

        if player1['气血'] <= 0:  # 玩家2气血小于0，结算
            play_list.append(f"{player2['道号']}胜利")
            suc = f"{player2['道号']}"
            break

        if player2_turn_cost < 0:  # 休息为负数，如果休息，则跳过回合，正常是0
            user2_turn_skip = False
            player2_turn_cost += 1

        if user1_turn_skip is False and user2_turn_skip is False:
            play_list.append("双方都动弹不得！")
            user1_turn_skip = True
            user2_turn_skip = True

        if player1['气血'] <= 0 or player2['气血'] <= 0:
            play_list.append("逻辑错误！")
            break
    if not suc:
        play_list.append("你们打到天昏地暗被大能制止！！！！")
        suc = None

    if is_sql:
        await sql_message.update_user_hp_mp(player1['user_id'],
                                            max(1, int(player1['气血'] / player1['hp_buff'])),
                                            int(player1['真元'] / player1['mp_buff']))
        await sql_message.update_user_hp_mp(player2['user_id'],
                                            max(1, int(player2['气血'] / player2['hp_buff'])),
                                            int(player2['真元'] / player2['mp_buff']))
    return play_list, suc


def get_st2_type():
    data_dict = ST2
    return get_dict_type_rate(data_dict)


def get_st1_type():
    """根据概率返回事件类型"""
    data_dict = ST1
    return get_dict_type_rate(data_dict)


def get_dict_type_rate(data_dict):
    """根据字典内概率,返回字典key"""
    temp_dict = {}
    for i, v in data_dict.items():
        try:
            temp_dict[i] = v["type_rate"]
        except:
            continue
    key = OtherSet().calculated(temp_dict)
    return key


ST1 = {
    "攻击": {
        "type_rate": 50,
    },
    "会心": {
        "type_rate": 50,
    },
    "暴伤": {
        "type_rate": 50,
    },
    "禁血": {
        "type_rate": 50,
    }
}

ST2 = {
    "降攻": {
        "type_rate": 50,
    },
    "降会": {
        "type_rate": 50,
    },
    "降暴": {
        "type_rate": 50,
    },
    "禁蓝": {
        "type_rate": 50,
    }
}


async def boss_fight(player1: dict, boss: dict, type_in=2):
    """
    回合制战斗
    战斗，消耗气血、真元
    数据示例：
    {"user_id": None,"道号": None, "气血": None, "攻击": None, "真元": None, '会心':None, 'exp':None}
    """
    user1_buff_date = UserBuffDate(player1['user_id'])  # 1号的buff信息
    user1_buff_data = UserBuffData(player1['user_id'])

    play_list = []
    user1_buff_date_temp = await user1_buff_data.get_fight_temp_buff()
    if user1_buff_date_temp:
        for buff_type, buff_value in user1_buff_date_temp.items():
            buff_act_type = temp_buff_def[buff_type]
            player1[buff_act_type] *= 1 + buff_value
            play_list.append(f"{player1['道号']}的{buff_act_type}丹药力生效，{buff_act_type}提升{buff_value * 100}%")
    await user1_buff_data.update_fight_temp_buff({})
    if user1_buff_date is None:  # 处理为空的情况
        user1_main_buff_data = None
        user1_sub_buff_data = None  # 获取玩家1的辅修功法
    else:
        user1_main_buff_data = await user1_buff_date.get_user_main_buff_data()
        user1_sub_buff_data = await user1_buff_date.get_user_sub_buff_data()  # 获取玩家1的辅修功法
    user1_random_buff = user1_main_buff_data['random_buff'] if user1_main_buff_data is not None else 0
    fan_buff = user1_sub_buff_data['fan'] if user1_sub_buff_data is not None else 0
    stone_buff = user1_sub_buff_data['stone'] if user1_sub_buff_data is not None else 0
    sub_break = user1_sub_buff_data['break'] if user1_sub_buff_data is not None else 0

    random_buff = UserRandomBuff()
    if user1_random_buff == 1:
        user1_main_buff = random.randint(0, 100)
        if 0 <= user1_main_buff <= 25:
            random_buff.random_break = random.randint(15, 40) / 100
        elif 26 <= user1_main_buff <= 50:
            random_buff.random_xx = random.randint(2, 10) / 100
        elif 51 <= user1_main_buff <= 75:
            random_buff.random_hx = random.randint(5, 40) / 100
        elif 76 <= user1_main_buff <= 100:
            random_buff.random_def = random.randint(5, 15) / 100

    user1_break = random_buff.random_break + sub_break

    BOSSDEF = {
        "衣以候": "衣以侯布下了禁制镜花水月，",
        "金凰儿": "金凰儿使用了神通：金凰天火罩！",
        "九寒": "九寒使用了神通：寒冰八脉！",
        "莫女": "莫女使用了神通：圣灯启语诀！",
        "术方": "术方使用了神通：天罡咒！",
        "卫起": "卫起使用了神通：雷公铸骨！",
        "血枫": "血枫使用了神通：混世魔身！",
        "以向": "以向使用了神通：云床九练！",
        "砂鲛": "不说了！开鳖！",
        "神风王": "不说了！开鳖！",
        "鲲鹏": "鲲鹏使用了神通：逍遥游！",
        "天龙": "天龙使用了神通：真龙九变！",
        "历飞雨": "厉飞雨使用了神通：天煞震狱功！",
        "外道贩卖鬼": "不说了！开鳖！",
        "元磁道人": "元磁道人使用了法宝：元磁神山！",
        "散发着威压的尸体": "尸体周围爆发了出强烈的罡气！"
    }

    # 有技能，则开启技能模式

    player1_skil_open = False
    if (user1_skill_date := await user1_buff_date.get_user_sec_buff_data()) is not None:
        player1_skil_open = True

    player1_sub_open = False  # 辅修功法14
    if (user1_sub_buff_date := await user1_buff_date.get_user_sub_buff_data()) is not None:
        player1_sub_open = True
    suc = None
    is_sql = False
    if type_in == 2:
        is_sql = True
    user1_turn_skip = True
    boss_turn_skip = True
    player1_turn_cost = 0  # 先设定为初始值 0
    player1_f_js = await get_user_def_buff(player1['user_id'])
    player1_js = player1_f_js  # 减伤率

    # 回旋镖

    boss_buff = BossBuff()

    try:
        boss_rank = convert_rank((boss["jj"] + '中期'))[0]
    except:
        boss_rank = convert_rank((boss["jj"] + '四重'))[0]

    if convert_rank('合道境初期')[0] > boss_rank > convert_rank('求道者')[0]:  # 合道以下
        boss["减伤"] = 1  # boss减伤率
    if convert_rank('虚劫境初期')[0] > boss_rank > convert_rank('逆虚境后期')[0]:  # 合道境
        boss["减伤"] = random.randint(50, 55) / 100  # boss减伤率
        boss_st1 = random.randint(0, 100)  # boss神通1
        if 0 <= boss_st1 <= 25:
            boss_buff.boss_zs = 0.3  # boss攻击
        elif 26 <= boss_st1 <= 50:
            boss_buff.boss_hx = 0.1  # boss会心
        elif 51 <= boss_st1 <= 75:
            boss_buff.boss_bs = 0.5  # boss暴伤
        elif 75 <= boss_st1 <= 100:
            boss_buff.boss_xx = random.randint(5, 50) / 100  # boss禁血

        boss_st2 = random.randint(0, 100)  # boss神通2
        if 0 <= boss_st2 <= 25:
            boss_buff.boss_jg = 0.3  # boss降攻
        elif 26 <= boss_st2 <= 50:
            boss_buff.boss_jh = 0.3  # boss降会
        elif 51 <= boss_st2 <= 75:
            boss_buff.boss_jb = 0.5  # boss降暴
        elif 76 <= boss_st2 <= 100:
            boss_buff.boss_xl = random.randint(5, 50) / 100  # boss禁血

    if convert_rank('羽化境初期')[0] > boss_rank > convert_rank('合道境后期')[0]:  # 虚劫境
        boss["减伤"] = random.randint(40, 45) / 100  # boss减伤率
        boss_st1 = random.randint(0, 100)  # boss神通1
        if 0 <= boss_st1 <= 25:
            boss_buff.boss_zs = 0.4  # boss攻击
        elif 26 <= boss_st1 <= 50:
            boss_buff.boss_hx = 0.2  # boss会心
        elif 51 <= boss_st1 <= 75:
            boss_buff.boss_bs = 0.7  # boss暴伤
        elif 75 <= boss_st1 <= 100:
            boss_buff.boss_xx = random.randint(10, 50) / 100  # boss禁血

        boss_st2 = random.randint(0, 100)  # boss神通2
        if 0 <= boss_st2 <= 25:
            boss_buff.boss_jg = 0.4  # boss降攻
        elif 26 <= boss_st2 <= 50:
            boss_buff.boss_jh = 0.2  # boss降会
        elif 51 <= boss_st2 <= 75:
            boss_buff.boss_jb = 0.7  # boss降暴
        elif 76 <= boss_st2 <= 100:
            boss_buff.boss_xl = random.randint(10, 50) / 100  # boss禁血

    if convert_rank('登仙境初期')[0] > boss_rank > convert_rank('虚劫境后期')[0]:  # 羽化境
        boss["减伤"] = random.randint(30, 35) / 100  # boss减伤率
        boss_st1 = random.randint(0, 100)  # boss神通1
        if 0 <= boss_st1 <= 25:
            boss_buff.boss_zs = 0.6  # boss攻击
        elif 26 <= boss_st1 <= 50:
            boss_buff.boss_hx = 0.35  # boss会心
        elif 51 <= boss_st1 <= 75:
            boss_buff.boss_bs = 1.1  # boss暴伤
        elif 75 <= boss_st1 <= 100:
            boss_buff.boss_xx = random.randint(30, 100) / 100  # boss禁血

        boss_st2 = random.randint(0, 100)  # boss神通2
        if 0 <= boss_st2 <= 25:
            boss_buff.boss_jg = 0.5  # boss降攻
        elif 26 <= boss_st2 <= 50:
            boss_buff.boss_jh = 0.5  # boss降会
        elif 51 <= boss_st2 <= 75:
            boss_buff.boss_jb = 0.9  # boss降暴
        elif 76 <= boss_st2 <= 100:
            boss_buff.boss_xl = random.randint(30, 100) / 100  # boss禁血

    if convert_rank('凡仙境初期')[0] > boss_rank > convert_rank('羽化境后期')[0]:  # 登仙境
        boss["减伤"] = random.randint(20, 25) / 100  # boss减伤率
        boss_st1 = random.randint(0, 100)  # boss神通1
        if 0 <= boss_st1 <= 25:
            boss_buff.boss_zs = 0.7  # boss攻击
        elif 26 <= boss_st1 <= 50:
            boss_buff.boss_hx = 0.45  # boss会心
        elif 51 <= boss_st1 <= 75:
            boss_buff.boss_bs = 1.3  # boss暴伤
        elif 75 <= boss_st1 <= 100:
            boss_buff.boss_xx = random.randint(40, 100) / 100  # boss禁血

        boss_st2 = random.randint(0, 100)  # boss神通2
        if 0 <= boss_st2 <= 25:
            boss_buff.boss_jg = 0.55  # boss降攻
        elif 26 <= boss_st2 <= 50:
            boss_buff.boss_jh = 0.6  # boss降会
        elif 51 <= boss_st2 <= 75:
            boss_buff.boss_jb = 0.95  # boss降暴
        elif 76 <= boss_st2 <= 100:
            boss_buff.boss_xl = random.randint(40, 100) / 100  # boss禁血

    if convert_rank('地仙境初期')[0] > boss_rank > convert_rank('登仙境后期')[0]:  # 凡仙境
        boss["减伤"] = random.randint(10, 15) / 100  # boss减伤率
        boss_st1 = random.randint(0, 100)  # boss神通1
        if 0 <= boss_st1 <= 25:
            boss_buff.boss_zs = 0.85  # boss攻击
        elif 26 <= boss_st1 <= 50:
            boss_buff.boss_hx = 0.5  # boss会心
        elif 51 <= boss_st1 <= 75:
            boss_buff.boss_bs = 1.5  # boss暴伤
        elif 75 <= boss_st1 <= 100:
            boss_buff.boss_xx = random.randint(50, 100) / 100  # boss禁血

        boss_st2 = random.randint(0, 100)  # boss神通2
        if 0 <= boss_st2 <= 25:
            boss_buff.boss_jg = 0.6  # boss降攻
        elif 26 <= boss_st2 <= 50:
            boss_buff.boss_jh = 0.65  # boss降会
        elif 51 <= boss_st2 <= 75:
            boss_buff.boss_jb = 0.97  # boss降暴
        elif 76 <= boss_st2 <= 100:
            boss_buff.boss_xl = random.randint(50, 100) / 100  # boss禁血

    if convert_rank('玄仙境初期')[0] > boss_rank > convert_rank('凡仙境后期')[0]:  # 地仙境
        boss["减伤"] = 0.1  # boss减伤率
        boss_st1 = random.randint(0, 100)  # boss神通1
        if 0 <= boss_st1 <= 25:
            boss_buff.boss_zs = 0.9  # boss攻击
        elif 26 <= boss_st1 <= 50:
            boss_buff.boss_hx = 0.6  # boss会心
        elif 51 <= boss_st1 <= 75:
            boss_buff.boss_bs = 1.7  # boss暴伤
        elif 75 <= boss_st1 <= 100:
            boss_buff.boss_xx = random.randint(60, 100) / 100  # boss禁血

        boss_st2 = random.randint(0, 100)  # boss神通2
        if 0 <= boss_st2 <= 25:
            boss_buff.boss_jg = 0.62  # boss降攻
        elif 26 <= boss_st2 <= 50:
            boss_buff.boss_jh = 0.67  # boss降会
        elif 51 <= boss_st2 <= 75:
            boss_buff.boss_jb = 0.98  # boss降暴
        elif 76 <= boss_st2 <= 100:
            boss_buff.boss_xl = random.randint(60, 100) / 100  # boss禁血
        # 金仙境boss设置
    if convert_rank('金仙境初期')[0] > boss_rank > convert_rank('地仙境后期')[0]:  # 玄仙境
        boss["减伤"] = 0.05  # boss减伤率
        boss_st1 = random.randint(0, 100)  # boss神通1
        if 0 <= boss_st1 <= 25:
            boss_buff.boss_zs = 1  # boss攻击
        elif 26 <= boss_st1 <= 50:
            boss_buff.boss_hx = 0.7  # boss会心
        elif 51 <= boss_st1 <= 75:
            boss_buff.boss_bs = 2  # boss暴伤
        elif 75 <= boss_st1 <= 100:
            boss_buff.boss_xx = random.randint(80, 99) / 100  # boss禁血

        boss_st2 = random.randint(0, 100)  # boss神通2
        if 0 <= boss_st2 <= 25:
            boss_buff.boss_jg = 0.7  # boss降攻
        elif 26 <= boss_st2 <= 50:
            boss_buff.boss_jh = 0.7  # boss降会
        elif 51 <= boss_st2 <= 75:
            boss_buff.boss_jb = 0.99  # boss降暴
        elif 76 <= boss_st2 <= 100:
            boss_buff.boss_xl = random.randint(80, 99) / 100  # boss禁血
    if convert_rank('圣王境初期')[0] >= boss_rank > convert_rank('玄仙境后期')[0]:  # 金仙境 无上位境界，用0代替
        boss["减伤"] = 0.03  # boss减伤率
        boss_st1 = random.randint(0, 100)  # boss神通1
        if 0 <= boss_st1 <= 25:
            boss_buff.boss_zs = 1.1  # boss攻击
        elif 26 <= boss_st1 <= 50:
            boss_buff.boss_hx = 0.8  # boss会心
        elif 51 <= boss_st1 <= 75:
            boss_buff.boss_bs = 2.4  # boss暴伤
        elif 75 <= boss_st1 <= 100:
            boss_buff.boss_xx = random.randint(90, 99) / 100  # boss禁血

        boss_st2 = random.randint(0, 100)  # boss神通2
        if 0 <= boss_st2 <= 25:
            boss_buff.boss_jg = 0.73  # boss降攻
        elif 26 <= boss_st2 <= 50:
            boss_buff.boss_jh = 0.80  # boss降会
        elif 51 <= boss_st2 <= 75:
            boss_buff.boss_jb = 0.999  # boss降暴
        elif 76 <= boss_st2 <= 100:
            boss_buff.boss_xl = random.randint(90, 99) / 100  # boss禁血

    if fan_buff == 1:
        fan_data = True
    else:
        fan_data = False

    user1_skill_sh = 0

    get_stone = 0
    sh = 0
    qx = boss['气血']
    boss_now_stone = boss['stone']
    boss_js = boss['减伤']
    if 'defence' in boss:
        boss_js = boss['defence']

    if boss['name'] in BOSSDEF:
        effect_name = BOSSDEF[boss['name']]
        boss_js_data = f"{effect_name},获得了{int((1 - boss_js) * 100)}%减伤!"
    else:
        boss_js_data = f"{boss['name']}展开了护体罡气,获得了{int((1 - boss_js) * 100)}%减伤!"

    play_list.append(boss_js_data)

    if boss_buff.boss_zs > 0:
        boss_zs_data = f"{boss['name']}使用了真龙九变,提升了{int(boss_buff.boss_zs * 100)}%攻击力!"

        play_list.append(boss_zs_data)

    if boss_buff.boss_hx > 0:
        boss_hx_data = f"{boss['name']}使用了无瑕七绝剑,提升了{int(boss_buff.boss_hx * 100)}%会心率!"

        play_list.append(boss_hx_data)

    if boss_buff.boss_bs > 0:
        boss_bs_data = f"{boss['name']}使用了太乙剑诀,提升了{int(boss_buff.boss_bs * 100)}%会心伤害!"

        play_list.append(boss_bs_data)

    if boss_buff.boss_xx > 0:
        boss_xx_data = f"{boss['name']}使用了七煞灭魂聚血杀阵,降低了{player1['道号']}{int(boss_buff.boss_xx * 100)}%气血吸取!"

        play_list.append(boss_xx_data)

    if boss_buff.boss_jg > 0:
        boss_jg_data = f"{boss['name']}使用了子午安息香,降低了{player1['道号']}{int(boss_buff.boss_jg * 100)}%伤害!"

        play_list.append(boss_jg_data)

    if boss_buff.boss_jh > 0:
        boss_jh_data = f"{boss['name']}使用了玄冥剑气,降低了{player1['道号']}{int(boss_buff.boss_jh * 100)}%会心率!"

        play_list.append(boss_jh_data)

    if boss_buff.boss_jb > 0:
        boss_jb_data = f"{boss['name']}使用了大德琉璃金刚身,降低了{player1['道号']}{int(boss_buff.boss_jb * 100)}%会心伤害!"

        play_list.append(boss_jb_data)

    if boss_buff.boss_xl > 0:
        boss_xl_data = f"{boss['name']}使用了千煌锁灵阵,降低了{player1['道号']}{int(boss_buff.boss_xl * 100)}%真元吸取!"

        play_list.append(boss_xl_data)

    if random_buff.random_break > 0:
        random_break_rate = f"{player1['道号']}发动了八九玄功,获得了{int(random_buff.random_break * 100)}%穿甲！"
        play_list.append(random_break_rate)

    if random_buff.random_xx > 0:
        random_xx_data = f"{player1['道号']}发动了八九玄功,提升了{int(random_buff.random_xx * 100)}%!吸血效果！"
        play_list.append(random_xx_data)

    if random_buff.random_hx > 0:
        random_hx_data = f"{player1['道号']}发动了八九玄功,提升了{int(random_buff.random_hx * 100)}%!会心！"
        play_list.append(random_hx_data)

    if random_buff.random_def > 0:
        random_def_data = f"{player1['道号']}发动了八九玄功,获得了{int(random_buff.random_def * 100)}%!减伤！"
        play_list.append(random_def_data)

    boss['会心'] = 30

    if fan_data is True:
        fan_data = f"{player1['道号']}发动了辅修功法反咒禁制，无效化了减益！"
        play_list.append(fan_data)

    user1_battle_buff_date = UserBattleBuffDate(player1['user_id'])  # 1号的战斗buff信息 辅修功法14

    for i in range(20):

        user1_battle_buff_date, user2_battle_buff_date, msg = start_sub_buff_handle(player1_sub_open,
                                                                                    user1_sub_buff_date,
                                                                                    user1_battle_buff_date,
                                                                                    False,
                                                                                    {},
                                                                                    {})
        if msg:
            play_list.append(msg)  # 辅修功法14

        player2_health_temp = boss['气血']
        if player1_skil_open:  # 是否开启技能
            if user1_turn_skip:  # 无需跳过回合
                turn_start_msg = f"☆------{player1['道号']}的回合------☆"
                play_list.append(turn_start_msg)
                user1hpconst, user1mpcost, user1skill_type, skillrate = await get_skill_hp_mp_data(player1,
                                                                                                   user1_skill_date)
                if player1_turn_cost == 0:  # 没有持续性技能生效
                    player1_js = player1_f_js  # 没有持续性技能生效,减伤恢复
                    if is_enable_user_skill(player1, user1hpconst, user1mpcost, player1_turn_cost,
                                            skillrate):  # 满足技能要求，#此处为技能的第一次释放
                        skillmsg, user1_skill_sh, player1_turn_cost = await get_skill_sh_data(player1, user1_skill_date,
                                                                                              boss_js)
                        if user1skill_type == 1:  # 直接伤害类技能
                            play_list.append(skillmsg)
                            player1 = calculate_skill_cost(player1, user1hpconst, user1mpcost)
                            boss['气血'] = boss['气血'] - int(
                                user1_skill_sh * (boss_js + user1_break))  # 玩家1的伤害 * boss的减伤
                            boss_hp_msg = f"{boss['name']}剩余血量{number_to(boss['气血'])}"
                            play_list.append(boss_hp_msg)
                            sh += int(user1_skill_sh * (boss_js + user1_break))
                        elif user1skill_type == 2:  # 持续性伤害技能
                            play_list.append(skillmsg)
                            player1 = calculate_skill_cost(player1, user1hpconst, user1mpcost)
                            boss['气血'] = boss['气血'] - int(
                                user1_skill_sh * (0.2 + boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                            boss_hp_msg = f"{boss['name']}剩余血量{number_to(boss['气血'])}"
                            play_list.append(boss_hp_msg)
                            sh += int(user1_skill_sh * (0.2 + boss_js + user1_break))

                        elif user1skill_type == 3:  # buff类技能
                            user1buff_type = user1_skill_date['bufftype']
                            if user1buff_type == 1:  # 攻击类buff
                                is_crit, player1_sh = await get_turnatk(player1, 0, user1_battle_buff_date, boss_buff,
                                                                        random_buff)  # 判定是否暴击 辅修功法14
                                if is_crit:
                                    msg1 = "{}发起会心一击，造成了{}伤害"
                                else:
                                    msg1 = "{}发起攻击，造成了{}伤害"
                                player1 = calculate_skill_cost(player1, user1hpconst, user1mpcost)
                                play_list.append(skillmsg)
                                player1_atk_msg = msg1.format(player1['道号'],
                                                              number_to(int(player1_sh * (boss_js + user1_break))))
                                play_list.append(player1_atk_msg)
                                boss['气血'] = boss['气血'] - int(
                                    player1_sh * (boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                                boss_hp_msg = f"{boss['name']}剩余血量{number_to(boss['气血'])}"
                                play_list.append(boss_hp_msg)
                                sh += int(player1_sh * (boss_js + user1_break))

                            elif user1buff_type == 2:  # 减伤类buff,需要在player2处判断
                                is_crit, player1_sh = await get_turnatk(player1, 0, user1_battle_buff_date, boss_buff,
                                                                        random_buff)  # 判定是否暴击 辅修功法14
                                if is_crit:
                                    msg1 = "{}发起会心一击，造成了{}伤害"
                                else:
                                    msg1 = "{}发起攻击，造成了{}伤害"

                                player1 = calculate_skill_cost(player1, user1hpconst, user1mpcost)
                                play_list.append(skillmsg)
                                player1_atk_msg = msg1.format(player1['道号'],
                                                              number_to(player1_sh * (boss_js + user1_break)))
                                play_list.append(player1_atk_msg)
                                boss['气血'] = boss['气血'] - int(
                                    player1_sh * (boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                                boss_hp_msg = f"{boss['name']}剩余血量{number_to(boss['气血'])}"
                                play_list.append(boss_hp_msg)
                                player1_js = player1_f_js - user1_skill_sh
                                sh += player1_sh * (boss_js + user1_break)

                        elif user1skill_type == 4:  # 封印类技能
                            play_list.append(skillmsg)
                            player1 = calculate_skill_cost(player1, user1hpconst, user1mpcost)

                            if user1_skill_sh:  # 命中
                                boss_turn_skip = False

                    else:  # 没放技能，打一拳
                        is_crit, player1_sh = await get_turnatk(player1, 0, user1_battle_buff_date, boss_buff,
                                                                random_buff)  # 判定是否暴击 辅修功法14
                        if is_crit:
                            msg1 = "{}发起会心一击，造成了{}伤害"
                        else:
                            msg1 = "{}发起攻击，造成了{}伤害"
                        player1_atk_msg = msg1.format(player1['道号'],
                                                      number_to(int(player1_sh * (boss_js + user1_break))))
                        play_list.append(player1_atk_msg)
                        boss['气血'] = boss['气血'] - int(player1_sh * (boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                        boss_hp_msg = f"{boss['name']}剩余血量{number_to(boss['气血'])}"
                        play_list.append(boss_hp_msg)
                        sh += int(player1_sh * (boss_js + user1_break))

                else:  # 持续性技能判断,不是第一次
                    if user1skill_type == 2:  # 持续性伤害技能
                        player1_turn_cost = player1_turn_cost - 1
                        skillmsg = get_persistent_skill_msg(player1['道号'], user1_skill_date['name'], user1_skill_sh,
                                                            boss_js, player1_turn_cost)
                        play_list.append(skillmsg)
                        is_crit, player1_sh = await get_turnatk(player1, 0, user1_battle_buff_date, boss_buff,
                                                                random_buff)  # 判定是否暴击 辅修功法14
                        if is_crit:
                            msg1 = "{}发起会心一击，造成了{}伤害"
                        else:
                            msg1 = "{}发起攻击，造成了{}伤害"
                        player1_atk_msg = msg1.format(player1['道号'],
                                                      number_to(int(player1_sh * (boss_js + user1_break))))
                        play_list.append(player1_atk_msg)
                        boss['气血'] = boss['气血'] - int(
                            user1_skill_sh * (0.2 + boss_js + user1_break) + (player1_sh * (boss_js + user1_break)))
                        boss_hp_msg = f"{boss['name']}剩余血量{number_to(boss['气血'])}"
                        play_list.append(boss_hp_msg)
                        sh += user1_skill_sh * (0.2 + boss_js + user1_break) + (player1_sh * (boss_js + user1_break))

                    elif user1skill_type == 3:  # buff类技能
                        user1buff_type = user1_skill_date['bufftype']
                        if user1buff_type == 1:  # 攻击类buff
                            is_crit, player1_sh = await get_turnatk(player1, user1_skill_sh,
                                                                    user1_battle_buff_date, boss_buff,
                                                                    random_buff)  # 判定是否暴击 辅修功法14

                            if is_crit:
                                msg1 = "{}发起会心一击，造成了{}伤害"
                            else:
                                msg1 = "{}发起攻击，造成了{}伤害"
                            player1_turn_cost = player1_turn_cost - 1
                            play_list.append(
                                f"{user1_skill_date['name']}增伤剩余:{player1_turn_cost}回合")
                            player1_atk_msg = msg1.format(player1['道号'], number_to(player1_sh * boss_js))
                            play_list.append(player1_atk_msg)
                            boss['气血'] = boss['气血'] - int(player1_sh * (boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                            boss_hp_msg = f"{boss['name']}剩余血量{number_to(boss['气血'])}"
                            play_list.append(boss_hp_msg)
                            sh += int(player1_sh * (boss_js + user1_break))

                        elif user1buff_type == 2:  # 减伤类buff,需要在player2处判断
                            is_crit, player1_sh = await get_turnatk(player1, 0, user1_battle_buff_date, boss_buff,
                                                                    random_buff)  # 判定是否暴击 辅修功法14
                            if is_crit:
                                msg1 = "{}发起会心一击，造成了{}伤害"
                            else:
                                msg1 = "{}发起攻击，造成了{}伤害"

                            player1_turn_cost = player1_turn_cost - 1
                            play_list.append(f"减伤剩余{player1_turn_cost}回合！")
                            player1_atk_msg = msg1.format(player1['道号'], number_to(player1_sh * boss_js))
                            play_list.append(player1_atk_msg)
                            boss['气血'] = boss['气血'] - int(player1_sh * (boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                            boss_hp_msg = f"{boss['name']}剩余血量{number_to(boss['气血'])}"
                            play_list.append(boss_hp_msg)
                            player1_js = player1_f_js - user1_skill_sh
                            sh += int(player1_sh * (boss_js + user1_break))

                    elif user1skill_type == 4:  # 封印类技能
                        player1_turn_cost = player1_turn_cost - 1
                        skillmsg = get_persistent_skill_msg(player1['道号'], user1_skill_date['name'], user1_skill_sh,
                                                            boss_js, player1_turn_cost)
                        play_list.append(skillmsg)
                        is_crit, player1_sh = await get_turnatk(player1, 0, user1_battle_buff_date, boss_buff,
                                                                random_buff)  # 判定是否暴击 辅修功法14
                        if is_crit:
                            msg1 = "{}发起会心一击，造成了{}伤害"
                        else:
                            msg1 = "{}发起攻击，造成了{}伤害"
                        player1_atk_msg = msg1.format(player1['道号'], number_to(player1_sh * boss_js))
                        play_list.append(player1_atk_msg)
                        boss['气血'] = boss['气血'] - int(player1_sh * (boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                        boss_hp_msg = f"{boss['name']}剩余血量{number_to(boss['气血'])}"
                        play_list.append(boss_hp_msg)
                        sh += int(player1_sh * (boss_js + user1_break))
                        if player1_turn_cost == 0:  # 封印时间到
                            boss_turn_skip = True

            else:  # 休息回合-1
                play_list.append(f"☆------{player1['道号']}动弹不得！------☆")
                if player1_turn_cost > 0:
                    player1_turn_cost -= 1
                if player1_turn_cost == 0:
                    user1_turn_skip = True

        else:  # 没有技能的derB
            play_list.append(f"☆------{player1['道号']}的回合------☆")
            is_crit, player1_sh = await get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
            if is_crit:
                msg1 = "{}发起会心一击，造成了{}伤害"
            else:
                msg1 = "{}发起攻击，造成了{}伤害"
            player1_atk_msg = msg1.format(player1['道号'], number_to(player1_sh * boss_js))
            play_list.append(player1_atk_msg)
            boss['气血'] = boss['气血'] - player1_sh * boss_js
            boss_hp_msg = f"{boss['name']}剩余血量{number_to(boss['气血'])}"
            play_list.append(boss_hp_msg)
            sh += int(player1_sh * (boss_js + user1_break))

            ## 自己回合结束 处理 辅修功法14
        player1, boss, msg = after_atk_sub_buff_handle(player1_sub_open, player1,
                                                       user1_sub_buff_date, player2_health_temp - boss['气血'],
                                                       boss, boss_buff, random_buff)
        if msg:
            play_list.append(msg)
        sh += player2_health_temp - boss['气血']

        if boss['气血'] <= 0:  # boss气血小于0，结算
            play_list.append(f"{player1['道号']}胜利")
            suc = "群友赢了"
            get_stone = boss_now_stone * (1 + stone_buff)
            break

        if player1_turn_cost < 0:  # 休息为负数，如果休息，则跳过回合，正常是0
            user1_turn_skip = False
            player1_turn_cost += 1


            # 没有技能的derB
        if boss_turn_skip:
            boss_sub = random.randint(0, 100)
            if boss_sub <= 8:
                play_list.append(f"☆------{boss['name']}的回合------☆")
                is_crit, boss_sh = get_turnatk_boss(boss, 0, boss_buff)  # 判定是否暴击 辅修功法14
                if is_crit:
                    msg2 = "{}：紫玄掌！！紫星河！！！并且发生了会心一击，造成了{}伤害"
                else:
                    msg2 = "{}：紫玄掌！！紫星河！！！造成了{}伤害"
                play_list.append(msg2.format(boss['name'], number_to(
                    (boss_sh * (1 + boss_buff.boss_zs) * (player1_js - random_buff.random_def) * 5) + (
                            player1['气血'] * 0.3))))
                player1['气血'] = player1['气血'] - (
                    ((boss_sh * (1 + boss_buff.boss_zs) * (player1_js - random_buff.random_def) * 5) + (
                            player1['气血'] * 0.3)))
                play_list.append(
                    f"{player1['道号']}剩余血量{number_to(player1['气血'])}")

            elif 8 <= boss_sub <= 16:
                play_list.append(f"☆------{boss['name']}的回合------☆")
                is_crit, boss_sh = get_turnatk_boss(boss, 0, boss_buff)  # 判定是否暴击 辅修功法14
                if is_crit:
                    msg2 = "{}：子龙朱雀！！！穿透了对方的护甲！并且发生了会心一击，造成了{}伤害"
                else:
                    msg2 = "{}：子龙朱雀！！！穿透了对方的护甲！造成了{}伤害"
                play_list.append(msg2.format(boss['name'], number_to(
                    boss_sh * (1 + boss_buff.boss_zs) * (player1_js - random_buff.random_def + 0.5) * 3)))
                player1['气血'] = player1['气血'] - (
                        boss_sh * (1 + boss_buff.boss_zs) * (player1_js - random_buff.random_def + 0.5) * 3)
                play_list.append(
                    f"{player1['道号']}剩余血量{number_to(player1['气血'])}")

            else:
                play_list.append(f"☆------{boss['name']}的回合------☆")
                is_crit, boss_sh = get_turnatk_boss(boss, 0, boss_buff)  # 判定是否暴击 辅修功法14
                if is_crit:
                    msg2 = "{}发起会心一击，造成了{}伤害"
                else:
                    msg2 = "{}发起攻击，造成了{}伤害"
                play_list.append(msg2.format(boss['name'], number_to(
                    (boss_sh * (1 + boss_buff.boss_zs) * (player1_js - random_buff.random_def)))))
                player1['气血'] = player1['气血'] - (
                        boss_sh * (1 + boss_buff.boss_zs) * (player1_js - random_buff.random_def))
                play_list.append(
                    f"{player1['道号']}剩余血量{number_to(player1['气血'])}")

        else:
            play_list.append(f"☆------{boss['name']}动弹不得！------☆")

        if player1['气血'] <= 0:  # 玩家2气血小于0，结算
            play_list.append(f"{boss['name']}胜利")
            suc = "Boss赢了"

            zx = boss['总血量']

            get_stone = int(boss_now_stone * ((qx - boss['气血']) / zx) * (1 + stone_buff))
            boss['stone'] = boss_now_stone - get_stone
            break

        if player1['气血'] <= 0 or boss['气血'] <= 0:
            play_list.append("逻辑错误！")
            break

    if not suc:
        play_list.append("你们打到天昏地暗被大能制止！！！！")
        suc = "Boss赢了"

    if is_sql:
        await sql_message.update_user_hp_mp(
            player1['user_id'],
            max(1, int(min(player1['max_hp'], player1['气血']) / player1['hp_buff'])),
            int(min(player1['max_mp'], player1['真元']) / player1['mp_buff']))
    return play_list, suc, boss, get_stone


async def get_user_def_buff(user_id):
    user_armor_data = await UserBuffDate(user_id).get_user_armor_buff_data()
    user_weapon_data = await UserBuffDate(user_id).get_user_weapon_data()  # 武器减伤
    user_main_data = await UserBuffDate(user_id).get_user_main_buff_data()  # 功法减伤
    if user_weapon_data is not None:
        weapon_def = user_weapon_data['def_buff']  # 武器减伤
    else:
        weapon_def = 0
    if user_main_data is not None:
        main_def = user_main_data['def_buff']  # 功法减伤
    else:
        main_def = 0
    if user_armor_data is not None:
        def_buff = user_armor_data['def_buff']  # 减伤公式
    else:
        def_buff = 0
    return round((1 - def_buff) * (1 - weapon_def) * (1 - main_def), 2)  # 初始减伤率


async def get_turnatk(
        player, buff=0, user_battle_buff_date=None,
        boss_buff: BossBuff = empty_boss_buff,
        random_buff: UserRandomBuff = empty_ussr_random_buff):  # 辅修功法14
    if user_battle_buff_date is None:
        pass
    sub_atk = 0
    sub_crit = 0
    sub_dmg = 0
    zwsh = 0
    user_id = player['user_id']
    try:
        user_buff_data = UserBuffDate(user_id)
        weapon_zw = await UserBuffDate(user_id).get_user_weapon_data()
        main_zw = await user_buff_data.get_user_main_buff_data()
        if main_zw["ew"] == weapon_zw["zw"] and weapon_zw["zw"] != 0:
            zwsh = 0.5
        else:
            zwsh = 0
        main_critatk_data = await user_buff_data.get_user_main_buff_data()  # 功法会心伤害
        user_sub_buff_date = {}
        if (await user_buff_data.get_user_sub_buff_data()) is not None:
            user_sub_buff_date = await UserBuffDate(user_id).get_user_sub_buff_data()
        buff_value = int(user_sub_buff_date['buff'])
        buff_type = user_sub_buff_date['buff_type']
        if buff_type == '1':
            sub_atk = buff_value / 100  # 辅修功法buff实现
        else:
            sub_atk = 0
        if buff_type == '2':
            sub_crit = buff_value / 100
        else:
            sub_crit = 0
        if buff_type == '3':
            sub_dmg = buff_value / 100
        else:
            sub_dmg = 0
    except:
        main_critatk_data = None
        # 原会心计算出现bug，利用我的状态正常会心显示修复
    user_buff_data = UserBuffDate(user_id)
    user_armor_crit_data = await user_buff_data.get_user_armor_buff_data()  # 我的状态防具会心
    user_weapon_data = await UserBuffDate(user_id).get_user_weapon_data()  # 我的状态武器减伤
    user_main_crit_data = await UserBuffDate(user_id).get_user_main_buff_data()  # 我的状态功法会心
    if user_armor_crit_data is not None:  # 我的状态防具会心
        armor_crit_buff = ((user_armor_crit_data['crit_buff']) * 100)
    else:
        armor_crit_buff = 0

    if user_weapon_data is not None:
        crit_buff = ((user_weapon_data['crit_buff']) * 100)
    else:
        crit_buff = 0
    if user_main_crit_data is not None:  # 我的状态功法会心
        main_crit_buff = ((user_main_crit_data['crit_buff']) * 100)
    else:
        main_crit_buff = 0
    impart_data = await xiuxian_impart.get_user_info_with_id(user_id)
    weapon_critatk_data = await UserBuffDate(user_id).get_user_weapon_data()  # 我的状态武器会心伤害
    impart_know_per = impart_data['impart_know_per'] if impart_data is not None else 0
    impart_burst_per = impart_data['impart_burst_per'] if impart_data is not None else 0
    weapon_critatk = weapon_critatk_data['critatk'] if weapon_critatk_data is not None else 0  # 武器会心伤害
    main_critatk = main_critatk_data['critatk'] if main_critatk_data is not None else 0  # 功法会心伤害
    crit_per = crit_buff + int(
        (
                impart_know_per + sub_crit - boss_buff.boss_jh + random_buff.random_hx) * 100) + armor_crit_buff + main_crit_buff
    # 新会心实现，包含辅修，boss减暴击，随机buff效果，武器&装备暴击，功法暴击
    is_crit = False
    turnatk = int(round(random.uniform(0.95, 1.05), 2)
                  * (player['攻击'] * (buff + sub_atk + 1) * (1 - boss_buff.boss_jg)) * (1 + zwsh))  # 攻击波动,buff是攻击buff
    if random.randint(0, 100) <= crit_per:  # 会心判断
        turnatk = int(turnatk * (
                1.5 + impart_burst_per + weapon_critatk + main_critatk + sub_dmg - boss_buff.boss_jb))  # boss战、切磋、秘境战斗会心伤害公式（不包含抢劫）
        is_crit = True
    return is_crit, turnatk


def get_turnatk_boss(player, buff=0, boss_buff: BossBuff = empty_boss_buff):  # boss伤害计算公式
    is_crit = False
    turnatk = int(round(random.uniform(0.95, 1.05), 2)
                  * (player['攻击'] * (buff + 1)))  # 攻击波动,buff是攻击buff
    if random.randint(0, 100) <= player['会心'] + boss_buff.boss_hx * 100:  # 会心判断
        turnatk = int(turnatk * (1.5 + boss_buff.boss_bs))  # boss战、切磋、秘境战斗会心伤害公式（不包含抢劫）
        is_crit = True
    return is_crit, turnatk


def is_enable_user_skill(player, hpcost, mpcost, turncost, skillrate):  # 是否满足技能释放条件
    skill = False
    if turncost < 0:  # 判断是否进入休息状态
        return skill

    if player['气血'] > hpcost and player['真元'] >= mpcost:  # 判断血量、真元是否满足
        if random.randint(0, 100) <= skillrate:  # 随机概率释放技能
            skill = True
    return skill


async def get_skill_hp_mp_data(player, secbuffdata):
    user_id = player['user_id']
    weapon_data = await UserBuffDate(user_id).get_user_weapon_data()
    if weapon_data is not None and "mp_buff" in weapon_data:
        weapon_mp = weapon_data["mp_buff"]
    else:
        weapon_mp = 0

    hpcost = int(secbuffdata['hpcost'] * player['气血']) if secbuffdata['hpcost'] != 0 else 0
    mpcost = int(secbuffdata['mpcost'] * player['exp'] * (1 - weapon_mp)) if secbuffdata['mpcost'] != 0 else 0
    return hpcost, mpcost, secbuffdata['skill_type'], secbuffdata['rate']


def calculate_skill_cost(player, hpcost, mpcost):
    player['气血'] = player['气血'] - hpcost  # 气血消耗
    player['真元'] = player['真元'] - mpcost  # 真元消耗

    return player


def get_persistent_skill_msg(username, skillname, sh, js, turn):
    if type(sh) == bool:
        if sh:
            return f"{username}的封印技能：{skillname}，剩余回合：{turn}!"
    return f"{username}的持续性技能：{skillname}，造成{number_to(sh * (0.2 + js))}伤害，剩余回合：{turn}!"


async def get_skill_sh_data(player, secbuffdata, js):
    skillmsg = ''
    if secbuffdata['skill_type'] == 1:  # 连续攻击类型
        turncost = -secbuffdata['turncost']
        is_crit, turnatk = await get_turnatk(player)
        atkvalue = secbuffdata['atkvalue']  # 列表
        skillsh = 0
        atkmsg = ''
        for value in atkvalue:
            atkmsg += f"{int(value * turnatk * js)}伤害、"
            skillsh += int(value * turnatk)

        if turncost == 0:
            turnmsg = '!'
        else:
            turnmsg = f"，休息{secbuffdata['turncost']}回合！"

        if is_crit:
            skillmsg = (f"{player['道号']}发动技能：{secbuffdata['name']}，"
                        f"消耗气血{number_to(int(secbuffdata['hpcost'] * player['气血'])) if secbuffdata['hpcost'] != 0 else 0}点、"
                        f"真元{number_to(int(secbuffdata['mpcost'] * player['exp'])) if secbuffdata['mpcost'] != 0 else 0}点，"
                        f"{secbuffdata['desc']}并且发生了会心一击，造成{number_to(atkmsg[:-1])}，共计{number_to(skillsh * js)}点伤害{turnmsg}")
        else:
            skillmsg = (f"{player['道号']}发动技能：{secbuffdata['name']}，"
                        f"消耗气血{number_to(int(secbuffdata['hpcost'] * player['气血'])) if secbuffdata['hpcost'] != 0 else 0}点、"
                        f"真元{number_to(int(secbuffdata['mpcost'] * player['exp'])) if secbuffdata['mpcost'] != 0 else 0}点，"
                        f"{secbuffdata['desc']}造成{number_to(atkmsg[:-1])}，共计{number_to(skillsh * js)}点伤害{turnmsg}")

        return skillmsg, skillsh, turncost

    elif secbuffdata['skill_type'] == 2:  # 持续伤害类型
        turncost = secbuffdata['turncost']
        is_crit, turnatk = await get_turnatk(player)
        skillsh = int(secbuffdata['atkvalue'] * player['攻击'])  # 改动
        if is_crit:
            skillmsg = (f"{player['道号']}发动技能：{secbuffdata['name']}，"
                        f"消耗气血{number_to(int(secbuffdata['hpcost'] * player['气血'])) if secbuffdata['hpcost'] != 0 else 0}点、"
                        f"真元{number_to(int(secbuffdata['mpcost'] * player['exp'])) if secbuffdata['mpcost'] != 0 else 0}点，"
                        f"{secbuffdata['desc']}并且发生了会心一击，造成{number_to(skillsh * (0.2 + js))}点伤害，持续{turncost}回合！")
        else:
            skillmsg = (f"{player['道号']}发动技能：{secbuffdata['name']}，"
                        f"消耗气血{number_to(int(secbuffdata['hpcost'] * player['气血'])) if secbuffdata['hpcost'] != 0 else 0}点、"
                        f"真元{number_to(int(secbuffdata['mpcost'] * player['exp'])) if secbuffdata['mpcost'] != 0 else 0}点，"
                        f"{secbuffdata['desc']}造成{number_to(skillsh * (0.2 + js))}点伤害，持续{turncost}回合！")

        return skillmsg, skillsh, turncost

    elif secbuffdata['skill_type'] == 3:  # 持续buff类型
        turncost = secbuffdata['turncost']
        skillsh = secbuffdata['buffvalue']
        if secbuffdata['bufftype'] == 1:
            skillmsg = (f"{player['道号']}发动技能：{secbuffdata['name']}，"
                        f"消耗气血{number_to(int(secbuffdata['hpcost'] * player['气血'])) if secbuffdata['hpcost'] != 0 else 0}点、"
                        f"真元{number_to(int(secbuffdata['mpcost'] * player['exp'])) if secbuffdata['mpcost'] != 0 else 0}点，"
                        f"{secbuffdata['desc']}攻击力增加{skillsh}倍，持续{turncost}回合！")
        elif secbuffdata['bufftype'] == 2:
            skillmsg = (f"{player['道号']}发动技能：{secbuffdata['name']}，"
                        f"消耗气血{number_to(int(secbuffdata['hpcost'] * player['气血'])) if secbuffdata['hpcost'] != 0 else 0}点、"
                        f"真元{number_to(int(secbuffdata['mpcost'] * player['exp'])) if secbuffdata['mpcost'] != 0 else 0}点，"
                        f"{secbuffdata['desc']}获得{skillsh * 100}%的减伤，持续{turncost}回合！")

        return skillmsg, skillsh, turncost

    elif secbuffdata['skill_type'] == 4:  # 封印类技能
        turncost = secbuffdata['turncost']
        if random.randint(0, 100) <= secbuffdata['success']:  # 命中
            skillsh = True
            skillmsg = (f"{player['道号']}发动技能：{secbuffdata['name']}，"
                        f"消耗气血{number_to(int(secbuffdata['hpcost'] * player['气血'])) if secbuffdata['hpcost'] != 0 else 0}点、"
                        f"真元{number_to(int(secbuffdata['mpcost'] * player['exp'])) if secbuffdata['mpcost'] != 0 else 0}点，"
                        f"使对手动弹不得,{secbuffdata['desc']}持续{turncost}回合！")
        else:  # 未命中
            skillsh = False
            skillmsg = (f"{player['道号']}发动技能：{secbuffdata['name']}，"
                        f"消耗气血{number_to(int(secbuffdata['hpcost'] * player['气血'])) if secbuffdata['hpcost'] != 0 else 0}点、"
                        f"真元{number_to(int(secbuffdata['mpcost'] * player['exp'])) if secbuffdata['mpcost'] != 0 else 0}点，"
                        f"{secbuffdata['desc']}但是被对手躲避！")

        return skillmsg, skillsh, turncost


# 处理开局的辅修功法效果
def apply_buff(user_battle_buff, subbuffdata, is_opponent=False):
    buff_type_to_attr = {
        '1': ('atk_buff', "攻击力"),
        '2': ('crit_buff', "暴击率"),
        '3': ('crit_dmg_buff', "暴击伤害"),
        '4': ('health_restore_buff', "气血回复"),
        '5': ('mana_restore_buff', "真元回复"),
        '6': ('health_stolen_buff', "气血吸取"),
        '7': ('mana_stolen_buff', "真元吸取"),
        '8': ('thorns_buff', "中毒"),
        '9': ('hm_stolen_buff', "气血真元吸取"),
        '10': ('jx_buff', "重伤效果"),
        '11': ('fan_buff', "抵消效果"),
        '12': ('stone_buff', "聚宝效果"),
        '13': ('break_buff', "斗战效果"),
    }

    attr, desc = buff_type_to_attr[subbuffdata['buff_type']]
    setattr(user_battle_buff, attr, subbuffdata['buff'])
    if 0 <= int(subbuffdata['buff_type']) <= 10:
        sub_msg = f"提升{subbuffdata['buff']}%{desc}"
    else:
        sub_msg = "获得了特殊效果！！"
    prefix = "。对手" if is_opponent else ""
    return f"{prefix}使用功法{subbuffdata['name']}, {sub_msg}"


def start_sub_buff_handle(player1_sub_open, subbuffdata1, user1_battle_buff_date,
                          player2_sub_open, subbuffdata2, user2_battle_buff_date):
    msg1 = apply_buff(user1_battle_buff_date, subbuffdata1) if player1_sub_open else ""
    msg2 = apply_buff(user2_battle_buff_date, subbuffdata2, is_opponent=True) if player2_sub_open else ""

    return user1_battle_buff_date, user2_battle_buff_date, msg1 + msg2


# 处理攻击后辅修功法效果
def after_atk_sub_buff_handle(
        player1_sub_open, player1,
        subbuffdata1, damage1, player2,
        boss_buff: BossBuff = empty_boss_buff,
        random_buff: UserRandomBuff = empty_ussr_random_buff):
    msg = ""

    if not player1_sub_open:
        return player1, player2, msg

    buff_value = int(subbuffdata1['buff'])
    buff_tow = int(subbuffdata1['buff2'])
    buff_type = subbuffdata1['buff_type']
    max_hp = player1['max_hp']
    max_mp = player1['max_mp']

    if buff_type == '4':
        restore_health = max_hp * buff_value // 100
        player1['气血'] += restore_health
        player1['气血'] = min(player1['气血'], max_hp)
        msg = "回复气血:" + str(number_to(restore_health))
    elif buff_type == '5':
        restore_mana = max_mp * buff_value // 100
        player1['真元'] += restore_mana
        player1['真元'] = min(player1['真元'], max_mp)
        msg = "回复真元:" + str(number_to(restore_mana))
    elif buff_type == '6':
        health_stolen = (damage1 * (buff_value + random_buff.random_xx) // 100) * (1 - boss_buff.boss_xx)
        player1['气血'] += health_stolen
        player1['气血'] = min(player1['气血'], max_hp)
        msg = "吸取气血:" + str(number_to(health_stolen))
    elif buff_type == '7':
        mana_stolen = (damage1 * buff_value // 100) * (1 - boss_buff.boss_xl)
        player1['真元'] += mana_stolen
        player1['真元'] = min(player1['真元'], max_mp)
        msg = "吸取真元:" + str(number_to(mana_stolen))
    elif buff_type == '8':
        poison_damage = player2['气血'] * buff_value // 100
        player2['气血'] -= poison_damage
        msg = "对手中毒消耗血量:" + str(number_to(poison_damage))

    elif buff_type == '9':
        health_stolen = (damage1 * (buff_value + random_buff.random_xx) // 100) * (1 - boss_buff.boss_xx)
        mana_stolen = (damage1 * buff_tow // 100) * (1 - boss_buff.boss_xl)
        player1['气血'] += health_stolen
        player1['气血'] = min(player1['气血'], max_hp)
        player1['真元'] += mana_stolen
        player1['真元'] = min(player1['真元'], max_mp)
        msg = f"吸取气血: {str(number_to(health_stolen))}, 吸取真元: {str(number_to(mana_stolen))}"

    return player1, player2, msg


class UserBattleBuffDate:  # 辅修功法14
    def __init__(self, user_id):
        """用户战斗Buff数据"""
        self.user_id = user_id
        # 攻击buff
        self.atk_buff = 0
        # 攻击buff
        self.atk_buff_time = -1

        # 暴击率buff
        self.crit_buff = 0
        # 暴击率buff
        self.crit_buff_time = -1

        # 暴击伤害buff
        self.crit_dmg_buff = 0
        # 暴击伤害buff
        self.crit_dmg__buff_time = -1

        # 回血buff
        self.health_restore_buff = 0
        self.health_restore_buff_time = -1
        # 回蓝buff
        self.mana_restore_buff = 0
        self.mana_restore_buff_time = -1

        # 吸血buff
        self.health_stolen_buff = 0
        self.health_stolen_buff_time = -1
        # 吸蓝buff
        self.mana_stolen_buff = 0
        self.mana_stolen_buff_time = -1
        # 反伤buff
        self.thorns_buff = 0
        self.thorns_buff_time = -1

        # 破甲buff
        self.armor_break_buff = 0
        self.armor_break_buff_time = -1
