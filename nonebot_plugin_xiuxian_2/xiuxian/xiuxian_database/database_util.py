import sqlite3
import time
from pathlib import Path

import asyncpg

tower_db = Path() / "data" / "xiuxian" / "players_database" / "modus.db"
limit_db = Path() / "data" / "xiuxian" / "players_database" / "limit.db"
store_db = Path() / "data" / "xiuxian" / "items_database" / "store.db"
main_db = Path() / "data" / "xiuxian" / "xiuxian.db"
impart_db = Path() / "data" / "xiuxian" / "xiuxian_impart.db"
"""
对于无法自动推断类型的数据，需要进行类型修补定义
"""
type_fix = {"user_cd":
                {"create_time": str, "scheduled_time": str, "last_check_info_time": str},
            "sects":
                {"sect_fairyland": str},
            "back":
                {"remake": str}}


async def table_data_move(database, table, sqlite_db_path):
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
    print(f"表{table}数据转移成功! 耗时:{use_time}")


async def all_table_data_move(database, sqlite_db_path, values_type_check: bool = False):
    conn = sqlite3.connect(sqlite_db_path, check_same_thread=False)
    sqlite_cur = conn.cursor()
    sqlite_cur.execute("select name from sqlite_master where type='table'")
    all_tables = sqlite_cur.fetchall()
    print(all_tables)
    if not all_tables:
        print("未获取到原数据库表内容")
        return 404
    for table in all_tables:
        table = table[0]
        sql = f"select * from {table}"
        if table == "BuffInfo":
            table = "buff_info"
        sqlite_cur.execute(sql)
        result = sqlite_cur.fetchall()
        print(f"成功获取到表{table}欲转移数据，数据量", len(result))
        if not result:
            return None
        columns = [column[0] for column in sqlite_cur.description]
        data_dict = dict(zip(columns, result[0]))
        # 类型修补
        if table in type_fix:
            fix_dict = type_fix[table]
            for column_type_fix, goal_type_fix in fix_dict.items():
                data_dict[column_type_fix] = goal_type_fix(data_dict[column_type_fix])

        print(f"开始转移表{table}数据")
        start_time = time.time()
        async with database.pool.acquire() as pg_conn:
            try:
                await pg_conn.execute(f"select count(1) from {table}")
            except asyncpg.exceptions.UndefinedTableError:
                await pg_conn.execute(f"""CREATE TABLE "{table}" (
              "create_mark" boolean
              );""")
        sql, column_types = await database.insert(table=table, create_column=True, **data_dict)
        if sql == "error":
            print('执行初始化错误')
            return 401
        async with database.pool.acquire() as pg_conn:
            data = []
            print('数据预处理开始')
            for row in result[1:]:
                if values_type_check:
                    try:
                        row = [value_type(value if value else 0) for value, value_type in zip(row, column_types)]
                    except (ValueError, TypeError) as e:
                        print(f"类型严重不兼容：", dict(zip(row, column_types)))
                        print(e)
                        return 401
                data.append(row)
            print('数据预处理成功')
            try:
                await pg_conn.executemany(sql, data)
            except asyncpg.exceptions.DataError as e:
                print(f"表{table}数据转移失败")
                print(f"出错sql语句：{sql}")
                print(f"出错数据:")
                print(row)
                print(f"错误信息：", e)
                return 400
        end_time = time.time()
        use_time = (end_time - start_time) * 1000
        print(f"表{table}数据转移成功! 耗时:{use_time}")
