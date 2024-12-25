import asyncpg

from .database_config import database_config  # 这是上面的config()代码块，已经保存在config.py文件中
from .. import DRIVER

params = database_config()

db_dict = {}


async def create_pool():
    pool = await asyncpg.create_pool(
        database=params['database'],
        user=params['user'],
        password=params['password'],
        host=params['host'],
        port=params['post'])
    return pool


class DataBase:
    def __init__(self):
        self.pool = None

    async def connect_pool_make(self):
        self.pool = await create_pool()

    async def get_version(self):
        async with self.pool.acquire() as db:
            cursor = await db.fetch('SELECT version()')
            db_version = cursor[0]
            print(f"登录数据库成功，数据库版本：{db_version}")


database = DataBase()


@DRIVER.on_startup
async def connect_db():
    global database
    await database.connect_pool_make()
    await database.get_version()
