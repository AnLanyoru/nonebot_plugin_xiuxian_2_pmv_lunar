import json
import os
from pathlib import Path

from nonebot.log import logger

from ..xiuxian_database.database_connect import database

# todo 写入数据库

PLAYERSDATA = Path() / "data" / "xiuxian" / "players"


async def read_work_info(user_id):
    data = await database.select(
        table='user_cd',
        where={'user_id': user_id},
        need_column=['work_info'])
    return json.loads(data['work_info'])


async def save_work_info(user_id, data):
    update_data = {
        'work_info': json.dumps(data, ensure_ascii=False)}
    await database.update(
        table='user_cd',
        where={'user_id': user_id},
        **update_data)
    return True
