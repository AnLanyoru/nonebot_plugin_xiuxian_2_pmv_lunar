import asyncpg
from asyncpg import Pool

from .database_config import database_config  # 这是上面的config()代码块，已经保存在config.py文件中
from .. import DRIVER
from ..xiuxian_utils.clean_utils import zips

params = database_config()
date_type_set = {str: "TEXT", int: "numeric DEFAULT 0", float: "numeric DEFAULT 0", bytes: "bytea", None: "TEXT"}
db_dict = {}


async def create_pool():
    pool = await asyncpg.create_pool(
        database=params['database'],
        user=params['user'],
        password=params['password'],
        host=params['host'],
        port=params['port'],
        max_inactive_connection_lifetime=6000)
    return pool


class DataBase:
    def __init__(self):
        self.pool: Pool = None

    async def connect_pool_make(self):
        self.pool = await create_pool()

    async def get_version(self):
        async with self.pool.acquire() as db:
            cursor = await db.fetch('SELECT version()')
            db_version = cursor[0][0]
            print(f"登录数据库成功，数据库版本：{db_version}")

    async def sql_execute(self, sql: str, data=None):
        if not data:
            async with self.pool.acquire() as db:
                await db.execute(sql)
            return True
        else:
            async with self.pool.acquire() as db:
                await db.execute(sql, *data)
            return True

    async def select(self, table: str, where: dict, need_column: list = None):
        """
        简单逻辑数据查找接口
        """

        if need_column is None:
            need_column = ['*']

        need_column_str = ",".join(need_column)
        if where:
            where_column = ",".join([f"{column_name}=${count}" for column_name, count
                                     in zip(where.keys(), range(1, 1 + len(where)))])

            async with self.pool.acquire() as db:
                sql = f"select {need_column_str} from {table} WHERE {where_column}"
                result = await db.fetch(sql, *where.values())
                return zips(**result[0]) if result else None
        else:
            async with self.pool.acquire() as db:
                sql = f"select {need_column_str} from {table}"
                result = await db.fetch(sql)
                return zips(**result[0]) if result else None

    async def update(self, table: str, where: dict, create_column: bool = 0, **kwargs):
        """
        简单逻辑数据更新接口
        """
        column_count = len(kwargs) + 1

        update_column = ",".join([f"{column_name}=${count}" for column_name, count
                                  in zip(kwargs.keys(), range(1, column_count))])

        where_column = ",".join([f"{column_name}=${count}" for column_name, count
                                 in zip(where.keys(), range(column_count, column_count + len(where)))])

        async with self.pool.acquire() as db:
            if create_column:
                columns = list(*where.keys(), *kwargs.keys())
                values = list(*where.values(), *kwargs.values())
                for column, value in zip(columns, values):
                    column_type = date_type_set.get(type(value))
                    try:
                        await db.execute(f"select {column} from {table}")
                    except asyncpg.exceptions.UndefinedColumnError:
                        sql = f"ALTER TABLE {table} ADD COLUMN {column} {column_type};"
                        await db.execute(sql)
            sql = f"UPDATE {table} set {update_column} WHERE {where_column}"
            await db.execute(sql, *kwargs.values(), *where.values())

    async def insert(self, table: str, create_column: bool = 0, **kwargs):
        """
        简单逻辑数据插入接口
        """
        column_count = len(kwargs) + 1

        insert_column = ",".join(kwargs)

        value_format = ",".join([f"${count}" for count in range(1, column_count)])

        async with self.pool.acquire() as db:
            column_types = []
            if create_column:
                for column, value in kwargs.items():
                    column_types.append(type(value))
                    column_type = date_type_set.get(type(value))
                    try:
                        await db.execute(f"select {column} from {table}")
                    except asyncpg.exceptions.UndefinedColumnError:
                        sql = f"ALTER TABLE {table} ADD COLUMN {column} {column_type};"
                        try:
                            await db.execute(sql)
                        except (asyncpg.exceptions.DataError, asyncpg.exceptions.PostgresSyntaxError) as e:
                            print(f"表{table}数据插入失败")
                            print(f"出错sql语句：{sql}")
                            print(f"出错数据：{value}")
                            print("错误信息：", e)
                            return "error", None
            # 数据插入
            try:
                sql = f"""INSERT INTO {table} ({insert_column}) VALUES ({value_format})"""
                await db.execute(sql, *kwargs.values())
                return sql, column_types
            except (asyncpg.exceptions.DataError, asyncpg.exceptions.PostgresSyntaxError) as e:
                print(f"表{table}数据插入失败")
                print(f"出错sql语句：{sql}")
                print(f"出错数据:")
                print(kwargs.values())
                print("错误信息：", e)
                return "error", None


database = DataBase()


@DRIVER.on_startup
async def connect_db():
    global database
    await database.connect_pool_make()
    await database.get_version()


@DRIVER.on_shutdown
async def close_db():
    await database.pool.close()
