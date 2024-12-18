import threading
import aiosqlite
from datetime import datetime
from pathlib import Path
from .. import DRIVER

WORKDATA = Path() / "data" / "xiuxian" / "work"
PLAYERSDATA = Path() / "data" / "xiuxian" / "players"
DATABASE = Path() / "data" / "xiuxian"
DATABASE_IMPARTBUFF = Path() / "data" / "xiuxian"
SKILLPATHH = DATABASE / "功法"
WEAPONPATH = DATABASE / "装备"
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_number = "123451234"
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

connect_pool = threading.local()


# 本模块用于独立化数据库操作光标对象，防止有需要独立读取时引发的循环导入
class XiuxianDateBase:

    def __init__(self):
        self.database_path = DATABASE
        if not self.database_path.exists():
            self.database_path.mkdir(parents=True)
            self.database_path /= "xiuxian.db"
        else:
            self.database_path /= "xiuxian.db"

    async def get_db(self):
        db_instance = getattr(connect_pool, 'db_instance', None)
        if db_instance is None:
            connect_pool.db_instance = await aiosqlite.connect(self.database_path)
        return connect_pool.db_instance

    async def close(self):
        self.get_db().close()


@DRIVER.on_shutdown
async def close_db():
    await XiuxianDateBase().close()
