from datetime import datetime

import asyncpg

from .. import DRIVER
from ..xiuxian_database.database_connect import database
from ..xiuxian_utils.clean_utils import zips


# 创建一个临时活动数据库
@DRIVER.on_startup
async def shop_prepare():
    async with database.pool.acquire() as conn:
        try:
            await conn.execute(f"select count(1) from world_shop")
        except asyncpg.exceptions.UndefinedTableError:
            await conn.execute(f"""CREATE TABLE "world_shop" (
                "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                "owner_id" bigint DEFAULT 0,
                "item_id" bigint DEFAULT 0,
                "item_type" text,
                "item_price" numeric DEFAULT 0,
                "insert_time" timestamp,
                "buyer" bigint DEFAULT 0
                );""")
            await conn.execute("CREATE INDEX ON world_shop (item_id);")


async def create_goods(user_id, item_id, item_type, price: int):
    item_data = {"owner_id": user_id,
                 "item_id": item_id,
                 "item_type": item_type,
                 "item_price": price,
                 "insert_time": datetime.now(),
                 "buyer": 0}
    await database.insert(table='world_shop',
                          **item_data)


async def mark_goods(goods_id, mark_user_id):
    sql = 'update world_shop set buyer=$1 where id=$2 and buyer=0'
    async with database.pool.acquire() as conn:
        update_result = await conn.execute(sql, mark_user_id, goods_id)
    return update_result


async def fetch_goods_min_price_type(user_id, item_type: tuple[str]):
    sql_arg = ','.join([f"${no}" for no in range(2, len(item_type) + 2)])
    sql = ('select item_id, min(item_price) as item_price '
           'from world_shop '
           f'where item_type in ({sql_arg}) and buyer=0 and owner_id != $1 '
           'group by item_id')
    async with database.pool.acquire() as conn:
        result = await conn.fetch(sql, user_id, *item_type)
    result_all = [zips(**result_per) for result_per in result]
    return result_all


async def fetch_goal_goods_data(item_id, user_id):
    sql = ('select id, owner_id, item_id, item_type, item_price '
           'from world_shop '
           'where item_id=$1 and buyer=0 and owner_id != $2 '
           'order by item_price desc '
           'limit 1')
    async with database.pool.acquire() as conn:
        result = await conn.fetch(sql, item_id, user_id)
    result_all = zips(**result[0]) if result else {}
    return result_all


async def fetch_goods_data_by_id(item_shop_id, user_id):
    sql = ('select id, owner_id, item_id, item_type, item_price '
           'from world_shop '
           'where id=$1 and buyer=0 and owner_id != $2')
    async with database.pool.acquire() as conn:
        result = await conn.fetch(sql, item_shop_id, user_id)
    result_all = zips(**result[0]) if result else {}
    return result_all
