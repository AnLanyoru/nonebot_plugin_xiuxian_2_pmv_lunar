import random

from .fight_base import BaseFightMember


def get_fight(
        pre_fight_dict: dict[int, BaseFightMember],
        max_turn: int = 20
) -> tuple[int, list[str], dict[int, BaseFightMember]]:
    """
    进行战斗
    :param pre_fight_dict: 战斗中对象字典
    :param max_turn: 最大战斗回合 0为无限回合
    """
    # 排轴 排个🥚啊
    # fight_dict = dict(sorted(pre_fight_dict.items(), key=lambda x: x[1].speed, reverse=True))
    fight_dict = pre_fight_dict
    loser = []
    msg_list = []
    winner = None
    for turn in range(1, max_turn + 1):
        for user_id, fight_player in fight_dict.items():
            enemy_list = [user_id for user_id in fight_dict
                          if fight_dict[user_id].team != fight_player.team and fight_dict[user_id].status]
            if not enemy_list:
                msg_list.append(f"{fight_player.name}方胜利！")
                winner = fight_player.team
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
