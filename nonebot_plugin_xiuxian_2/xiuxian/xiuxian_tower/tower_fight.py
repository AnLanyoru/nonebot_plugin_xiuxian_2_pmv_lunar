from ..user_data_handle import UserBuffHandle
from ..xiuxian_config import convert_rank
from ..xiuxian_utils.player_fight import boss_fight
from ..xiuxian_utils.xiuxian2_handle import sql_message


async def get_tower_battle_info(user_info, tower_floor_info: dict):
    """获取Boss战事件的内容"""
    player = await UserBuffHandle(user_info['user_id']).get_user_fight_info()
    player['道号'] = player['user_name']
    player['气血'] = player['fight_hp']
    player['攻击'] = player['atk']
    player['真元'] = player['fight_mp']

    boss_info = {
        "name": tower_floor_info["name"],
        "气血": int(tower_floor_info["hp"]),
        "总血量": int(tower_floor_info["hp"]),
        "攻击": int(tower_floor_info["atk"]),
        "真元": int(tower_floor_info["mp"]),
        "jj": f"{convert_rank()[1][72][:3]}",
        'stone': 1,
        'defence': (1 - int(tower_floor_info['defence']) / 100)
    }

    result, victor, _, _ = await boss_fight(player, boss_info)  # 未开启，1不写入，2写入

    return result, victor
