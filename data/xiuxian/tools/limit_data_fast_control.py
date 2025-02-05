import asyncio
from configparser import ConfigParser
from datetime import datetime, timedelta
from pathlib import Path

import asyncpg

from limit_database import limit_data, limit_handle

DATABASE = Path()
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_number = "123451234"
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


async def get_all_user_id_10():
    """获取全部用户id"""
    sql = "SELECT user_id FROM new_year_temp ORDER BY fight_damage DESC limit 10"
    async with limit_data.pool.acquire() as db:
        result = await db.fetch(sql)
        if result:
            return [row[0] for row in result]
        else:
            return None


async def get_all_user_id_any():
    """获取全部用户id"""
    sql = "SELECT user_id FROM new_year_temp where fight_damage>0"
    async with limit_data.pool.acquire() as db:
        result = await db.fetch(sql)
        if result:
            return [row[0] for row in result]
        else:
            return None


async def get_all_owner_user_id(item_id):
    """获取全部拥有某物品的用户id"""
    sql = "SELECT user_id FROM back where goods_id=$1"
    async with limit_data.pool.acquire() as db:
        result = await db.fetch(sql, item_id)
        if result:
            return [row[0] for row in result]
        else:
            return []


async def send_all_user_item(all_user_id: list, item_info: dict, send_num: int, is_bind: bool = False):
    now_time = datetime.now()
    now_time = str(now_time)
    need_send_item = item_info['id']
    had_user_id = await get_all_owner_user_id(need_send_item)
    update_user_id = [user_id for user_id in all_user_id
                      if user_id in had_user_id]
    insert_user_id = [user_id for user_id in all_user_id
                      if user_id not in update_user_id]

    async with limit_data.pool.acquire() as db:
        if update_user_id:
            sql = (f"UPDATE back set goods_num=goods_num+$1,update_time=$2,bind_num=bind_num+$3 "
                   f"WHERE user_id=$4 and goods_id=$5")
            update_data = []
            for user_id in update_user_id:
                update_data.append((send_num, now_time, send_num * is_bind, user_id, need_send_item))
            await db.executemany(sql, update_data)
        if insert_user_id:
            sql = (f"INSERT INTO back "
                   f"(user_id, goods_id, goods_name, goods_type, goods_num, create_time, update_time, bind_num) "
                   f"VALUES ($1,$2,$3,$4,$5,$6,$7,$8)")
            insert_data = []
            for user_id in insert_user_id:
                insert_data.append(
                    (user_id, need_send_item, item_info['name'], item_info['type'], send_num,
                     now_time, now_time, send_num * is_bind))
            await db.executemany(sql, insert_data)


def database_config(filename=Path(__file__).parent / 'database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db


params = database_config()


class Date:
    def __init__(self):
        self.base_date = datetime.now()
        self.base_date_change = self.base_date.date()

    def today(self):
        return self.base_date_change


async def create_pool():
    pool = await asyncpg.create_pool(
        database=params['database'],
        user=params['user'],
        password=params['password'],
        host=params['host'],
        port=params['port'],
        max_inactive_connection_lifetime=6000)
    return pool


date = Date()


async def fast_handle():
    now_time = date.today()
    print("欢迎使用快速活动&补偿&限制操作系统\n", "现在是：", now_time, '\n')
    print(
        "请选择你要进行的操作：\n1：操作活动信息\n2：操作补偿信息\n3：操作用户限制信息(making)\n4：进行模拟用户操作(测试用)\n5:发放年兽奖励")
    choice = None
    while choice not in [1, 2, 3, 4, 5]:
        choice = int(input("请选择你要进行的操作:"))
    if choice == 1:
        print("当前已有活动信息：", await limit_handle.get_active_msg())
        print("请选择你要进行的操作：\n1：添加活动\n2：删除活动(制作中)\n3：修改活动(制作中)\n")
        choice = None
        while choice not in [1, 2, 3]:
            choice = int(input())
        if choice == 1:
            active_id = int(input("请输入活动id："))
            active_name = input("请输入活动名称：")
            active_desc = input("请输入活动介绍：")
            active_deadline = int(input("请输入活动持续时间（天）："))
            last_time = now_time.replace(day=now_time.day + active_deadline)
            active_daily = input("活动是否日刷新奖励（y/n）：")
            active_daily = 0 if active_daily == 'n' else 1
            await limit_data.active_make(active_id, active_name, active_desc, str(last_time), active_daily)

            if await limit_data.get_active_by_id(active_id):
                print('创建活动成功！！！')
            else:
                print("创建活动失败！！")

        pass
    elif choice == 2:
        print("当前已有补偿信息：", await limit_handle.get_offset_list())
        print("请选择你要进行的操作：\n1：添加补偿\n2：删除补偿\n3：修改补偿(制作中)\n4：查询补偿详情信息\n")
        choice = None
        while choice not in [1, 2, 3, 4]:
            choice = int(input("请输入需要进行的操作id：\n"))
        if choice == 1:
            offset_id = int(input("请输入补偿id："))
            offset_name = input("请输入补偿名称：")
            offset_desc = input("请输入补偿介绍：")
            offset_deadline = int(input("请输入补偿持续时间（天）："))
            last_time = now_time + timedelta(days=offset_deadline)
            offset_daily = input("补偿是否日刷新奖励（y/n）：")
            offset_daily = 0 if offset_daily == 'n' else 1

            item_num = int(input("补偿物品种类数量："))
            offset_items = {}
            for n in range(item_num):
                need_item_id = int(input(f"请输入第{n + 1}个补偿物品id:"))
                need_item_num = int(input(f"请输入第{n + 1}个补偿物品数量:"))
                offset_items[need_item_id] = need_item_num
            await limit_data.offset_make(offset_id, offset_name, offset_desc, offset_items, str(last_time),
                                         offset_daily)

            if await limit_data.get_offset_by_id(offset_id):
                print('创建补偿成功！！！')
            else:
                print("创建补偿失败！！")

        elif choice == 2:
            offset_id = int(input("请输入要删除的补偿id："))
            await limit_data.offset_del(offset_id)
            if await limit_data.get_offset_by_id(offset_id):
                print('删除补偿失败！！！')
            else:
                print("删除补偿成功！！！")


        elif choice == 4:
            offset_id = int(input("请输入你想要查询的补偿id："))
            info = await limit_data.get_offset_by_id(offset_id)
            if info:
                print("查询到如下信息：\n" + await limit_handle.change_offset_info_to_msg(info))
            else:
                print("没有相关补偿信息！！")
        pass
    elif choice == 4:
        user_id = int(input("请输入模拟用户id："))
        print("当前用户限制词典：", await limit_data.get_limit_by_user_id(user_id))
        print("项目id总览(施工中略显寒酸)", await limit_handle.keymap)
        choice_type = None
        project_type = 0
        while choice_type is None:
            project_type = int(input("请输入要模拟的项目id：\n1-7观察总表\n"))
            choice_type = await limit_handle.keymap.get(project_type)
        if project_type < 6:
            project_value = int(input("请输入要模拟的项目值：\n"))
            project_mode = int(input("请输入要模拟的项目模式(0加1减)：\n"))
            await limit_handle.update_user_limit(user_id, project_type, project_value, project_mode)
        elif project_type < 7:
            print("当前已有补偿信息：", await limit_handle.get_offset_list())
            offset_id = int(input("请输入要模拟的补偿id："))
            is_pass = await limit_handle.update_user_offset(user_id, offset_id)
            if is_pass:
                print("领取补偿成功")
            else:
                print('领取补偿失败，请勿重复领取')
        print("模拟成功，当前用户限制词典：", await limit_data.get_limit_by_user_id(user_id))

        pass
    elif choice == 5:
        item_info = {'id': 700001, 'name': '二零二五新春福包', 'type': '道具', 'rank': 1000,
                     'desc': '2025新春活动获得，打开后随机获取以下物品中的三样：\r思恋结晶，随机buff增益丹药，复元水，悬赏衙令，金元宝，饺子\r获取数量概率如下：10%：10，20%：8，30%：6，40%：3',
                     'buff': 1, 'buff_type': 5, 'item_type': '道具'}
        all_user_id = await get_all_user_id_10()
        await send_all_user_item(all_user_id, item_info, 5, is_bind=True)
        print("前10补发5个")
        pass
    else:
        pass


async def run():
    limit_data.pool = await create_pool()
    print(f"xiuxian_limit数据库已连接!")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    while True:
        loop.run_until_complete(fast_handle())
        choice = input("执行结束，任意输入退出")
        if choice:
            break
        else:
            pass
