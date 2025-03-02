from datetime import datetime

import asyncpg

from .shop_models import Goods
from .. import DRIVER
from ..xiuxian_database.database_connect import database
from ..xiuxian_utils.clean_utils import zips
from ..xiuxian_utils.item_json import items


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


async def create_goods_many(user_id: int, item_dict: dict[int, int], price: int):
    sql = ('insert into world_shop (owner_id, item_id, item_type, item_price, insert_time, buyer) '
           'values ($1, $2, $3, $4, $5, 0)')
    insert_data = []
    now_time = datetime.now()
    for item_id, item_num in item_dict.items():
        item_info = items.get_data_by_item_id(item_id)
        item_type = item_info['item_type']
        goods_tuple = (user_id, item_id, item_type, price, now_time)
        for _ in range(item_num):
            insert_data.append(goods_tuple)

    async with database.pool.acquire() as conn:
        update_result = await conn.executemany(sql, insert_data)
    return update_result


async def mark_goods(goods_id, mark_user_id):
    sql = 'update world_shop set buyer=$1 where id=$2 and buyer=0'
    async with database.pool.acquire() as conn:
        update_result = await conn.execute(sql, mark_user_id, goods_id)
    return update_result


async def mark_goods_many(goods_id_list: list[str], mark_user_id: int) -> str:
    sql: str = 'update world_shop set buyer=$1 where id=$2 and buyer=0'
    mark_data: list[tuple[int, str]] = [(mark_user_id, goods_id) for goods_id in goods_id_list]
    async with database.pool.acquire() as conn:
        update_result = await conn.executemany(sql, mark_data)
    return update_result


async def fetch_goods_min_price_type(user_id, item_type: tuple[str]) -> list[dict]:
    sql_arg = ','.join([f"${no}" for no in range(2, len(item_type) + 2)])
    sql = ('select item_id, min(item_price) as item_price '
           'from world_shop '
           f'where item_type in ({sql_arg}) and buyer=0 and owner_id != $1 '
           'group by item_id')
    async with database.pool.acquire() as conn:
        result = await conn.fetch(sql, user_id, *item_type)
    result_all = [zips(**result_per) for result_per in result]
    return result_all


async def fetch_goal_goods_data(item_id, user_id) -> Goods | None:
    sql = ('select id, owner_id, item_id, item_type, item_price '
           'from world_shop '
           'where item_id=$1 and buyer=0 and owner_id != $2 '
           'order by item_price asc '
           'limit 1')
    async with database.pool.acquire() as conn:
        result = await conn.fetch(sql, item_id, user_id)
    result_all = zips(**result[0]) if result else None
    return result_all


async def fetch_self_goods_data(item_id, user_id) -> Goods | None:
    sql = ('select id, owner_id, item_id, item_type, item_price '
           'from world_shop '
           'where item_id=$1 and buyer=0 and owner_id=$2 '
           'limit 1')
    async with database.pool.acquire() as conn:
        result = await conn.fetch(sql, item_id, user_id)
    result_all = zips(**result[0]) if result else None
    return result_all


async def fetch_self_goods_data_all(user_id: int) -> list[Goods]:
    sql = ('select id, owner_id, item_id, item_type, item_price '
           'from world_shop '
           'where buyer=0 and owner_id=$1 '
           'limit 10000')
    async with database.pool.acquire() as conn:
        result = await conn.fetch(sql, user_id)
    result_all = [zips(**result_per) for result_per in result]
    return result_all


async def fetch_self_goods_data_all_type(user_id: int, item_type: tuple[str]) -> list[Goods]:
    sql_arg = ','.join([f"${no}" for no in range(2, len(item_type) + 2)])
    sql = ('select id, owner_id, item_id, item_type, item_price '
           'from world_shop '
           f'where item_type in ({sql_arg}) and buyer=0 and owner_id=$1 '
           'limit 10000')
    async with database.pool.acquire() as conn:
        result = await conn.fetch(sql, user_id, *item_type)
    result_all = [zips(**result_per) for result_per in result]
    return result_all


async def fetch_goods_data_by_id(item_shop_id, user_id) -> Goods | None:
    sql = ('select id, owner_id, item_id, item_type, item_price '
           'from world_shop '
           'where id=$1 and buyer=0 and owner_id != $2')
    async with database.pool.acquire() as conn:
        result = await conn.fetch(sql, item_shop_id, user_id)
    result_all = zips(**result[0]) if result else None
    return result_all


async def fetch_goal_goods_data_many(item_id, user_id, num: int = 12) -> list[Goods]:
    sql = ('select id, owner_id, item_id, item_type, item_price '
           'from world_shop '
           'where item_id=$1 and buyer=0 and owner_id != $2 '
           'order by item_price asc '
           'limit ($3)')
    async with database.pool.acquire() as conn:
        result = await conn.fetch(sql, item_id, user_id, num)
    result_all = [zips(**result_per) for result_per in result]
    return result_all
