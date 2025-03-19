import random

from .fight_base import BaseFightMember
from .fight_player import PlayerFight
from ...xiuxian_utils.xiuxian2_handle import sql_message


async def player_fight(user_id_dict: dict[int, int], fight_key: int = 0):
    """
    玩家战斗
    :param user_id_dict: 需要进入战斗的玩家id字典{玩家id:玩家阵营}，例{123456:1, 123457:2}
    :param fight_key:战斗类型 0不掉血战斗，切磋，1掉血战斗，没做好，你敢调用就敢给你爆了
    """
    fight_dict = {}  # 初始化战斗字典
    for user_id, team in user_id_dict.items():
        user_fight_info = await sql_message.get_user_real_info(user_id)
        fight_dict[user_id] = PlayerFight(user_fight_info, team)
    winner, fight_msg, after_fight_user_info_list = get_fight(fight_dict, max_turn=30)
    if fight_key:
        for user_id, user_after_fight_info in after_fight_user_info_list.items():
            await sql_message.update_user_info_by_fight_obj(user_id, user_after_fight_info)
    fight_msg = '\r'.join(fight_msg)
    return winner, fight_msg


def get_fight(
        pre_fight_dict: dict[int, BaseFightMember],
        max_turn: int = 20) \
        -> tuple[str, list[str], dict[int, BaseFightMember]]:
    """
    进行战斗
    :param pre_fight_dict: 战斗中对象字典
    :param max_turn: 最大战斗回合 0为无限回合
    """
    # 排轴 个🥚啊
    # fight_dict = dict(sorted(pre_fight_dict.items(), key=lambda x: x[1].speed, reverse=True))
    fight_dict = pre_fight_dict
    loser = []
    msg_list = []
    winner = None
    for turn in range(1, max_turn + 1):
        if winner:
            break
        msg_list.append(f"\r⭐第{turn}回合⭐\r")
        for user_id, fight_player in fight_dict.items():
            enemy_list = [user_id for user_id in fight_dict
                          if fight_dict[user_id].team != fight_player.team and fight_dict[user_id].status]
            if not enemy_list:
                msg_list.append(f"{fight_player.name}方胜利！")
                winner = fight_player.name
                break
            enemy_id = random.choice(enemy_list)
            enemy = fight_dict[enemy_id]
            fight_player.active(enemy, msg_list)
            if kill_user := fight_player.turn_kill:
                loser.append(kill_user)
                fight_dict[kill_user].status = 0
    if not winner:
        msg_list.append("你们打到天昏地暗，被大能叫停！！！")
    # 盘点回合
    return winner, msg_list, fight_dict
