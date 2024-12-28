import sqlite3
import time
from pathlib import Path

import asyncpg

tower_db = Path() / "data" / "xiuxian" / "players_database" / "modus.db"
limit_db = Path() / "data" / "xiuxian" / "players_database" / "limit.db"
store_db = Path() / "data" / "xiuxian" / "items_database" / "store.db"
main_db = Path() / "data" / "xiuxian" / "xiuxian.db"
impart_db = Path() / "data" / "xiuxian" / "xiuxian_impart.db"


async def data_move(database, table, sqlite_db_path):
    conn = sqlite3.connect(sqlite_db_path, check_same_thread=False)
    sqlite_cur = conn.cursor()
    try:
        sqlite_cur.execute(f"select count(1) from {table}")
    except sqlite3.OperationalError:
        print("目标表原数据库不存在")
        return 404

    sql = f"select * from {table}"
    sqlite_cur.execute(sql)
    result = sqlite_cur.fetchall()
    print("成功获取到欲转移数据，数据量", len(result))
    if not result:
        return None
    columns = [column[0] for column in sqlite_cur.description]
    data_dict = dict(zip(columns, result[0]))
    print(f"开始转移表{table}数据")
    start_time = time.time()
    async with database.pool.acquire() as pg_conn:
        try:
            await pg_conn.execute(f"select count(1) from {table}")
        except asyncpg.exceptions.UndefinedTableError:
            await pg_conn.execute(f"""CREATE TABLE "{table}" (
          "create_mark" boolean
          );""")
    sql = await database.insert(table=table, create_column=True, **data_dict)
    async with database.pool.acquire() as pg_conn:
        for row in result[1:]:
            await pg_conn.execute(sql, *row)
    end_time = time.time()
    use_time = (end_time - start_time) * 1000
    print(f"数据转移成功! 耗时:{use_time}")
