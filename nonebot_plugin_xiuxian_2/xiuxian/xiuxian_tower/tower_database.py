import pickle
from datetime import datetime
from pathlib import Path

import asyncpg
from asyncpg import Pool
from nonebot.log import logger

from .point_shop import shop_1, shop_2, point_give_1, point_give_2
from .. import DRIVER
from ..xiuxian_database.database_connect import database
from ..xiuxian_place import place
from ..xiuxian_utils.clean_utils import number_to_msg, zips
from ..xiuxian_utils.item_json import items

DATABASE = Path() / "data" / "xiuxian" / "players_database"
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_number = "123451234"
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


class Tower:
    def __init__(self, name, place_id, shop_data: dict, point_give):
        self.name = name
        self.place = place_id
        self.shop = shop_data
        self.point_give = point_give


class WorldTowerData:

    def __init__(self):
        fj_tower = Tower("灵虚古境", 3, shop_1, point_give_1)
        lj_tower = Tower("紫霄神渊", 19, shop_2, point_give_2)
        self.pool: Pool = None
        self.tower_data = {0: fj_tower, 1: lj_tower}
        self.sql_user_table_name = "user_tower_info"
        self.sql_tower_info_table_name = "world_tower"
        self.sql_col = ["user_id", "now_floor", "best_floor", "tower_point", "tower_place",
                        "weekly_point", "fight_log"]
        self.blob_data_list = ["fight_log"]

    async def check_data(self):
        """检查数据完整性"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(f"select count(1) from {self.sql_tower_info_table_name}")
            except asyncpg.exceptions.UndefinedTableError:
                await conn.execute(f"""CREATE TABLE "{self.sql_tower_info_table_name}" (
                    "floor" bigint NOT NULL,
                    "place_id" bigint DEFAULT 0,
                    "name" TEXT,
                    "hp" bigint DEFAULT 0,
                    "mp" bigint DEFAULT 0,
                    "atk" bigint DEFAULT 0,
                    "defence" bigint DEFAULT 0
                    );""")
            try:
                await conn.execute(f"select count(1) from {self.sql_user_table_name}")
            except asyncpg.exceptions.UndefinedTableError:
                await conn.execute(f"""CREATE TABLE "{self.sql_user_table_name}" (
                    "user_id" bigint NOT NULL,
                    "now_floor" bigint DEFAULT 0,
                    "best_floor" bigint DEFAULT 0,
                    "tower_point" bigint DEFAULT 0,
                    "tower_place" bigint DEFAULT 0,
                    "weekly_point" bigint DEFAULT 0,
                    "fight_log" bytea
                    );""")

    # 上面是数据库校验，别动

    async def get_tower_floor_info(self, floor, place_id) -> dict | None:
        """
        获取指定层数战斗塔信息
        :return:
        """
        sql = f"SELECT * FROM {self.sql_tower_info_table_name} WHERE floor=$1 and place_id=$2"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql, floor, place_id)
            return zips(**result[0]) if result else None

    async def tower_floor_make(
            self,
            floor: int,
            place_id: int,
            name: str,
            hp: int,
            mp: int,
            atk: int,
            defence: float,
            **kwargs):
        """
        插入塔楼层信息至数据库，数据处理不要放这里
        """
        # 检查物品是否存在，存在则update
        async with self.pool.acquire() as conn:
            item = self.get_tower_floor_info(floor, place_id)
            if item:
                # 判断是否存在，存在则update
                sql = (f"UPDATE {self.sql_tower_info_table_name} "
                       f"set name=$1, hp=$2, mp=$3, atk=$4, defence=$5 "
                       f"where floor=$6 and place_id=$7")
                await conn.execute(sql, name, hp, mp, atk, defence, floor, place_id)
                is_new = False
            else:
                # 判断是否存在，不存在则INSERT
                sql = (f"INSERT INTO {self.sql_tower_info_table_name} "
                       f"(floor, place_id, name, hp, mp, atk, defence) "
                       f"VALUES ($1,$2,$3,$4,$5,$6,$7)")
                await conn.execute(sql, floor, place_id, name, hp, mp, atk, defence)
                is_new = True
            return is_new

    async def get_user_tower_info(self, user_id):
        """
        获取指定用户的塔信息
        :param user_id: 用户id
        :return:
        """
        sql = f"select * from {self.sql_user_table_name} WHERE user_id=$1"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql, user_id)
            return zips(**result[0]) if result else None

    async def user_tower_info_make(
            self,
            user_id: int,
            now_floor: int,
            best_floor: int,
            tower_point: int,
            tower_place: int,
            weekly_point: int,
            fight_log: bytes,
            **kwargs):
        """

        :param user_id:
        :param now_floor:
        :param best_floor:
        :param tower_point:
        :param tower_place:
        :param weekly_point:
        :param fight_log:
        :return:
        """
        # 检查物品是否存在，存在则update
        async with self.pool.acquire() as conn:
            item = self.get_user_tower_info(user_id)
            if item:
                # 判断是否存在，存在则update
                sql = (
                    f"UPDATE {self.sql_user_table_name} set "
                    f"now_floor=$1, "
                    f"best_floor=$2, "
                    f"tower_point=$3,"
                    f"tower_place=$4, "
                    f"weekly_point=$5, "
                    f"fight_log=$6 where "
                    f"user_id=$7")
                await conn.execute(
                    sql,
                    now_floor,
                    best_floor,
                    tower_point,
                    tower_place,
                    weekly_point,
                    fight_log,
                    user_id)
                is_new = False
            else:
                # 判断是否存在，不存在则INSERT
                sql = f"""INSERT INTO {self.sql_user_table_name} (user_id, now_floor, best_floor, 
                tower_point, tower_place, weekly_point, fight_log) VALUES ($1,$2,$3,$4,$5,$6,$7)"""
                await conn.execute(
                    sql,
                    user_id,
                    now_floor,
                    best_floor,
                    tower_point,
                    tower_place,
                    weekly_point,
                    fight_log)
                is_new = True
            return is_new

    async def reset_point_get(self):
        async with self.pool.acquire() as conn:
            sql = (
                f"UPDATE {self.sql_user_table_name} set "
                f"weekly_point=0 where "
                f"user_id is not NULL")
            await conn.execute(sql)

    async def get_all_tower_user_id(self):
        """获取全部用户id"""
        sql = f"SELECT user_id FROM {self.sql_user_table_name}"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql)
            return [result_per[0] for result_per in result] if result else None

    async def update_user_tower_point(self, user_id, change_value, update_key: int = 0):
        """
        更新用户积分
        :param user_id:
        :param change_value:
        :param update_key: 更新类型 0增 1减
        :return:
        """
        change = '-' if update_key else '+'
        async with self.pool.acquire() as conn:
            sql = (
                f"UPDATE {self.sql_user_table_name} set "
                f"tower_point=tower_point{change}$1 where "
                f"user_id=$2")
            await conn.execute(
                sql,
                change_value,
                user_id)


class TowerHandle(WorldTowerData):
    def __init__(self):
        super().__init__()

    async def create_enemy(self):
        place_id = None
        floor = None
        name = None
        hp = None
        mp = None
        atk = None
        defence = None
        input_pass = False
        while not input_pass:
            try:
                place_id = int(input("请输入boss所在通天塔id（所在地图id）"))
                input_pass = True
            except ValueError:
                print("请输入正确的地图id数字")
        input_pass = False
        while not input_pass:
            try:
                floor = int(input("请输入boss所在楼层"))
                input_pass = True
            except ValueError:
                print("请输入正确的楼层数字")
        input_pass = False
        while not input_pass:
            try:
                name = str(input("请输入boss名称"))
                input_pass = True
            except ValueError:
                print("请输入正确的数值")
        input_pass = False
        while not input_pass:
            try:
                hp = int(input("请输入boss血量"))
                input_pass = True
            except ValueError:
                print("请输入正确的数值")
        input_pass = False
        while not input_pass:
            try:
                mp = int(input("请输入boss真元"))
                input_pass = True
            except ValueError:
                print("请输入正确的数值")
        input_pass = False
        while not input_pass:
            try:
                atk = int(input("请输入boss攻击力"))
                input_pass = True
            except ValueError:
                print("请输入正确的数值")
        input_pass = False
        while not input_pass:
            try:
                defence = int(input("请输入boss减伤率（%）"))
                input_pass = True
            except ValueError:
                print("请输入正确的数值")
        await self.tower_floor_make(floor, place_id, name, hp, mp, atk, defence)

    async def get_user_floor(self, user_info: dict):
        """
        获取用户目前通天塔楼层
        :param user_info: 获取的用户信息
        :return:
        """
        user_id = user_info.get('user_id')
        user_tower_info = await self.get_user_tower_info(user_id)
        if user_tower_info:
            floor = user_tower_info.get('now_floor')
            place_id = user_tower_info.get('tower_place')
            world_id = place.get_world_id(place_id)
            tower = self.tower_data.get(world_id)
        else:
            # 初始化
            floor = 0
            place_id = user_info.get('tower_place')
            world_id = place.get_world_id(place_id)
            tower = self.tower_data.get(world_id)
        return floor, tower

    async def get_user_tower_msg(self, user_info: dict):
        floor, tower = await self.get_user_floor(user_info)
        msg = (f"当前处于{tower.name}\r"
               f"第{floor}区域\r")
        next_floor = floor + 1
        enemy_info = await self.get_tower_floor_info(next_floor, tower.place)
        if not enemy_info:
            text = f"道友已抵达{tower.name}之底！！"
            return msg, text
        text = (f"下区域道友将会遭遇\r"
                f"【{enemy_info.get('name')}】\r"
                f"气血：{number_to_msg(enemy_info.get('hp'))}\r"
                f"真元：{number_to_msg(enemy_info.get('mp'))}\r"
                f"攻击：{number_to_msg(enemy_info.get('atk'))}\r"
                )
        return msg, text

    async def update_user_tower_info(self, user_tower_info: dict):
        for blob_data in self.blob_data_list:
            user_tower_info[blob_data] = pickle.dumps(user_tower_info[blob_data])
        await self.user_tower_info_make(**user_tower_info)

    async def check_user_tower_info(self, user_id):
        user_tower_info = await self.get_user_tower_info(user_id)
        if user_tower_info:
            # 若有则返回
            for blob_data in self.blob_data_list:
                user_tower_info[blob_data] = pickle.loads(user_tower_info[blob_data])
            return user_tower_info
        else:
            # 若无则初始化
            user_tower_info = {'user_id': user_id,
                               'now_floor': 0,
                               'best_floor': 0,
                               'tower_point': 0,
                               'tower_place': 0,
                               'weekly_point': 0,
                               'fight_log': []}
            return user_tower_info

    async def get_tower_shop_info(self, user_id):
        """
        获取通天塔商店
        :param user_id:
        :return: msg
        """
        user_tower_info = await self.get_user_tower_info(user_id)
        msg_list = []
        msg_head = ''
        if user_tower_info:
            place_id = user_tower_info.get('tower_place')
            point = user_tower_info.get('tower_point')
            world_id = place.get_world_id(place_id)
            tower = self.tower_data.get(world_id)
            msg_head = (f"【{tower.name}】积分兑换商店\r"
                        f"当前拥有积分：{point}")
            shop = tower.shop
            for goods_no, goods in shop.items():
                msg = (f"商品编号：{goods_no}\r"
                       f"物品名称：{items.items.get(str(goods.get('item'))).get('name')}\r"
                       f"兑换需要积分：{goods.get('price')}")
                msg_list.append(msg)
        return msg_list, msg_head


tower_handle = TowerHandle()


@DRIVER.on_startup
async def check_limit_db():
    tower_handle.pool = database.pool
    logger.opt(colors=True).info(f"<green>xiuxian_tower数据库已连接!</green>")
    logger.opt(colors=True).info(f"<green>检查xiuxian_tower数据库完整性中</green>")
    await tower_handle.check_data()
    logger.opt(colors=True).info(f"<green>检查xiuxian_tower数据库完整性成功</green>")
