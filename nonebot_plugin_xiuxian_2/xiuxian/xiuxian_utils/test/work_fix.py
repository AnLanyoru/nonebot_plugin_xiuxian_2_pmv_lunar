import threading
import aiosqlite
import time
from datetime import datetime
from pathlib import Path

DATABASE = Path()
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_number = "123451234"
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


# 本模块用于独立化数据库操作光标对象，防止有需要独立读取时引发的循环导入
class XiuxianDateCur:
    global xiuxian_num
    _instance = {}
    _has_init = {}

    def __new__(cls):
        if cls._instance.get(xiuxian_num) is None:
            cls._instance[xiuxian_num] = super(XiuxianDateCur, cls).__new__(cls)
        return cls._instance[xiuxian_num]

    def __init__(self):
        if not self._has_init.get(xiuxian_num):
            self._has_init[xiuxian_num] = True
            self.database_path = DATABASE
            if not self.database_path.exists():
                self.database_path.mkdir(parents=True)
                self.database_path /= "xiuxian.db"
                self.conn = aiosqlite.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()
            else:
                self.database_path /= "xiuxian.db"
                self.conn = aiosqlite.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()
            print(f"<green>修仙数据库已连接！</green>")

    def close(self):
        self.conn.close()
        print(f"<green>修仙数据库关闭！</green>")

    def get_all_user_id(self):
        """获取全部用户id"""
        sql = "SELECT user_id FROM user_xiuxian"
        cur = self.conn.cursor()
        cur.execute(sql, )
        result = cur.fetchall()
        if result:
            return [row[0] for row in result]
        else:
            return None

    def get_work_num(self, user_id):  # todo 回滚主动更新
        """获取用户悬赏令刷新次数
           拥有被动效果，检测隔日自动重置悬赏令刷新 次数
        """
        sql = f"SELECT work_num FROM user_xiuxian WHERE user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if result:
            work_num = int(result[0])
        else:
            work_num = 0
        return work_num

    def update_work_num(self, user_id, work_num):
        sql = f"UPDATE user_xiuxian SET work_num=? WHERE user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (work_num, user_id,))
        self.conn.commit()

sql_message = XiuxianDateCur()

def fix_work(user_id):
    work_num = await sql_message.get_work_num(str(user_id))
    real_work_num = int(str(work_num)[-1:])
    if work_num < 10:
        print(work_num)
        print(f"无需修复")
        return 0
    work_day = str(work_num)[:-1]
    now = time.localtime()
    now_day = str(now.tm_year) + str(now.tm_mon) + str(now.tm_mday)
    if now_day == work_day:
        await sql_message.update_work_num(user_id, real_work_num)
        print(f"修复完成，设定为：{real_work_num}")
    else:
        await sql_message.update_work_num(user_id, 0)
        print(f"修复完成, 补满")
    return 0

all_users = await sql_message.get_all_user_id()

for fix_user_id in all_users:
    fix_work(fix_user_id)

await sql_message.close()
