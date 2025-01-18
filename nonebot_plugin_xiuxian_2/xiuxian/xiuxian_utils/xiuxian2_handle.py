import decimal
import operator

import asyncpg
from nonebot.adapters.onebot.v11 import Message

from .clean_utils import number_to, zips, get_strs_from_str
from .. import DRIVER
from ..xiuxian_data.data.境界_data import level_data
from ..xiuxian_data.data.灵根_data import root_data
from ..xiuxian_database.database_connect import database

try:
    import ujson as json
except ImportError:
    import json
import os
import random
from datetime import datetime
from pathlib import Path
from nonebot.log import logger
from ..xiuxian_config import XiuConfig, convert_rank
from .item_json import items
from .xn_xiuxian_impart_config import config_impart

WORKDATA = Path() / "data" / "xiuxian" / "work"
PLAYERSDATA = Path() / "data" / "xiuxian" / "players"
DATABASE = Path() / "data" / "xiuxian"
DATABASE_IMPARTBUFF = Path() / "data" / "xiuxian"
SKILLPATHH = DATABASE / "功法"
WEAPONPATH = DATABASE / "装备"
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_number = "123451234"
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


class XiuxianDateManage:

    def __init__(self):
        self.pool = None

    async def check_data(self):
        """检查数据完整性"""
        async with self.pool.acquire() as db:

            for i in XiuConfig().sql_table:
                if i == "user_xiuxian":
                    try:
                        await db.execute(f"select count(1) from {i}")
                    except asyncpg.exceptions.UndefinedTableError:
                        await db.execute("""CREATE TABLE "user_xiuxian" (
          "id" bigserial,
          "user_id" numeric NOT NULL,
          "sect_id" numeric DEFAULT NULL,
          "sect_position" numeric DEFAULT NULL,
          "stone" numeric DEFAULT 0,
          "root" TEXT,
          "root_type" TEXT,
          "level" TEXT,
          "power" numeric DEFAULT 0,
          "create_time" TEXT,
          "is_sign" numeric DEFAULT 0,
          "is_beg" numeric DEFAULT 0,
          "is_ban" numeric DEFAULT 0,
          "exp" numeric DEFAULT 0,
          "user_name" TEXT DEFAULT NULL,
          "level_up_cd" text,
          "level_up_rate" numeric DEFAULT 0
        );""")
                elif i == "user_cd":
                    try:
                        await db.execute(f"select count(1) from {i}")
                    except asyncpg.exceptions.UndefinedTableError:
                        await db.execute("""CREATE TABLE "user_cd" (
      "user_id" numeric NOT NULL,
      "type" numeric DEFAULT 0,
      "create_time" TEXT,
      "scheduled_time" TEXT,
      "last_check_info_time" TEXT,
      "user_active_info" json DEFAULT NULL
    );""")
                elif i == "sects":
                    try:
                        await db.execute(f"select count(1) from {i}")
                    except asyncpg.exceptions.UndefinedTableError:
                        await db.execute("""CREATE TABLE "sects" (
      "sect_id" bigserial,
      "sect_name" TEXT NOT NULL,
      "sect_owner" numeric,
      "sect_scale" numeric NOT NULL,
      "sect_used_stone" numeric,
      "sect_fairyland" numeric
      "is_open" boolean DEFAULT True
    );""")
                elif i == "back":
                    try:
                        await db.execute(f"select count(1) from {i}")
                    except asyncpg.exceptions.UndefinedTableError:
                        await db.execute("""CREATE TABLE "back" (
      "user_id" numeric NOT NULL,
      "goods_id" numeric NOT NULL,
      "goods_name" TEXT,
      "goods_type" TEXT,
      "goods_num" numeric,
      "create_time" TEXT,
      "update_time" TEXT,
      "remake" TEXT,
      "day_num" numeric DEFAULT 0,
      "all_num" numeric DEFAULT 0,
      "action_time" TEXT,
      "state" numeric DEFAULT 0
    );""")

                elif i == "buff_info":
                    try:
                        await db.execute(f"select count(1) from {i}")
                    except asyncpg.exceptions.UndefinedTableError:
                        await db.execute("""CREATE TABLE "buff_info" (
      "id" bigserial,
      "user_id" numeric NOT NULL,
      "main_buff" numeric DEFAULT 0,
      "sec_buff" numeric DEFAULT 0,
      "faqi_buff" numeric DEFAULT 0,
      "fabao_weapon" numeric DEFAULT 0,
      "sub_buff" numeric DEFAULT 0
    );""")
                elif i == "bank_info":
                    try:
                        await db.execute(f"select count(1) from {i}")
                    except asyncpg.exceptions.UndefinedTableError:
                        await db.execute("""CREATE TABLE "bank_info" (
      "user_id" numeric NOT NULL,
      "save_stone" numeric DEFAULT 0,
      "save_time" TEXT DEFAULT NULL,
      "bank_level" smallint DEFAULT 0
    );""")
                elif i == "mix_elixir_info":
                    try:
                        await db.execute(f"select count(1) from {i}")
                    except asyncpg.exceptions.UndefinedTableError:
                        await db.execute("""CREATE TABLE "mix_elixir_info" (
      "user_id" numeric NOT NULL,
      "farm_num" numeric DEFAULT 0,
      "farm_harvest_time" text DEFAULT NULL,
      "last_alchemy_furnace_data" json DEFAULT NULL
    );""")

            for i in XiuConfig().sql_user_xiuxian:
                try:
                    await db.execute(f"select {i} from user_xiuxian limit 1")
                except asyncpg.exceptions.UndefinedColumnError:
                    logger.opt(colors=True).info("<yellow>sql_user_xiuxian有字段不存在，开始创建\r</yellow>")
                    sql = f"ALTER TABLE user_xiuxian ADD COLUMN {i} numeric DEFAULT 0;"
                    logger.opt(colors=True).info(f"<green>{sql}</green>")
                    await db.execute(sql)

            for d in XiuConfig().sql_user_cd:
                try:
                    await db.execute(f"select {d} from user_cd limit 1")
                except asyncpg.exceptions.UndefinedColumnError:
                    logger.opt(colors=True).info("<yellow>sql_user_cd有字段不存在，开始创建</yellow>")
                    sql = f"ALTER TABLE user_cd ADD COLUMN {d} numeric DEFAULT 0;"
                    logger.opt(colors=True).info(f"<green>{sql}</green>")
                    await db.execute(sql)

            for s in XiuConfig().sql_sects:
                try:
                    await db.execute(f"select {s} from sects limit 1")
                except asyncpg.exceptions.UndefinedColumnError:
                    logger.opt(colors=True).info("<yellow>sql_sects有字段不存在，开始创建</yellow>")
                    sql = f"ALTER TABLE sects ADD COLUMN {s} numeric DEFAULT 0;"
                    logger.opt(colors=True).info(f"<green>{sql}</green>")
                    await db.execute(sql)

            for m in XiuConfig().sql_buff:
                try:
                    await db.execute(f"select {m} from buff_info limit 1")
                except asyncpg.exceptions.UndefinedColumnError:
                    logger.opt(colors=True).info("<yellow>sql_buff有字段不存在，开始创建</yellow>")
                    sql = f"ALTER TABLE buff_info ADD COLUMN {m} numeric DEFAULT 0;"
                    logger.opt(colors=True).info(f"<green>{sql}</green>")
                    await db.execute(sql)

            for b in XiuConfig().sql_back:
                try:
                    await db.execute(f"select {b} from back limit 1")
                except asyncpg.exceptions.UndefinedColumnError:
                    logger.opt(colors=True).info("<yellow>sql_back有字段不存在，开始创建</yellow>")
                    sql = f"ALTER TABLE back ADD COLUMN {b} numeric DEFAULT 0;"
                    logger.opt(colors=True).info(f"<green>{sql}</green>")
                    await db.execute(sql)

            # 检查并更新 last_check_info_time 列的记录
            await db.execute(f"""UPDATE user_cd
    SET last_check_info_time = $1
    WHERE last_check_info_time = '0' OR last_check_info_time IS NULL
            """, current_time)

    async def _create_user(self, user_id: int, root: str, root_type: str, power: str, create_time, user_name) -> None:
        """在数据库中创建用户并初始化"""
        async with self.pool.acquire() as db:
            sql = (
                f"INSERT INTO user_xiuxian (user_id,stone,root,root_type,level,power,create_time,user_name,exp,sect_id,"
                f"sect_position,user_stamina,place_id) VALUES ($1,0,$2,$3,'求道者',$4,$5,$6,100,NULL,NULL,$7,$8)")
            sql_cd = (f"INSERT INTO user_cd (user_id,type,create_time,scheduled_time,last_check_info_time"
                      f") VALUES ($1,$2,$3,$4,$5)")

            await db.execute(sql, user_id, root, root_type, power, create_time, user_name, XiuConfig().max_stamina, 1)
            await db.execute(sql_cd, user_id, 0, None, None, None)

    async def get_user_info_with_id(self, user_id):
        """根据USER_ID获取用户信息,不获取功法加成"""
        async with self.pool.acquire() as db:
            sql = f"select * from user_xiuxian WHERE user_id=$1"
            result = await db.fetch(sql, user_id)
            return zips(**result[0]) if result else None

    async def get_user_info_with_name(self, user_id):
        """根据user_name获取用户信息"""
        async with self.pool.acquire() as db:
            sql = f"select * from user_xiuxian WHERE user_name=$1"
            result = await db.fetch(sql, user_id)
            return zips(**result[0]) if result else None

    async def update_all_users_stamina(self, max_stamina, stamina):
        """体力未满用户更新体力值"""
        async with self.pool.acquire() as db:
            sql = f"""
                UPDATE user_xiuxian
                SET user_stamina = LEAST(user_stamina + $1, $2)
                WHERE user_stamina < $3
            """
            await db.execute(sql, stamina, max_stamina, max_stamina)

    async def update_user_stamina(self, user_id, stamina_change, key):
        """更新用户体力值 1为增加，2为减少"""
        async with self.pool.acquire() as db:

            if key == 1:
                sql = f"UPDATE user_xiuxian SET user_stamina=user_stamina+$1 WHERE user_id=$2"
                await db.execute(sql, stamina_change, user_id)

            elif key == 2:
                sql = f"UPDATE user_xiuxian SET user_stamina=user_stamina-$1 WHERE user_id=$2"
                await db.execute(sql, stamina_change, user_id)

    async def get_user_real_info(self, user_id):
        """
        根据USER_ID获取用户信息,获取功法加成
        战斗面板
        """
        async with self.pool.acquire() as db:
            sql = f"select * from user_xiuxian WHERE user_id=$1"
            result = await db.fetch(sql, user_id)
            return await final_user_data(**result[0]) if result else None

    async def get_sect_info(self, sect_id):
        """
        通过宗门编号获取宗门信息
        :param sect_id: 宗门编号
        :return:
        """
        async with self.pool.acquire() as db:
            sql = f"select * from sects WHERE sect_id=$1"
            result = await db.fetch(sql, sect_id)
            return zips(**result[0]) if result else None

    async def get_sect_owners(self):
        """获取所有宗主的 user_id"""
        async with self.pool.acquire() as db:
            sql = f"SELECT user_id FROM user_xiuxian WHERE sect_position = 0"
            result = await db.fetch(sql)
            return zips(**result[0]) if result else None

    async def get_elders(self):
        """获取所有长老的 user_id"""
        async with self.pool.acquire() as db:
            sql = f"SELECT user_id FROM user_xiuxian WHERE sect_position = 1"
            result = await db.fetch(sql)
            return zips(**result[0]) if result else None

    async def create_user(self, user_id, *args):
        """校验用户是否存在"""
        async with self.pool.acquire() as db:
            sql = f"select * from user_xiuxian WHERE user_id=$1"
            result = await db.fetch(sql, user_id)
            place_name = "缘起小镇"
            if not result:
                await self._create_user(user_id, args[0], args[1], args[2], args[3],
                                        args[4])  # root, type, power, create_time, user_name

                welcome_msg = f"必死之境机逢仙缘，修仙之路波澜壮阔！\r恭喜{args[4]}踏入仙途，你的灵根为：{args[0]},类型是：{args[1]},你的战力为：{args[2]}\r当前境界：求道者，所处位置：{place_name}"
                return True, welcome_msg
            else:
                return False, f"您已迈入修仙世界，输入【我的修仙信息】获取数据吧！"

    async def get_sign(self, user_id):
        """获取用户签到信息"""
        async with self.pool.acquire() as db:
            sql = "select is_sign from user_xiuxian WHERE user_id=$1"
            result = await db.fetch(sql, user_id)
            if not result:
                return f"修仙界没有你的足迹，输入【踏入仙途】加入修仙世界吧！"
            elif not result[0][0]:
                ls = random.randint(XiuConfig().sign_in_lingshi_lower_limit,
                                    XiuConfig().sign_in_lingshi_upper_limit)
                sql2 = f"UPDATE user_xiuxian SET is_sign=1,stone=stone+$1 WHERE user_id=$2"
                await db.execute(sql2, ls, user_id)
                return f"签到成功，获取{number_to(ls)}|{ls}块灵石!"
            elif result[0][0] == 1:
                return f"贪心的人是不会有好运的！"

    async def get_beg(self, user_id):
        """获取仙途奇缘信息"""
        async with self.pool.acquire() as db:
            sql = f"select is_beg from user_xiuxian WHERE user_id=$1"
            result = await db.fetch(sql, user_id)
            if not result:
                return f"修仙界没有你的足迹，输入【踏入仙途】加入修仙世界吧！"
            if result[0][0] == 0:
                ls = random.randint(XiuConfig().beg_lingshi_lower_limit, XiuConfig().beg_lingshi_upper_limit)
                sql2 = f"UPDATE user_xiuxian SET is_beg=1,stone=stone+$1 WHERE user_id=$2"
                await db.execute(sql2, ls, user_id)

                return ls
            elif result[0][0] == 1:
                return None

    async def ramaker(self, lg, root_type, user_id):
        """洗灵根"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE user_xiuxian SET root=$1,root_type=$2,stone=stone-$3 WHERE user_id=$4"
            await db.execute(sql, lg, root_type, XiuConfig().remake, user_id)
            await self.update_power2(user_id)  # 更新战力
            return f"逆天之行，重获新生，新的灵根为：{lg}，类型为：{root_type}"

    @staticmethod
    async def get_root_rate(name):
        """获取灵根倍率"""
        data = root_data
        return data[name]['type_speeds']

    @staticmethod
    async def get_level_power(name):
        """获取境界倍率|exp"""
        data = level_data
        return data[name]['power']

    async def update_power2(self, user_id) -> None:
        """更新战力"""
        user_info = await self.get_user_info_with_id(user_id)
        async with self.pool.acquire() as db:
            level = level_data
            root = root_data
            sql = f"UPDATE user_xiuxian SET power=round(exp*$1*$2,0) WHERE user_id=$3"
            await db.execute(sql, root[user_info['root_type']]["type_speeds"],
                             level[user_info['level']]["spend"], user_id)

    async def update_ls(self, user_id, price, key):
        """更新灵石  1为增加，2为减少"""
        async with self.pool.acquire() as db:

            if key == 1:
                sql = f"UPDATE user_xiuxian SET stone=stone+$1 WHERE user_id=$2"
                await db.execute(sql, price, user_id)

            elif key == 2:
                sql = f"UPDATE user_xiuxian SET stone=stone-$1 WHERE user_id=$2"
                await db.execute(sql, price, user_id)

    async def update_root(self, user_id, key):
        """更新灵根  1为混沌,2为融合,3为超,4为龙,5为天,6为千世,7为万世"""
        async with self.pool.acquire() as db:
            root_name = None
            sql = f"UPDATE user_xiuxian SET root=$1,root_type=$2 WHERE user_id=$3"
            if int(key) == 1:
                await db.execute(sql, "全属性灵根", "混沌灵根", user_id)
                root_name = "混沌灵根"


            elif int(key) == 2:
                await db.execute(sql, "融合万物灵根", "融合灵根", user_id)
                root_name = "融合灵根"


            elif int(key) == 3:
                await db.execute(sql, "月灵根", "超灵根", user_id)
                root_name = "超灵根"


            elif int(key) == 4:
                await db.execute(sql, "言灵灵根", "龙灵根", user_id)
                root_name = "龙灵根"


            elif int(key) == 5:
                await db.execute(sql, "金灵根", "天灵根", user_id)
                root_name = "天灵根"


            elif int(key) == 6:
                await db.execute(sql, "一朝轮回散天人，凝练红尘化道根", "轮回灵根", user_id)
                root_name = "轮回灵根"


            elif int(key) == 7:
                await db.execute(sql, "求道散尽半仙躯，堪能窥得源宇秘", "源宇道根", user_id)
                root_name = "源宇道根"


            elif int(key) == 8:
                await db.execute(sql, "帝蕴浸灭求一道，触及本源登顶峰", "道之本源", user_id)
                root_name = "道之本源"

            return root_name  # 返回灵根名称

    async def update_ls_all(self, price):
        """所有用户增加灵石"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE user_xiuxian SET stone=stone+$1"
            await db.execute(sql, price)

    async def get_exp_rank(self, user_id):
        """修为排行"""
        sql = f"select rank from(select user_id,exp,dense_rank() over (ORDER BY exp desc) as rank FROM user_xiuxian) WHERE user_id=$1"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, user_id)
            result_all = [result_per[0] for result_per in result]
            return result_all

    async def get_stone_rank(self, user_id):
        """灵石排行"""
        sql = f"select rank from(select user_id,stone,dense_rank() over (ORDER BY stone desc) as rank FROM user_xiuxian) WHERE user_id=$1"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, user_id)
            result_all = [result_per[0] for result_per in result]
            return result_all

    async def get_ls_rank(self):
        """灵石排行榜"""
        sql = f"SELECT user_id,stone FROM user_xiuxian WHERE stone>0 ORDER BY stone DESC LIMIT 5"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def get_nearby_player(self, place_id: int, exp: int):
        """附近玩家，优先获取实力相近的"""
        sql = f"SELECT user_name,level FROM user_xiuxian WHERE place_id=$1 and exp<$2 ORDER BY exp DESC LIMIT 10"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, place_id, exp)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def sign_remake(self):
        """重置签到"""
        sql = f"UPDATE user_xiuxian SET is_sign=0"
        async with self.pool.acquire() as db:
            await db.execute(sql)

    async def beg_remake(self):
        """重置仙途奇缘"""
        sql = f"UPDATE user_xiuxian SET is_beg=0"
        async with self.pool.acquire() as db:
            await db.execute(sql)

    async def ban_user(self, user_id):
        """小黑屋"""
        sql = f"UPDATE user_xiuxian SET is_ban=1 WHERE user_id=$1"
        async with self.pool.acquire() as db:
            await db.execute(sql, user_id)

    async def update_user_name(self, user_id, user_name):
        """更新用户道号"""
        async with self.pool.acquire() as db:
            get_name = f"select user_name from user_xiuxian WHERE user_name=$1"
            result = await db.fetch(get_name, user_name)
            if result:
                return "已存在该道号！"
            else:
                sql = f"UPDATE user_xiuxian SET user_name=$1 WHERE user_id=$2"

                await db.execute(sql, user_name, user_id)
                return '道友的道号更新成功拉~'

    async def updata_level_cd(self, user_id):
        """更新破镜CD"""
        sql = f"UPDATE user_xiuxian SET level_up_cd=$1 WHERE user_id=$2"
        async with self.pool.acquire() as db:
            now_time = datetime.now()
            now_time = str(now_time)
            await db.execute(sql, now_time, user_id)

    async def update_last_check_info_time(self, user_id):
        """更新查看修仙信息时间"""
        sql = "UPDATE user_cd SET last_check_info_time = $1 WHERE user_id = $2"
        async with self.pool.acquire() as db:
            now_time = datetime.now()
            now_time = str(now_time)
            await db.execute(sql, now_time, user_id)

    async def get_last_check_info_time(self, user_id):
        """获取最后一次查看修仙信息时间"""
        async with self.pool.acquire() as db:
            sql = "SELECT last_check_info_time FROM user_cd WHERE user_id = $1"
            result = await db.fetch(sql, user_id)
            if result:
                return datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f')
            else:
                return None

    async def updata_level(self, user_id, level_name):
        """更新境界"""
        sql = f"UPDATE user_xiuxian SET level=$1 WHERE user_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, level_name, user_id)

    async def get_user_id(self, user_nike_name):
        """
        通过道号获取用户id,替代at
        :param user_nike_name: 用户道号
        :return: 用户id
        """
        if isinstance(user_nike_name, Message):
            user_nike_name = user_nike_name.extract_plain_text()

        user_nike_name = get_strs_from_str(user_nike_name)
        if user_nike_name:
            user_nike_name = user_nike_name[0]
        else:
            return None
        async with self.pool.acquire() as db:
            sql = "SELECT user_id FROM user_xiuxian WHERE user_name =$1"
            result = await db.fetch(sql, user_nike_name)
            if not result:
                return None
            return result[0][0]

    async def get_user_cd(self, user_id):
        """
        获取用户操作CD
        :param user_id: QQ
        :return: 用户CD信息的字典
        """
        sql = f"SELECT * FROM user_cd  WHERE user_id=$1"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, user_id)
            if result:
                user_cd_dict = zips(**result[0])
                return user_cd_dict
            else:
                await self.insert_user_cd(user_id)
                return None

    async def insert_user_cd(self, user_id) -> None:
        """
        添加用户至CD表
        :param user_id: qq
        :return:
        """
        sql = f"INSERT INTO user_cd (user_id) VALUES ($1)"
        async with self.pool.acquire() as db:
            await db.execute(sql, user_id)

    async def create_sect(self, user_id, sect_name) -> None:
        """
        创建宗门
        :param user_id:qq
        :param sect_name:宗门名称
        :return:
        """
        sql = f"INSERT INTO sects(sect_name, sect_owner, sect_scale, sect_used_stone) VALUES ($1,$2,0,0)"
        async with self.pool.acquire() as db:
            await db.execute(sql, sect_name, user_id)

    async def update_sect_name(self, sect_id, sect_name) -> bool:
        """
        修改宗门名称
        :param sect_id: 宗门id
        :param sect_name: 宗门名称
        :return: 返回是否更新成功的标志，True表示更新成功，False表示更新失败（已存在同名宗门）
        """
        async with self.pool.acquire() as db:
            get_sect_name = f"select sect_name from sects WHERE sect_name=$1"
            result = await db.fetch(get_sect_name, sect_name)
            if result:
                return False
            else:
                sql = f"UPDATE sects SET sect_name=$1 WHERE sect_id=$2"
                await db.execute(sql, sect_name, sect_id)
                return True

    async def get_sect_info_by_qq(self, user_id):
        """
        通过用户qq获取宗门信息
        :param user_id:
        :return:
        """
        async with self.pool.acquire() as db:
            sql = f"select * from sects WHERE sect_owner=$1"
            result = await db.fetch(sql, user_id)
            return zips(**result[0]) if result else None

    async def get_sect_info_by_id(self, sect_id):
        """
        通过宗门id获取宗门信息
        :param sect_id:
        :return:
        """
        async with self.pool.acquire() as db:
            sql = f"select * from sects WHERE sect_id=$1"
            result = await db.fetch(sql, sect_id)
            return zips(**result[0]) if result else None

    async def update_usr_sect(self, user_id, usr_sect_id, usr_sect_position):
        """
        更新用户信息表的宗门信息字段
        :param user_id:
        :param usr_sect_id:
        :param usr_sect_position:
        :return:
        """
        sql = f"UPDATE user_xiuxian SET sect_id=$1,sect_position=$2 WHERE user_id=$3"
        async with self.pool.acquire() as db:
            await db.execute(sql, usr_sect_id, usr_sect_position, user_id)

    async def update_sect_owner(self, user_id, sect_id):
        """
        更新宗门所有者
        :param user_id:
        :param sect_id:
        :return:
        """
        sql = f"UPDATE sects SET sect_owner=$1 WHERE sect_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, user_id, sect_id)

    async def get_highest_contrib_user_except_current(self, sect_id, current_owner_id):
        """
        获取指定宗门的贡献最高的人，排除当前宗主
        :param sect_id: 宗门ID
        :param current_owner_id: 当前宗主的ID
        :return: 贡献最高的人的ID，如果没有则返回None
        """
        async with self.pool.acquire() as db:
            sql = """
            SELECT user_id
            FROM user_xiuxian
            WHERE sect_id = $1 AND sect_position = 1 AND user_id != $2
            ORDER BY sect_contribution DESC
            LIMIT 1
            """
            result = await db.fetch(sql, sect_id, current_owner_id)
            if result:
                return result[0][0]
            else:
                return None

    async def get_all_sect_id(self):
        """获取全部宗门id"""
        sql = "SELECT sect_id FROM sects"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql)
            if result:
                return [result_per[0] for result_per in result]
            else:
                return None

    async def get_all_user_id(self):
        """获取全部用户id"""
        sql = "SELECT user_id FROM user_xiuxian"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql)
            if result:
                return [row[0] for row in result]
            else:
                return None

    async def in_closing(self, user_id, the_type):
        """
        更新用户状态
        :param user_id: qq
        :param the_type: 0:无状态  1:闭关中  2:历练中  3:闭关中  4:修炼中  -1:赶路中
        :return:
        """
        now_time = None
        if the_type == 1:
            now_time = datetime.now()
        elif the_type == 0:
            now_time = 0
        elif the_type == 2:
            now_time = datetime.now()
        elif the_type == 5:
            now_time = datetime.now()
        elif the_type == -1:
            now_time = datetime.now()
        now_time = str(now_time)
        sql = "UPDATE user_cd SET type=$1,create_time=$2 WHERE user_id=$3"
        async with self.pool.acquire() as db:
            await db.execute(sql, the_type, now_time, user_id)

    async def update_exp(self, user_id, exp):
        """增加修为"""
        sql = "UPDATE user_xiuxian SET exp=exp+$1 WHERE user_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, exp, user_id)

    async def update_j_exp(self, user_id, exp):
        """减少修为"""
        sql = "UPDATE user_xiuxian SET exp=exp-$1 WHERE user_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, exp, user_id)

    async def del_exp_decimal(self, user_id, exp):
        """去浮点"""
        sql = "UPDATE user_xiuxian SET exp=$1 WHERE user_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, exp, user_id)

    async def realm_top(self, world_id):
        """境界排行榜前50"""
        place_max = world_id * 12 + 13
        place_min = world_id * 12
        rank_mapping = {rank: idx for idx, rank in enumerate(convert_rank('求道者')[1])}

        sql = f"""SELECT user_name, level, exp FROM user_xiuxian 
            WHERE user_name IS NOT NULL and place_id > {place_min} and place_id < {place_max}
            ORDER BY exp DESC, (CASE level """

        for level, value in sorted(rank_mapping.items(), key=lambda x: x[1], reverse=True):
            sql += f"WHEN '{level}' THEN '{value:02}' "

        sql += """ELSE level END) ASC LIMIT 60"""

        async with self.pool.acquire() as db:
            result = await db.fetch(sql)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def random_name(self):
        """
        生成一个随机名字，不会与数据库内名字重复(递归实现)
        :return: type = str
        """
        name_x1 = "万俟 司马 上官 欧阳 夏侯 诸葛 闻人 东方 赫连 皇甫 尉迟 公羊 澹台 公冶 宗政 濮阳 淳于 单于 太叔 申屠 公孙 仲孙 轩辕 令狐 徐离 宇文 长孙 慕容 司徒 司空".split()
        name_x2 = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍虞万支柯昝管卢莫经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭历戎祖武符刘景詹束龙叶幸司韶郜黎蓟溥印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阳郁胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍郤璩桑桂濮牛寿通边扈燕冀姓浦尚农温别庄晏柴瞿阎充慕连茹宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逮盍益桓公"
        num = random.randint(1, 2)
        if num == 1:
            name_x = random.choice(name_x2)
        else:
            name_x = random.choice(name_x1)
        first_m = '伟刚勇毅俊峰强军平保东文辉力明永健世广志义兴良海山仁波宁贵福生龙元全国胜学祥才发武新利清洛冰奕启钧心辛皓皓煜鹭洋叶轩南弦振博御嘉无洛睿磊琦宁鸿皓盛冰翊颢丘黎皓阳景禹钧枫亦骏莫羡玉堂轩学浩灿远尘商阳谦峻千城星逸元鸣皓丁知许望峻中震杰英皓源瀚文澈幕星舒远野哲辰乐新冷睿升寒子洛安锦枫朗浩川皓讯天霖墨离奚鸣曜伟栋家鸿煊寒靖弘泽开霁云霆皓彭昊皓煜明轩天倾川黎川克启源健景鸿溪枫麟坚岳古华风修亮夜羽轶锦修远源捷悦翔辉轩皓伯志泽朗勋明笛青玄言风皓旸遥清天宇寂云墨萧少宣逍枫和星言润翰墨皓博硕泽问枫墨尘'
        two_m = '飞彬富顺信子杰涛昌成康星光天达安岩中茂进林有坚和彪博诚先敬震振壮会思群豪心邦承乐绍功松善嘉无洛睿磊琦宁鸿皓盛冰翊颢丘黎皓阳景禹钧枫亦骏莫羡玉堂轩学浩灿远尘商阳谦峻千城星逸元鸣皓丁知许望峻中震杰英皓源瀚文澈幕星舒远野哲辰乐新冷睿升寒子洛安锦枫朗浩川皓讯天霖墨离奚鸣曜伟栋家鸿煊寒靖弘泽开霁云霆皓彭昊皓煜明轩天倾川黎川克启源健景鸿溪枫麟坚岳古华风修亮夜羽轶锦修远源捷悦翔辉轩皓伯志泽朗勋明笛青玄言风皓旸遥清天宇寂云墨萧少宣逍枫和星言润翰墨皓博硕泽问枫墨尘'
        first_f = "依文婉靓芷依烁娅婧一瑾如娴一恩屿漫淑雨静以一沐柔以紫思采芷思辰沛珺姝婉乐瑶予雨倩知一恩琦夏景婉岚苓予清素韩思妤煊梓可思一一莹祺静灵槿屿允汐斯莘晓郡舒童静子尹漫若婉栀晴淑芸以妮梓禹可霜梦若承梦昕萱思芸宜研歆宛琬玥情辛婧妤柳艺一炘筱珊韵俏紫瑾巧思曼诗云瑶梦妍仪馨婧泓静亦允亦夏夏晓怡珂妙梦唯艺炜静姿思依玺唯子夏侨谨曼卉诗亦悦燕洛芮柳茹夏清玲一若萱骐黛筱彦芷菁洛若晓瑾昭梦芷羽沐萱蝶恩诺慕萱菀茹浠羽诗素曼沐雯可果梦舒莹傲素茜洛仙娅歆恩韵子亦未若琬希茵巧莹桉雅馨觅乐彦晨慈若恩媛怡燕素蕊伊雅攸晓歆雪晓怡玥雨妙依柔雯茗若夏芊玲知漪玲暄筱莫宸君姝雨竹笑筱俏玲颖如颜梓芷曼悦乐欢韵芸珊沁敏仪菲漫琪依瑶童倬艺倪皙筠可芮紫芸馨灵汐燕以菀紫婉茜诗小倚罗婷乔倩欣薇伊瑾竹祺莹依婉淇雯伊一韵雪欣寻颐茵灵筱沐澜郡芯子知恩梓婧攸灵芸晓予允叶芷沫宛熙俞黛予芝宛斐敏婧曼子珊宸玥雅睿嫣宸蝶萌子昕灵颖伶若苡漫亦玥晓笑悦子知馨亦雯凌筠艾诗珞舜微宸思采亦蓝欣希怡筱珊筠钰淳熙宛柠恩菲君霄槿惜菱小予筱恩清晨若柠芸弄可婷诗俐含梦珊灵昕昊熙惟君颐茹锦润宇柔子茗子巧怡胤甜书溪子梦筱清可伊思千钰晨姿茹嘉妍乔依桐筱洛语夕雨于楚静雨枝嘉亦栎茗筱依小月嘉语紫琬素欣星沛瑾沐淑梦艺甜梦汐俪茵采忱怡曼渝蒽洺婧娜梦宛漫灿诗曼梦忆妙诗琬妮涵熙玲"
        two_f = "尘茵菲苒茉沐菲若宸可冉宁君依琪柠欣如珊冉静萱琪蔓榕菲茹奕静宁怡瑶沅予忆缇玲晨茵榆婉薇甜蕊奕薇伶可芮蒙苒娅菲柔玄琪歆蕊允若宁若玥瑄枝媛夏知妤晨妤予珞夏恩艺姮姝莹漫灵夏雅菱彤璇菲希珊一晴一娜妤樱娜姗亚檬薇斐祺禾瑜岑情萌韩淇彤漫泺彤静若灵彤蒨娴妍墨姝嫣雅舒希姿宁宁淇玲岚唯彤玲霏樱音蔓郡茵蝶宜芮采怡婷憶诺霖清娜予汐夏琦依莹淑函菲莹桐樱仪怡冉静菲冉梦瑛柔冉彤兮恩芊希雁柔仪晓瑶柒子曼怡婷妃昕沁婷伊媛歌乐甜卿欣研菲睿妤尹玥珊瑶柔雯雅莹佟莹倩芃恬希夕如言彤韵儿祺忻予禾怡珺甜芯琼玥欣禾灵邑珊然婕宁韵淇姗柳悦歆昕雪朵嫣娜仪汶可尹霜羽墨蓓钰夕熙妃梦萱菲君冉淇妤钰瑶静晴汐倩汐熙依娱霖禾菲沁桐桐语玥曼霏虹羽怡淑莎茉灵佩栖冉睿儿娅雨柳霏茹婷桐柠晗灵梦依燕茵喆妍妍柔桦苒敏涵馨柔桐萱璇墨妮颜柔芹妃可汐敏冉夕瑶妍珊遥晗棠文然茹微菲熙采薇旋彤盈彤茜娇依妤茹怡君竹漫晴卉淑苒薇蕊琼暄柳寒溦恩圻婵娜娇墨如沫妍宜莹君晚欣曼梦欣允妤萌晴灵依涵嫣尧霏舒薇伶婷瑶嫣仪婷婷宁倩燕芯谊絮情音熙晨娜微萌若歆禾莹若墨依影芃娜柔萱韵斐君梦遥薇媛瑾娅晴慈妤漫姝淑媛涵娅昕蕊彤薇静雯淑姝柯瑜亦珞媛千依熙菲艺瑾霏之冉静茴姝橦瑶沫炘茵妤瑄柔苒禾桐冉芸墨汝淑艺晨姝云珺缘苒晗茹微玮情蒙静琪染彤沛潼漫若辰静绣萱熙娜夕妗汐雯睿如仙姿语思宜玥钰微珑"
        sex = random.randint(1, 2)
        if random.randint(1, 6) == 1:

            temp = name_x + random.choice(first_m if sex == 1 else first_f)
        else:
            temp = name_x + random.choice(first_m if sex == 1 else first_f) + random.choice(
                two_m if sex == 1 else two_f)
        return await self.no_same_name(temp)

    async def no_same_name(self, name):
        sql = f"SELECT * FROM user_xiuxian WHERE user_name is NOT NULL"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql)
            result_all = [result_per[0] for result_per in result]
            if name not in result_all:
                return name
            else:
                name += "_"
                return await self.no_same_name(name)

    async def stone_top(self, world_id):
        """这也是灵石排行榜"""
        place_max = world_id * 12 + 13
        place_min = world_id * 12
        sql = (f"SELECT user_name,level,stone FROM user_xiuxian WHERE user_name is NOT NULL "
               f"and place_id > {place_min} and place_id < {place_max} ORDER BY stone DESC LIMIT 60")
        async with self.pool.acquire() as db:
            result = await db.fetch(sql)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def power_top(self, world_id):
        """战力排行榜"""
        place_max = world_id * 12 + 13
        place_min = world_id * 12
        sql = (f"SELECT user_name,level,power FROM user_xiuxian WHERE user_name is NOT NULL "
               f"and place_id > {place_min} and place_id < {place_max} ORDER BY power DESC LIMIT 60")
        async with self.pool.acquire() as db:
            result = await db.fetch(sql)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def scale_top(self):
        """
        宗门建设度排行榜
        :return:
        """
        sql = f"SELECT sect_id, sect_name, sect_scale FROM sects WHERE sect_owner is NOT NULL ORDER BY sect_scale DESC"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def scale_elixir_top(self):
        """
        宗门建设度排行榜
        :return:
        """
        sql = (f"SELECT sect_id, sect_name, elixir_room_level, sect_scale "
               f"FROM sects WHERE sect_owner is NOT NULL "
               f"ORDER BY elixir_room_level DESC, sect_scale DESC "
               f"LIMIT 60")
        async with self.pool.acquire() as db:
            result = await db.fetch(sql)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def get_all_sects(self):
        """
        获取所有宗门信息
        :return: 宗门信息字典列表
        """
        sql = f"SELECT * FROM sects WHERE sect_owner is NOT NULL"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def get_all_sects_with_member_count(self):
        """
        获取所有宗门及其各个宗门成员数
        """
        async with self.pool.acquire() as db:
            result = await db.fetch("""
                SELECT sects.sect_id, sects.sect_name, sects.sect_scale,
                (SELECT user_name FROM user_xiuxian WHERE user_xiuxian.user_id = sects.sect_owner) as user_name,
                (SELECT COUNT(user_name) FROM user_xiuxian WHERE sects.sect_id = user_xiuxian.sect_id) as member_count
                FROM sects
                LEFT JOIN user_xiuxian ON sects.sect_id = user_xiuxian.sect_id
            """)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def update_user_is_beg(self, user_id, is_beg):
        """
        更新用户的最后奇缘时间

        :param user_id: 用户ID
        :param is_beg: 'YYYY-MM-DD HH:MM:SS'
        """
        async with self.pool.acquire() as db:
            sql = "UPDATE user_xiuxian SET is_beg=$1 WHERE user_id=$2"
            await db.execute(sql, is_beg, user_id)

    async def get_top1_user(self):
        """
        获取修为第一的用户
        """
        async with self.pool.acquire() as db:
            sql = f"select * from user_xiuxian ORDER BY exp DESC LIMIT 1"
            result = await db.fetch(sql)
            return zips(**result[0]) if result else None

    async def donate_update(self, sect_id, stone_num):
        """宗门捐献更新建设度及可用灵石"""
        sql = f"UPDATE sects SET sect_used_stone=sect_used_stone+$1,sect_scale=sect_scale+$2 WHERE sect_id=$3"
        async with self.pool.acquire() as db:
            await db.execute(sql, stone_num, stone_num * 1, sect_id)

    async def update_sect_used_stone(self, sect_id, sect_used_stone, key):
        """更新宗门灵石储备  1为增加,2为减少"""
        async with self.pool.acquire() as db:

            if key == 1:
                sql = f"UPDATE sects SET sect_used_stone=sect_used_stone+$1 WHERE sect_id=$2"
                await db.execute(sql, sect_used_stone, sect_id)

            elif key == 2:
                sql = f"UPDATE sects SET sect_used_stone=sect_used_stone-$1 WHERE sect_id=$2"
                await db.execute(sql, sect_used_stone, sect_id)

    async def update_sect_materials(self, sect_id, sect_materials, key):
        """更新资材  1为增加,2为减少"""
        async with self.pool.acquire() as db:

            if key == 1:
                sql = f"UPDATE sects SET sect_materials=sect_materials+$1 WHERE sect_id=$2"
                await db.execute(sql, sect_materials, sect_id)

            elif key == 2:
                sql = f"UPDATE sects SET sect_materials=sect_materials-$1 WHERE sect_id=$2"
                await db.execute(sql, sect_materials, sect_id)

    async def daily_update_sect_materials(self, sect_id: list):
        """更新资材  1为增加,2为减少"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE sects SET sect_materials=sect_materials+sect_scale WHERE sect_id=$1"
            await db.executemany(sql, sect_id)

    async def get_all_sects_id_scale(self):
        """
        获取所有宗门信息
        :return
        :result[0] = sect_id   
        :result[1] = 建设度 sect_scale,
        :result[2] = 丹房等级 elixir_room_level 
        """
        sql = f"SELECT sect_id, sect_scale, elixir_room_level FROM sects WHERE sect_owner is NOT NULL ORDER BY sect_scale DESC"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def get_all_users_by_sect_id(self, sect_id):
        """
        获取宗门所有成员信息
        :return: 成员列表
        """
        sql = f"SELECT * FROM user_xiuxian WHERE sect_id = $1"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, sect_id)
            result_all = [zips(**result_per) for result_per in result]
            results = sorted(result_all, key=operator.itemgetter('sect_contribution'), reverse=True)
            return results

    async def do_work(self, user_id, the_type, sc_time: str = None):
        """
        更新用户操作CD
        :param sc_time: 任务耗时
        :param user_id: 用户对机器人虚拟值
        :param the_type: 0:无状态  1:闭关中  2:历练中  3:探索秘境中  4:修炼中
        :return:
        """
        now_time = None
        if the_type == 1:
            now_time = datetime.now()
        elif the_type == 0:
            now_time = 0
        elif the_type == 2:
            now_time = datetime.now()
        elif the_type == 3:
            now_time = datetime.now()
        elif the_type == -1:
            now_time = datetime.now()
        now_time = str(now_time)
        sql = f"UPDATE user_cd SET type=$1,create_time=$2,scheduled_time=$3 WHERE user_id=$4"
        async with self.pool.acquire() as db:
            await db.execute(sql, the_type, now_time, str(sc_time), user_id)

    async def update_levelrate(self, user_id, rate):
        """更新突破成功率"""
        sql = f"UPDATE user_xiuxian SET level_up_rate=$1 WHERE user_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, rate, user_id)

    async def update_user_attribute(self, user_id, hp, mp, atk):
        """更新用户HP,MP,ATK信息"""
        sql = f"UPDATE user_xiuxian SET hp=$1,mp=$2,atk=$3 WHERE user_id=$4"
        async with self.pool.acquire() as db:
            await db.execute(sql, hp, mp, atk, user_id)

    async def update_user_hp_mp(self, user_id, hp, mp):
        """更新用户HP,MP信息"""
        sql = f"UPDATE user_xiuxian SET hp=$1,mp=$2 WHERE user_id=$3"
        async with self.pool.acquire() as db:
            await db.execute(sql, hp, mp, user_id)

    async def update_user_sect_contribution(self, user_id, sect_contribution):
        """更新用户宗门贡献度"""
        sql = f"UPDATE user_xiuxian SET sect_contribution=$1 WHERE user_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, sect_contribution, user_id)

    async def update_user_hp(self, user_id):
        """重置用户hp,mp信息"""
        sql = f"UPDATE user_xiuxian SET hp=exp/2,mp=exp,atk=exp/10 WHERE user_id=$1"
        async with self.pool.acquire() as db:
            await db.execute(sql, user_id)

    async def restate(self, user_id=None):
        """重置所有用户状态或重置对应人状态，老掉牙代码，不建议使用"""
        if user_id is None:
            sql = f"UPDATE user_xiuxian SET hp=exp/2,mp=exp,atk=exp/10"
            async with self.pool.acquire() as db:
                await db.execute(sql)

        else:
            sql = f"UPDATE user_xiuxian SET hp=exp/2,mp=exp,atk=exp/10 WHERE user_id=$1"
            async with self.pool.acquire() as db:
                await db.execute(sql, user_id)

    async def get_back_msg(self, user_id):
        """获取用户背包信息"""
        sql = f"SELECT * FROM back WHERE user_id=$1 and goods_num >= 1"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, user_id)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def get_back_msg_all(self, user_id):
        """获取用户背包信息"""
        sql = f"SELECT * FROM back WHERE user_id=$1"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, user_id)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def get_back_goal_type_msg(self, user_id, goods_type):
        """
        获取用户背包内指定类型物品信息
        :param user_id: 用户虚拟值
        :param goods_type: type = str 目标物品类型
        :return: type = list | None
        """
        sql = f"SELECT * FROM back WHERE user_id=$1 and goods_num >= 1 and goods_type = $2"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, user_id, goods_type)
            result_all = [zips(**result_per) for result_per in result]
            return result_all

    async def goods_num(self, user_id, goods_id):
        """
        判断用户物品数量
        :param user_id: 用户qq
        :param goods_id: 物品id
        :return: 物品数量
        """
        sql = "SELECT num FROM back WHERE user_id=$1 and goods_id=$2"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, user_id, goods_id)
            return zips(**result[0]) if result else None

    async def get_all_user_exp(self, level):
        """查询所有对应大境界玩家的修为"""
        sql = f"SELECT exp FROM user_xiuxian  WHERE level like '{level}%'"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql)
            result_all = [result_per[0] for result_per in result]
            return result_all

    async def update_user_atkpractice(self, user_id, atkpractice):
        """更新用户攻击修炼等级"""
        sql = f"UPDATE user_xiuxian SET atkpractice={atkpractice} WHERE user_id=$1"
        async with self.pool.acquire() as db:
            await db.execute(sql, user_id)

    async def update_user_sect_task(self, user_id, sect_task):
        """更新用户宗门任务次数"""
        sql = f"UPDATE user_xiuxian SET sect_task=sect_task+$1 WHERE user_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, sect_task, user_id)

    async def sect_task_reset(self):
        """重置宗门任务次数"""
        sql = f"UPDATE user_xiuxian SET sect_task=0"
        async with self.pool.acquire() as db:
            await db.execute(sql)

    async def update_sect_scale_and_used_stone(self, sect_id, sect_used_stone, sect_scale):
        """更新宗门灵石、建设度"""
        sql = f"UPDATE sects SET sect_used_stone=$1,sect_scale=$2 WHERE sect_id=$3"
        async with self.pool.acquire() as db:
            await db.execute(sql, sect_used_stone, sect_scale, sect_id)

    async def update_sect_elixir_room_level(self, sect_id, level):
        """更新宗门丹房等级"""
        sql = f"UPDATE sects SET elixir_room_level=$1 WHERE sect_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, level, sect_id)

    async def update_user_sect_elixir_get_num(self, user_id):
        """更新用户每日领取丹药领取次数"""
        sql = f"UPDATE user_xiuxian SET sect_elixir_get=1 WHERE user_id=$1"
        async with self.pool.acquire() as db:
            await db.execute(sql, user_id)

    async def sect_elixir_get_num_reset(self):
        """重置宗门丹药领取次数"""
        sql = f"UPDATE user_xiuxian SET sect_elixir_get=0"
        async with self.pool.acquire() as db:
            await db.execute(sql)

    async def update_sect_mainbuff(self, sect_id, mainbuffid):
        """更新宗门当前的主修功法"""
        sql = f"UPDATE sects SET mainbuff=$1 WHERE sect_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, mainbuffid, sect_id)

    async def update_sect_secbuff(self, sect_id, secbuffid):
        """更新宗门当前的神通"""
        sql = f"UPDATE sects SET secbuff=$1 WHERE sect_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, secbuffid, sect_id)

    async def initialize_user_buff_info(self, user_id):
        """初始化用户buff信息"""
        sql = f"INSERT INTO buff_info (user_id,main_buff,sec_buff,faqi_buff,fabao_weapon) VALUES ($1,0,0,0,0)"
        async with self.pool.acquire() as db:
            await db.execute(sql, user_id)

    async def get_user_buff_info(self, user_id):
        """获取用户buff信息"""
        sql = f"select * from buff_info WHERE user_id =$1"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, user_id)
            return zips(**result[0]) if result else None

    async def updata_user_main_buff(self, user_id, buff_id):
        """更新用户主功法信息"""
        sql = f"UPDATE buff_info SET main_buff = $1 WHERE user_id = $2"
        async with self.pool.acquire() as db:
            await db.execute(sql, buff_id, user_id)

    async def updata_user_sub_buff(self, user_id, buff_id):  # 辅修功法3
        """更新用户辅修功法信息"""
        sql = f"UPDATE buff_info SET sub_buff = $1 WHERE user_id = $2"
        async with self.pool.acquire() as db:
            await db.execute(sql, buff_id, user_id)

    async def updata_user_sec_buff(self, user_id, buff_id):
        """更新用户副功法信息"""
        sql = f"UPDATE buff_info SET sec_buff = $1 WHERE user_id = $2"
        async with self.pool.acquire() as db:
            await db.execute(sql, buff_id, user_id)

    async def updata_user_faqi_buff(self, user_id, buff_id):
        """更新用户法器信息"""
        sql = f"UPDATE buff_info SET faqi_buff = $1 WHERE user_id = $2"
        async with self.pool.acquire() as db:
            await db.execute(sql, buff_id, user_id)

    async def updata_user_fabao_weapon(self, user_id, buff_id):
        """更新用户法宝信息"""
        sql = f"UPDATE buff_info SET fabao_weapon = $1 WHERE user_id = $2"
        async with self.pool.acquire() as db:
            await db.execute(sql, buff_id, user_id)

    async def updata_user_armor_buff(self, user_id, buff_id):
        """更新用户防具信息"""
        sql = f"UPDATE buff_info SET armor_buff = $1 WHERE user_id = $2"
        async with self.pool.acquire() as db:
            await db.execute(sql, buff_id, user_id)

    async def updata_user_atk_buff(self, user_id, buff):
        """更新用户永久攻击buff信息"""
        sql = f"UPDATE buff_info SET atk_buff=atk_buff+$1 WHERE user_id = $2"
        async with self.pool.acquire() as db:
            await db.execute(sql, buff, user_id)

    async def updata_user_blessed_spot(self, user_id, blessed_spot):
        """更新用户洞天福地等级"""
        sql = f"UPDATE buff_info SET blessed_spot=$1 WHERE user_id = $2"
        async with self.pool.acquire() as db:
            await db.execute(sql, blessed_spot, user_id)

    async def update_user_blessed_spot_flag(self, user_id):
        """更新用户洞天福地是否开启"""
        sql = f"UPDATE user_xiuxian SET blessed_spot_flag=1 WHERE user_id=$1"
        async with self.pool.acquire() as db:
            await db.execute(sql, user_id)

    async def update_user_blessed_spot_name(self, user_id, blessed_spot_name):
        """更新用户洞天福地的名字"""
        sql = f"UPDATE user_xiuxian SET blessed_spot_name=$1 WHERE user_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, blessed_spot_name, user_id)

    async def day_num_reset(self):
        """重置丹药每日使用次数"""
        sql = f"UPDATE back SET day_num=0 WHERE goods_type='丹药'"
        async with self.pool.acquire() as db:
            await db.execute(sql)

    async def reset_work_num(self):
        """重置用户悬赏令刷新次数"""
        sql = f"UPDATE user_xiuxian SET work_num=0 "
        async with self.pool.acquire() as db:
            await db.execute(sql)

    async def get_work_num(self, user_id):  # todo 回滚主动更新
        """获取用户悬赏令刷新次数
           拥有被动效果，检测隔日自动重置悬赏令刷新 次数
        """
        sql = f"SELECT work_num FROM user_xiuxian WHERE user_id=$1"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, user_id)
            return result[0][0] if result else None

    async def update_work_num(self, user_id, work_num):
        sql = f"UPDATE user_xiuxian SET work_num=$1 WHERE user_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, work_num, user_id)

    async def send_back(self, user_id, goods_id, goods_name, goods_type, goods_num, bind_flag=0):
        """
        插入物品至背包
        :param user_id: 用户qq
        :param goods_id: 物品id
        :param goods_name: 物品名称
        :param goods_type: 物品类型
        :param goods_num: 物品数量
        :param bind_flag: 是否绑定物品,0-非绑定,1-绑定
        :return: None
        """
        now_time = datetime.now()
        now_time = str(now_time)
        # 检查物品是否存在，存在则update
        async with self.pool.acquire() as db:
            back = await self.get_item_by_good_id_and_user_id(user_id, goods_id)
            if back:
                # 判断是否存在，存在则update
                if bind_flag == 1:
                    bind_num = back['bind_num'] + goods_num
                else:
                    bind_num = back['bind_num']
                goods_nums = back['goods_num'] + goods_num
                sql = f"UPDATE back set goods_num=$1,update_time=$2,bind_num={bind_num} WHERE user_id=$3 and goods_id=$4"
                await db.execute(sql, goods_nums, now_time, user_id, goods_id)

            else:
                # 判断是否存在，不存在则INSERT
                if bind_flag == 1:
                    bind_num = goods_num
                else:
                    bind_num = 0
                sql = f"""
                        INSERT INTO back (user_id, goods_id, goods_name, goods_type, goods_num, create_time, update_time, bind_num)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)"""
                await db.execute(sql, user_id, goods_id, goods_name, goods_type, goods_num, now_time, now_time,
                                 bind_num)

    async def get_item_by_good_id_and_user_id(self, user_id, goods_id):
        """根据物品id、用户id获取物品信息"""
        sql = f"select * from back WHERE user_id=$1 and goods_id=$2"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, user_id, goods_id)
            return zips(**result[0]) if result else None

    async def update_back_equipment(self, sql_str):
        """更新背包,传入sql"""
        logger.opt(colors=True).info(f"<green>执行的sql:{sql_str}</green>")
        async with self.pool.acquire() as db:
            await db.execute(sql_str)

    async def update_back_j(self, user_id, goods_id, num=1, use_key=0):
        """
        使用物品
        :num 减少数量  默认1
        :use_key 是否使用，丹药使用传1 优先使用非绑定物品0  优先使用绑定物品2
        """
        back = await self.get_item_by_good_id_and_user_id(user_id, goods_id)
        goods_num = back['goods_num'] - num
        if back['goods_type'] == "丹药" and use_key == 1:  # 丹药要判断耐药性、日使用上限
            day_num = back['day_num'] + num
            all_num = back['all_num'] + num
            bind_num = max(back['bind_num'] - num, 0)
        elif use_key == 2:
            day_num = back['day_num']
            all_num = back['all_num']
            bind_num = max(back['bind_num'] - num, 0)
        else:
            day_num = back['day_num']
            all_num = back['all_num']
            bind_num = back['bind_num']
        bind_num = min(bind_num, goods_num)
        now_time = datetime.now()
        now_time = str(now_time)
        sql_str = (f"UPDATE back set update_time=$1,action_time=$2,goods_num=$3,"
                   f"day_num=$4,all_num=$5,bind_num=$6 "
                   f"WHERE user_id=$7 and goods_id=$8")
        async with self.pool.acquire() as db:
            await db.execute(sql_str, now_time, now_time, goods_num, day_num, all_num, bind_num,
                             user_id, goods_id)

    async def del_back_item(self, user_id, goods_id):
        """
        删除物品
        """
        sql_str = f"DELETE FROM back WHERE user_id={user_id} and goods_id={goods_id}"
        async with self.pool.acquire() as db:
            await db.execute(sql_str)

    async def bind_item(self, user_id, goods_id):
        """
        绑定物品
        """
        sql_str = f"UPDATE back set bind_num=goods_num WHERE user_id={user_id} and goods_id={goods_id}"
        async with self.pool.acquire() as db:
            await db.execute(sql_str)

    async def break_bind_item(self, user_id, goods_id):
        """
        解绑物品
        """
        sql_str = f"UPDATE back set bind_num=0 WHERE user_id={user_id} and goods_id={goods_id}"
        async with self.pool.acquire() as db:
            await db.execute(sql_str)

    async def set_sect_join_mode(self, sect_id, mode: bool):
        """
        关闭宗门加入
        """
        sql_str = f"UPDATE sects set is_open=$1 WHERE sect_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql_str, mode, sect_id)


sql_message = XiuxianDateManage()  # sql类


async def final_user_data(**user_dict):
    """
    传入用户当前信息、buff信息,返回最终信息
    糟糕的函数
    """
    for key, value in user_dict.items():
        if isinstance(value, decimal.Decimal):
            user_dict[key] = int(value)
    # 通过字段名称获取相应的值
    impart_data = await xiuxian_impart.get_user_info_with_id(user_dict['user_id'])
    if impart_data:
        pass
    else:
        await xiuxian_impart.impart_create_user(user_dict['user_id'])
        impart_data = await xiuxian_impart.get_user_info_with_id(user_dict['user_id'])
    for key, value in impart_data.items():
        if isinstance(value, decimal.Decimal):
            impart_data[key] = int(value)
    impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
    impart_mp_per = impart_data['impart_mp_per'] if impart_data is not None else 0
    impart_atk_per = impart_data['impart_atk_per'] if impart_data is not None else 0

    user_buff_data = await UserBuffDate(user_dict['user_id']).buff_info

    armor_atk_buff = 0
    if int(user_buff_data['armor_buff']) != 0:
        armor_info = items.get_data_by_item_id(user_buff_data['armor_buff'])
        armor_atk_buff = armor_info['atk_buff']

    weapon_atk_buff = 0
    if int(user_buff_data['faqi_buff']) != 0:
        weapon_info = items.get_data_by_item_id(user_buff_data['faqi_buff'])
        weapon_atk_buff = weapon_info['atk_buff']

    main_buff_data = await UserBuffDate(user_dict['user_id']).get_user_main_buff_data()
    main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
    main_mp_buff = main_buff_data['mpbuff'] if main_buff_data is not None else 0
    main_atk_buff = main_buff_data['atkbuff'] if main_buff_data is not None else 0

    hp_rate = level_data[user_dict['level']]["HP"]

    hp_final_buff = (1 + main_hp_buff + impart_hp_per) * hp_rate
    mp_final_buff = (1 + main_mp_buff + impart_mp_per)

    # 改成字段名称来获取相应的值
    user_dict['hp_buff'] = hp_final_buff
    user_dict['hp'] = int(user_dict['hp'] * hp_final_buff)
    user_dict['max_hp'] = int(user_dict['exp'] * hp_final_buff / 2)
    user_dict['mp_buff'] = mp_final_buff
    user_dict['mp'] = int(user_dict['mp'] * mp_final_buff)
    user_dict['max_mp'] = int(user_dict['exp'] * mp_final_buff)

    user_dict['atk'] = (int((user_dict['atk']
                             * (user_dict['atkpractice'] * 0.04 + 1)  # 攻击修炼
                             * (1 + main_atk_buff)  # 功法攻击加成
                             * (1 + weapon_atk_buff)  # 武器攻击加成
                             * (1 + armor_atk_buff))  # 防具攻击加成
                            * (1 + impart_atk_per))  # 传承攻击加成
                        + int(user_buff_data['atk_buff']))  # 攻击丹药加成

    return user_dict


# 这里是虚神界部分

class XiuxianImpartBuff:

    def __init__(self):
        self.pool = None

    async def check_data(self):
        """检查数据完整性"""
        async with self.pool.acquire() as db:

            for i in config_impart.sql_table:
                if i == "xiuxian_impart":
                    try:
                        await db.execute(f"select count(1) from {i}")
                    except asyncpg.exceptions.UndefinedTableError:
                        await db.execute(f"""CREATE TABLE "xiuxian_impart" (
        "id" bigserial,
        "user_id" numeric DEFAULT 0,
        "impart_hp_per" numeric DEFAULT 0,
        "impart_atk_per" numeric DEFAULT 0,
        "impart_mp_per" numeric DEFAULT 0,
        "impart_exp_up" numeric DEFAULT 0,
        "boss_atk" numeric DEFAULT 0,
        "impart_know_per" numeric DEFAULT 0,
        "impart_burst_per" numeric DEFAULT 0,
        "impart_mix_per" numeric DEFAULT 0,
        "impart_reap_per" numeric DEFAULT 0,
        "impart_two_exp" numeric DEFAULT 0,
        "stone_num" numeric DEFAULT 0,
        "pray_stone_num" numeric DEFAULT 0,
        "pray_card_num" numeric DEFAULT 0,
        "exp_day" numeric DEFAULT 0,
        "wish" numeric DEFAULT 0
        );""")

            for s in config_impart.sql_table_impart_buff:
                try:
                    await db.execute(f"select {s} from xiuxian_impart limit 1")
                except asyncpg.exceptions.UndefinedColumnError:
                    sql = f"ALTER TABLE xiuxian_impart ADD COLUMN {s} numeric DEFAULT 0;"
                    logger.opt(colors=True).info(f"<green>{sql}</green>")
                    logger.opt(colors=True).info(f"<green>xiuxian_impart数据库核对成功!</green>")
                    await db.execute(sql)

    async def check_user(self, user_id):
        """校验用户是否存在"""
        async with self.pool.acquire() as db:
            sql = f"select * from xiuxian_impart WHERE user_id=$1"
            result = await db.fetch(sql, user_id)
            return result[0][0] if result else None

    async def impart_create_user(self, user_id: int) -> None:
        """在数据库中创建用户并初始化"""
        if not await self.check_user(user_id):
            async with self.pool.acquire() as db:
                sql = (f"INSERT INTO xiuxian_impart ("
                       f"user_id, impart_hp_per, impart_atk_per, impart_mp_per, impart_exp_up , boss_atk, impart_know_per,"
                       f"impart_burst_per, impart_mix_per, impart_reap_per, impart_two_exp, stone_num, exp_day, wish) "
                       f"VALUES($1, 0, 0, 0, 0 ,0, 0, 0, 0, 0 ,0 ,0 ,0, 0)")
                await db.execute(sql, user_id)

    async def get_user_info_with_id(self, user_id):
        """根据USER_ID获取用户impart_buff信息"""
        async with self.pool.acquire() as db:
            sql = f"select * from xiuxian_impart WHERE user_id=$1"
            result = await db.fetch(sql, user_id)
            return zips(**result[0]) if result else None

    async def update_impart_hp_per(self, impart_num, user_id):
        """更新impart_hp_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_hp_per=$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def add_impart_hp_per(self, impart_num, user_id):
        """add impart_hp_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_hp_per=impart_hp_per+$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def update_impart_atk_per(self, impart_num, user_id):
        """更新impart_atk_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_atk_per=$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def add_impart_atk_per(self, impart_num, user_id):
        """add  impart_atk_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_atk_per=impart_atk_per+$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def update_impart_mp_per(self, impart_num, user_id):
        """impart_mp_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_mp_per=$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def add_impart_mp_per(self, impart_num, user_id):
        """add impart_mp_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_mp_per=impart_mp_per+$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def update_impart_exp_up(self, impart_num, user_id):
        """impart_exp_up"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_exp_up=$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def add_impart_exp_up(self, impart_num, user_id):
        """add impart_exp_up"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_exp_up=impart_exp_up+$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def update_boss_atk(self, impart_num, user_id):
        """boss_atk"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET boss_atk=$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def add_boss_atk(self, impart_num, user_id):
        """add boss_atk"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET boss_atk=boss_atk+$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def update_impart_know_per(self, impart_num, user_id):
        """impart_know_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_know_per=$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def add_impart_know_per(self, impart_num, user_id):
        """add impart_know_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_know_per=impart_know_per+$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def update_impart_burst_per(self, impart_num, user_id):
        """impart_burst_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_burst_per=$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def add_impart_burst_per(self, impart_num, user_id):
        """add impart_burst_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_burst_per=impart_burst_per+$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def update_impart_mix_per(self, impart_num, user_id):
        """impart_mix_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_mix_per=$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def add_impart_mix_per(self, impart_num, user_id):
        """add impart_mix_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_mix_per=impart_mix_per+$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def update_impart_reap_per(self, impart_num, user_id):
        """impart_reap_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_reap_per=$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def add_impart_reap_per(self, impart_num, user_id):
        """add impart_reap_per"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_reap_per=impart_reap_per+$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def update_impart_two_exp(self, impart_num, user_id):
        """更新双修"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_two_exp=$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def add_impart_two_exp(self, impart_num, user_id):
        """add impart_two_exp"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET impart_two_exp=impart_two_exp+$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def update_impart_wish(self, impart_num, user_id):
        """更新抽卡次数"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET wish=$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def add_impart_wish(self, impart_num, user_id):
        """增加抽卡次数"""
        async with self.pool.acquire() as db:
            sql = f"UPDATE xiuxian_impart SET wish=wish+$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def update_stone_num(self, impart_num, user_id, type_):
        """更新结晶数量"""
        if type_ == 1:
            async with self.pool.acquire() as db:
                sql = f"UPDATE xiuxian_impart SET stone_num=stone_num+$1 WHERE user_id=$2"
                await db.execute(sql, impart_num, user_id)

                return True
        if type_ == 2:
            async with self.pool.acquire() as db:
                sql = f"UPDATE xiuxian_impart SET stone_num=stone_num-$1 WHERE user_id=$2"
                await db.execute(sql, impart_num, user_id)

                return True

    async def update_pray_stone_num(self, impart_num, user_id, type_):
        """
        更新祈愿结晶数量
        1加 2减
        """
        if type_ == 1:
            async with self.pool.acquire() as db:
                sql = f"UPDATE xiuxian_impart SET pray_stone_num=pray_stone_num+$1 WHERE user_id=$2"
                await db.execute(sql, impart_num, user_id)

                return True
        if type_ == 2:
            async with self.pool.acquire() as db:
                sql = f"UPDATE xiuxian_impart SET pray_stone_num=pray_stone_num-$1 WHERE user_id=$2"
                await db.execute(sql, impart_num, user_id)
                return True

    async def update_pray_card_num(self, num, user_id, update_type: int = 0):
        """
        更新祈愿共鸣数量
        0加 1减 2设置
        """
        if not update_type:
            sql = f"UPDATE xiuxian_impart SET pray_card_num=pray_card_num-$1 WHERE user_id=$2"
        elif update_type == 1:
            sql = f"UPDATE xiuxian_impart SET pray_card_num=pray_card_num+$1 WHERE user_id=$2"
        else:
            sql = f"UPDATE xiuxian_impart SET pray_card_num=$1 WHERE user_id=$2"
        async with self.pool.acquire() as db:
            await db.execute(sql, num, user_id)
            return True

    async def update_impart_stone_all(self, impart_stone):
        """所有用户增加结晶"""
        async with self.pool.acquire() as db:
            sql = "UPDATE xiuxian_impart SET stone_num=stone_num+$1"
            await db.execute(sql, impart_stone)

    async def update_impart_pray_stone_all(self, impart_stone):
        """所有用户增加结晶"""
        async with self.pool.acquire() as db:
            sql = "UPDATE xiuxian_impart SET pray_stone_num=stone_num+$1"
            await db.execute(sql, impart_stone)

    async def add_impart_exp_day(self, impart_num, user_id):
        """add  impart_exp_day"""
        async with self.pool.acquire() as db:
            sql = "UPDATE xiuxian_impart SET exp_day=exp_day+$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True

    async def use_impart_exp_day(self, impart_num, user_id):
        """use  impart_exp_day"""
        async with self.pool.acquire() as db:
            sql = "UPDATE xiuxian_impart SET exp_day=exp_day-$1 WHERE user_id=$2"
            await db.execute(sql, impart_num, user_id)
            return True


async def leave_harm_time(user_id):
    hp_speed = 25
    user_mes = await sql_message.get_user_info_with_id(user_id)
    level = user_mes['level']
    level_rate = await sql_message.get_root_rate(user_mes['root_type'])  # 灵根倍率
    realm_rate = level_data[level]["spend"]  # 境界倍率
    main_buff_data = await UserBuffDate(user_id).get_user_main_buff_data()  # 主功法数据
    main_buff_rate_buff = main_buff_data['ratebuff'] if main_buff_data else 0  # 主功法修炼倍率

    try:
        time = int(((user_mes['exp'] / 1.5) - user_mes['hp']) / ((XiuConfig().closing_exp * level_rate * realm_rate * (
                1 + main_buff_rate_buff)) * hp_speed))
    except ZeroDivisionError:
        time = "无穷大"
    except OverflowError:
        time = "溢出"
    return time


xiuxian_impart = XiuxianImpartBuff()


@DRIVER.on_startup
async def check_main_db():
    sql_message.pool = database.pool
    logger.opt(colors=True).info(f"<green>xiuxian数据库已连接!</green>")
    xiuxian_impart.pool = database.pool
    logger.opt(colors=True).info(f"<green>xiuxian_impart数据库已连接!</green>")
    logger.opt(colors=True).info(f"<green>检查xiuxian数据库完整性中</green>")
    await sql_message.check_data()
    logger.opt(colors=True).info(f"<green>检查xiuxian数据库完整性成功</green>")
    logger.opt(colors=True).info(f"<green>检查xiuxian_impart数据库完整性中</green>")
    await xiuxian_impart.check_data()
    logger.opt(colors=True).info(f"<green>检查xiuxian_impart数据库完整性成功</green>")


class UserBuffDate:
    def __init__(self, user_id):
        """用户Buff数据"""
        self.user_id = user_id

    @property
    async def buff_info(self):
        """获取最新的 Buff 信息"""
        return await get_user_buff(self.user_id)

    async def get_user_main_buff_data(self):
        main_buff_data = None
        buff_info = await self.buff_info
        main_buff_id = buff_info.get('main_buff', 0)
        if main_buff_id != 0:
            main_buff_data = items.get_data_by_item_id(main_buff_id)
        return main_buff_data

    async def get_user_sub_buff_data(self):
        sub_buff_data = None
        buff_info = await self.buff_info
        sub_buff_id = buff_info.get('sub_buff', 0)
        if sub_buff_id != 0:
            sub_buff_data = items.get_data_by_item_id(sub_buff_id)
        return sub_buff_data

    async def get_user_sec_buff_data(self):
        sec_buff_data = None
        buff_info = await self.buff_info
        sec_buff_id = buff_info.get('sec_buff', 0)
        if sec_buff_id != 0:
            sec_buff_data = items.get_data_by_item_id(sec_buff_id)
        return sec_buff_data

    async def get_user_weapon_data(self):
        weapon_data = None
        buff_info = await self.buff_info
        weapon_id = buff_info.get('faqi_buff', 0)
        if weapon_id != 0:
            weapon_data = items.get_data_by_item_id(weapon_id)
        return weapon_data

    async def get_user_armor_buff_data(self):
        armor_buff_data = None
        buff_info = await self.buff_info
        armor_buff_id = buff_info.get('armor_buff', 0)
        if armor_buff_id != 0:
            armor_buff_data = items.get_data_by_item_id(armor_buff_id)
        return armor_buff_data


def get_weapon_info_msg(weapon_id, weapon_info=None):
    """
    获取一个法器(武器)信息msg
    :param weapon_id:法器(武器)ID
    :param weapon_info:法器(武器)信息json,可不传
    :return 法器(武器)信息msg
    """
    msg = ''
    if weapon_info is None:
        weapon_info = items.get_data_by_item_id(weapon_id)
    atk_buff_msg = f"提升{int(weapon_info['atk_buff'] * 100)}%攻击力！" if weapon_info['atk_buff'] != 0 else ''
    crit_buff_msg = f"提升{int(weapon_info['crit_buff'] * 100)}%会心率！" if weapon_info['crit_buff'] != 0 else ''
    crit_atk_msg = f"提升{int(weapon_info['critatk'] * 100)}%会心伤害！" if weapon_info['critatk'] != 0 else ''
    def_buff_msg = f"{'提升' if weapon_info['def_buff'] > 0 else '降低'}{int(abs(weapon_info['def_buff']) * 100)}%减伤率！" if \
        weapon_info['def_buff'] != 0 else ''
    zw_buff_msg = f"装备专属武器时提升伤害！！" if weapon_info['zw'] != 0 else ''
    mp_buff_msg = f"降低真元消耗{int(weapon_info['mp_buff'] * 100)}%！" if weapon_info['mp_buff'] != 0 else ''
    msg += f"名字：{weapon_info['name']}\r"
    msg += f"品阶：{weapon_info['level']}\r"
    msg += f"效果：{atk_buff_msg}{crit_buff_msg}{crit_atk_msg}{def_buff_msg}{mp_buff_msg}{zw_buff_msg}"
    return msg


def get_armor_info_msg(armor_id, armor_info=None):
    """
    获取一个法宝(防具)信息msg
    :param armor_id:法宝(防具)ID
    :param armor_info;法宝(防具)信息json,可不传
    :return 法宝(防具)信息msg
    """
    msg = ''
    if armor_info is None:
        armor_info = items.get_data_by_item_id(armor_id)
    def_buff_msg = f"提升{int(armor_info['def_buff'] * 100)}%减伤率！"
    atk_buff_msg = f"提升{int(armor_info['atk_buff'] * 100)}%攻击力！" if armor_info['atk_buff'] != 0 else ''
    crit_buff_msg = f"提升{int(armor_info['crit_buff'] * 100)}%会心率！" if armor_info['crit_buff'] != 0 else ''
    msg += f"名字：{armor_info['name']}\r"
    msg += f"品阶：{armor_info['level']}\r"
    msg += f"效果：{def_buff_msg}{atk_buff_msg}{crit_buff_msg}"
    return msg


def get_main_info_msg(item_id):
    mainbuff = items.get_data_by_item_id(item_id)
    hpmsg = f"提升{round(mainbuff['hpbuff'] * 100, 0)}%气血" if mainbuff['hpbuff'] != 0 else ''
    mpmsg = f"，提升{round(mainbuff['mpbuff'] * 100, 0)}%真元" if mainbuff['mpbuff'] != 0 else ''
    atkmsg = f"，提升{round(mainbuff['atkbuff'] * 100, 0)}%攻击力" if mainbuff['atkbuff'] != 0 else ''
    ratemsg = f"，提升{round(mainbuff['ratebuff'] * 100, 0)}%修炼速度" if mainbuff['ratebuff'] != 0 else ''

    cri_tmsg = f"，提升{round(mainbuff['crit_buff'] * 100, 0)}%会心率" if mainbuff['crit_buff'] != 0 else ''
    def_msg = f"，{'提升' if mainbuff['def_buff'] > 0 else '降低'}{round(abs(mainbuff['def_buff']) * 100, 0)}%减伤率" if \
        mainbuff['def_buff'] != 0 else ''
    dan_msg = f"，增加炼丹产出{round(mainbuff['dan_buff'])}枚" if mainbuff['dan_buff'] != 0 else ''
    dan_exp_msg = f"，每枚丹药额外增加{round(mainbuff['dan_exp'])}炼丹经验" if mainbuff['dan_exp'] != 0 else ''
    reap_msg = f"，提升药材收取数量{round(mainbuff['reap_buff'])}个" if mainbuff['reap_buff'] != 0 else ''
    exp_msg = f"，突破失败{round(mainbuff['exp_buff'] * 100, 0)}%经验保护" if mainbuff['exp_buff'] != 0 else ''
    critatk_msg = f"，提升{round(mainbuff['critatk'] * 100, 0)}%会心伤害" if mainbuff['critatk'] != 0 else ''
    two_msg = f"，增加{round(mainbuff['two_buff'])}次双修次数" if mainbuff['two_buff'] != 0 else ''
    number_msg = f"，提升{round(mainbuff['number'])}%突破概率" if mainbuff['number'] != 0 else ''

    clo_exp_msg = f"，提升{round(mainbuff['clo_exp'] * 100, 0)}%闭关经验" if mainbuff['clo_exp'] != 0 else ''
    clo_rs_msg = f"，提升{round(mainbuff['clo_rs'] * 100, 0)}%闭关生命回复" if mainbuff['clo_rs'] != 0 else ''
    random_buff_msg = f"，战斗时随机获得一个战斗属性" if mainbuff['random_buff'] != 0 else ''
    ew_msg = f"，使用专属武器时伤害增加50%！" if mainbuff['ew'] != 0 else ''
    msg = f"{mainbuff['name']}: {hpmsg}{mpmsg}{atkmsg}{ratemsg}{cri_tmsg}{def_msg}{dan_msg}{dan_exp_msg}{reap_msg}{exp_msg}{critatk_msg}{two_msg}{number_msg}{clo_exp_msg}{clo_rs_msg}{random_buff_msg}{ew_msg}！"
    return mainbuff, msg


def get_sub_info_msg(item_id):  # 辅修功法8
    subbuff = items.get_data_by_item_id(item_id)
    submsg = ""
    if subbuff['buff_type'] == '1':
        submsg = "提升" + subbuff['buff'] + "%攻击力"
    if subbuff['buff_type'] == '2':
        submsg = "提升" + subbuff['buff'] + "%暴击率"
    if subbuff['buff_type'] == '3':
        submsg = "提升" + subbuff['buff'] + "%暴击伤害"
    if subbuff['buff_type'] == '4':
        submsg = "提升" + subbuff['buff'] + "%每回合气血回复"
    if subbuff['buff_type'] == '5':
        submsg = "提升" + subbuff['buff'] + "%每回合真元回复"
    if subbuff['buff_type'] == '6':
        submsg = "提升" + subbuff['buff'] + "%气血吸取"
    if subbuff['buff_type'] == '7':
        submsg = "提升" + subbuff['buff'] + "%真元吸取"
    if subbuff['buff_type'] == '8':
        submsg = "给对手造成" + subbuff['buff'] + "%中毒"
    if subbuff['buff_type'] == '9':
        submsg = f"提升{subbuff['buff']}%气血吸取,提升{subbuff['buff2']}%真元吸取"

    stone_msg = "提升{}%boss战灵石获取".format(round(subbuff['stone'] * 100, 0)) if subbuff['stone'] != 0 else ''
    integral_msg = "，提升{}点boss战积分获取".format(round(subbuff['integral'])) if subbuff['integral'] != 0 else ''
    jin_msg = "禁止对手吸取" if subbuff['jin'] != 0 else ''
    drop_msg = "，提升boss掉落率" if subbuff['drop'] != 0 else ''
    fan_msg = "使对手发出的debuff失效" if subbuff['fan'] != 0 else ''
    break_msg = "获得战斗破甲" if subbuff['break'] != 0 else ''
    exp_msg = "，增加战斗获得的修为" if subbuff['exp'] != 0 else ''

    msg = f"{subbuff['name']}：{submsg}{stone_msg}{integral_msg}{jin_msg}{drop_msg}{fan_msg}{break_msg}{exp_msg}"
    return subbuff, msg


async def get_user_buff(user_id):
    buff_info = await sql_message.get_user_buff_info(user_id)
    if buff_info is None:
        await sql_message.initialize_user_buff_info(user_id)
        return await sql_message.get_user_buff_info(user_id)
    else:
        return buff_info


def readf(filepath):
    with open(filepath, "r", encoding="UTF-8") as f:
        data = f.read()
    return json.loads(data)


def get_sec_msg(secbuffdata):
    msg = None
    if secbuffdata is None:
        msg = "无"
        return msg
    hpmsg = f"，消耗当前血量{int(secbuffdata['hpcost'] * 100)}%" if secbuffdata['hpcost'] != 0 else ''
    mpmsg = f"，消耗真元{int(secbuffdata['mpcost'] * 100)}%" if secbuffdata['mpcost'] != 0 else ''

    if secbuffdata['skill_type'] == 1:
        shmsg = ''
        for value in secbuffdata['atkvalue']:
            shmsg += f"{value}倍、"
        if secbuffdata['turncost'] == 0:
            msg = f"攻击{len(secbuffdata['atkvalue'])}次，造成{shmsg[:-1]}伤害{hpmsg}{mpmsg}，释放概率：{secbuffdata['rate']}%"
        else:
            msg = f"连续攻击{len(secbuffdata['atkvalue'])}次，造成{shmsg[:-1]}伤害{hpmsg}{mpmsg}，休息{secbuffdata['turncost']}回合，释放概率：{secbuffdata['rate']}%"
    elif secbuffdata['skill_type'] == 2:
        msg = f"持续伤害，造成{secbuffdata['atkvalue']}倍攻击力伤害{hpmsg}{mpmsg}，无视敌方20%减伤率，无法暴击，持续{secbuffdata['turncost']}回合，释放概率：{secbuffdata['rate']}%"
    elif secbuffdata['skill_type'] == 3:
        if secbuffdata['bufftype'] == 1:
            msg = f"增强自身，提高{secbuffdata['buffvalue']}倍攻击力{hpmsg}{mpmsg}，持续{secbuffdata['turncost']}回合，释放概率：{secbuffdata['rate']}%"
        elif secbuffdata['bufftype'] == 2:
            msg = f"增强自身，提高{secbuffdata['buffvalue'] * 100}%减伤率{hpmsg}{mpmsg}，持续{secbuffdata['turncost']}回合，释放概率：{secbuffdata['rate']}%"
    elif secbuffdata['skill_type'] == 4:
        msg = f"封印对手{hpmsg}{mpmsg}，持续{secbuffdata['turncost']}回合，释放概率：{secbuffdata['rate']}%，命中成功率{secbuffdata['success']}%"

    return msg


def get_player_info(user_id, info_name):
    player_info = None
    if info_name == "mix_elixir_info":  # 灵田信息
        mix_elixir_info_config_key = ["收取时间", "收取等级", "灵田数量", '药材速度', "丹药控火", "丹药耐药性",
                                      "炼丹记录", "炼丹经验"]
        nowtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # str
        mix_elixir_info_config = {
            "收取时间": nowtime,
            "收取等级": 0,
            "灵田数量": 1,
            '药材速度': 0,
            "丹药控火": 0,
            "丹药耐药性": 0,
            "炼丹记录": {},
            "炼丹经验": 0
        }
        try:
            player_info = read_player_info(user_id, info_name)
            for key in mix_elixir_info_config_key:
                if key not in list(player_info.keys()):
                    player_info[key] = mix_elixir_info_config[key]
            save_player_info(user_id, player_info, info_name)
        except:
            player_info = mix_elixir_info_config
            save_player_info(user_id, player_info, info_name)
    return player_info


def read_player_info(user_id, info_name):
    user_id = str(user_id)
    filepath = PLAYERSDATA / user_id / f"{info_name}.json"
    with open(filepath, "r", encoding="UTF-8") as f:
        data = f.read()
    return json.loads(data)


def save_player_info(user_id, data, info_name):
    user_id = str(user_id)

    if not os.path.exists(PLAYERSDATA / user_id):
        logger.opt(colors=True).info(f"<green>用户目录不存在，创建目录</green>")
        os.makedirs(PLAYERSDATA / user_id)

    filepath = PLAYERSDATA / user_id / f"{info_name}.json"
    data = json.dumps(data, ensure_ascii=False, indent=4)
    save_mode = "w" if os.path.exists(filepath) else "x"
    with open(filepath, mode=save_mode, encoding="UTF-8") as f:
        f.write(data)
        f.close()
