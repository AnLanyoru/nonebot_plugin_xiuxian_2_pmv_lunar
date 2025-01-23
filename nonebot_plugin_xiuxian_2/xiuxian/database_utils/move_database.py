from ..xiuxian_database.database_connect import database

try:
    import ujson as json
except ImportError:
    import json
from pathlib import Path

PLAYERSDATA = Path() / "data" / "xiuxian" / "players"


async def read_move_data(user_id):
    data = await database.select(
        table='user_cd',
        where={'user_id': user_id},
        need_column=['move_info'])
    return json.loads(data['move_info'])


async def save_move_data(user_id, data):
    update_data = {
        'move_info': json.dumps(data, ensure_ascii=False)}
    await database.update(
        table='user_cd',
        where={'user_id': user_id},
        **update_data)
    return True
