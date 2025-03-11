import pickle
import re
from datetime import datetime

import asyncpg
from asyncpg import Record
from nonebot import logger

from .. import DRIVER
from ..xiuxian_database.database_connect import database
from ..xiuxian_utils.clean_utils import zips
from ..xiuxian_utils.item_json import items

xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号


def get_num_from_str(msg) -> list:
    """
    从消息字符串中获取数字列表
    :param msg: 从纯字符串中获取的获取的消息字符串
    :return: 提取到的分块整数
    """
    num = re.findall(r"\d+", msg)
    return num


class LimitData:

    def __init__(self):
        self.pool = None
        self.blob_data = ["offset_get", "active_get", "state", "lock_item"]
        self.sql_limit = ["user_id", "stone_exp_up", "send_stone", "receive_stone",
                          "impart_pk", "two_exp_up", "rift_protect",
                          "offset_get", "active_get", "last_time", "state"]

    async def check_data(self):
        """检查数据完整性"""
        async with self.pool.acquire() as db:
            try:
                await db.execute(f"select count(1) from user_limit")
            except asyncpg.exceptions.UndefinedTableError:
                await db.execute("""CREATE TABLE "user_limit" (
          "user_id" numeric NOT NULL,
          "stone_exp_up" bigint DEFAULT 0,
          "send_stone" bigint DEFAULT 0,
          "receive_stone" bigint DEFAULT 0,
          "impart_pk" integer DEFAULT 0,
          "two_exp_up" integer DEFAULT 0,
          "send_exp_accept" boolean DEFAULT false,
          "rift_protect" integer DEFAULT 0,
          "offset_get" bytea,
          "active_get" bytea,
          "lock_item" bytea,
          "last_time" TEXT,
          "state" bytea
          );""")
            try:
                await db.execute(f"select count(1) from active")
            except asyncpg.exceptions.UndefinedTableError:
                await db.execute("""CREATE TABLE "active" (
          "active_id" bigint NOT NULL,
          "active_name" TEXT,
          "active_desc" TEXT,
          "state" bytea,
          "start_time" TEXT,
          "last_time" TEXT,
          "daily_update" boolean DEFAULT false
          );""")
            try:
                await db.execute(f"select count(1) from offset_list")
            except asyncpg.exceptions.UndefinedTableError:
                await db.execute("""CREATE TABLE "offset_list" (
          "offset_id" bigint NOT NULL,
          "offset_name" TEXT,
          "offset_desc" TEXT,
          "offset_items" bytea,
          "state" bytea,
          "start_time" TEXT,
          "last_time" TEXT,
          "daily_update" boolean DEFAULT false
          );""")

    # 上面是数据库校验，别动

    async def get_limit_by_user_id(self, user_id) -> tuple[dict[str, int | dict | str], bool]:
        """
        获取目标用户限制列表
        :param user_id: 用户id
        :return:
        """
        date = datetime.now().date()
        now_time = date.today()
        now_time = str(now_time)
        sql = f"select * from user_limit WHERE user_id=$1"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, user_id)
            if not result:
                # 如果没有，则初始化
                limit_dict = {}
                for key in self.sql_limit:
                    limit_dict[key] = 0
                limit_dict['user_id'] = user_id
                limit_dict['last_time'] = now_time
                limit_dict['send_exp_accept'] = False

                for key in self.blob_data:
                    limit_dict[key] = {}
                return limit_dict, False

            # 如果有，返回限制字典
            limit_dict = zips(**result[0])
            for blob_key in self.blob_data:  # 结构化数据读取
                if limit_dict.get(blob_key):
                    limit_dict[blob_key] = pickle.loads(limit_dict[blob_key])
                else:
                    limit_dict[blob_key] = {}
            return limit_dict, True

    async def get_active_idmap(self):
        sql = f"SELECT active_name, active_id FROM active"
        async with self.pool.acquire() as db:
            result: list[Record] = await db.fetch(sql)
            result: dict[str, int] = {result_per[0]: result_per[1] for result_per in result}
            return result

    async def get_offset_idmap(self) -> dict[str, int]:
        sql = f"SELECT offset_name, offset_id FROM offset_list"
        async with self.pool.acquire() as db:
            result: list[Record] = await db.fetch(sql)
            result: dict[str, int] = {result_per[0]: result_per[1] for result_per in result}
            return result

    async def get_active_by_id(self, active_id):
        """
        获取活动内容
        :param active_id: 活动id
        :return:
        """
        sql = f"select * from active WHERE active_id=$1"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, active_id)
            # 如果有，返回活动字典
            return zips(**result[0]) if result else {}

    async def get_offset_by_id(self, offset_id):
        """
        获取补偿内容
        :param offset_id: 活动id
        :return:
        """
        sql = f"select * from offset_list WHERE offset_id=$1"
        async with self.pool.acquire() as db:
            result = await db.fetch(sql, offset_id)
            # 如果有，返回补偿字典
            offset = zips(**result[0]) if result else {}
            if offset.get('offset_items'):
                offset['offset_items'] = pickle.loads(offset['offset_items'])
            return offset

    async def active_make(self, active_id: int, active_name: str, active_desc: str,
                          last_time: str, daily_update: int, state=''):

        date = datetime.now().date()
        start_time = str(date.today())  # 标记创建日期
        async with self.pool.acquire() as db:
            sql = f"""INSERT INTO active (active_id, active_name, active_desc, start_time, last_time, daily_update, state)
                    VALUES ($1,$2,$3,$4,$5,$6,$7)"""
            await db.execute(sql, active_id, active_name, active_desc, start_time, last_time, daily_update, state)

    async def offset_make(self, offset_id: int, offset_name: str, offset_desc: str, offset_items: dict,
                          last_time: str, daily_update: int, state=''):
        date = datetime.now().date()
        start_time = str(date.today())  # 标记创建日期
        offset_items = pickle.dumps(offset_items)  # 结构化数据
        async with self.pool.acquire() as db:
            sql = f"""INSERT INTO offset_list (offset_id, offset_name, offset_desc, offset_items, start_time, last_time, daily_update, state)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8)"""
            await db.execute(
                sql,
                offset_id, offset_name, offset_desc,
                offset_items, start_time, last_time,
                daily_update, state)

    async def offset_del(self, offset_id: int):
        async with self.pool.acquire() as db:
            sql = f"""DELETE FROM offset_list
                    WHERE offset_id={offset_id};"""
            await db.execute(sql)

    async def update_limit_data(
            self,
            user_id,
            stone_exp_up,
            send_stone,
            receive_stone,
            impart_pk,
            two_exp_up,
            rift_protect,
            offset_get,
            active_get,
            state, **kwargs):
        """
        更新用户限制
        """
        date = datetime.now().date()
        now_time = date.today()
        now_time = str(now_time)
        async with self.pool.acquire() as db:
            offset_get = pickle.dumps(offset_get)  # 结构化数据
            active_get = pickle.dumps(active_get)
            state = pickle.dumps(state)
            table, is_pass = await self.get_limit_by_user_id(user_id)
            if is_pass:
                # 判断是否存在，存在则update
                sql = (f"UPDATE user_limit set "
                       f"stone_exp_up=$1,send_stone=$2,receive_stone=$3,impart_pk=$4,two_exp_up=$5,"
                       f"offset_get =$6,active_get=$7,last_time=$8,state=$9 "
                       f"WHERE user_id=$10")
                await db.execute(sql, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up,
                                 offset_get, active_get, now_time, state, user_id)
            else:
                # 判断是否存在，不存在则INSERT
                sql = (f"INSERT INTO user_limit "
                       f"(user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up, rift_protect, "
                       f"offset_get, active_get, last_time, state) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)")
                await db.execute(sql, user_id, stone_exp_up, send_stone, receive_stone,
                                 impart_pk, two_exp_up, rift_protect,
                                 offset_get, active_get, now_time, state)

    async def update_limit_data_with_key(
            self,
            update_key: str,
            goal,
            user_id,
            stone_exp_up,
            send_stone,
            receive_stone,
            impart_pk,
            two_exp_up,
            rift_protect,
            offset_get,
            active_get,
            state, **kwargs):
        """
        定向值更新用户限制 update_key: 欲定向更新的列值
        :return: result
        """
        blob_data = self.blob_data
        date = datetime.now().date()
        now_time = date.today()
        now_time = str(now_time)
        async with self.pool.acquire() as db:
            if update_key in blob_data:  # 结构化数据
                goal = pickle.dumps(goal)
            table, is_pass = await self.get_limit_by_user_id(user_id)
            if is_pass:
                # 判断是否存在，存在则update
                sql = f"UPDATE user_limit set {update_key}=$1 WHERE user_id=$2"
                await db.execute(sql, goal, user_id)
            else:
                # 判断是否存在，不存在则INSERT
                offset_get = pickle.dumps(offset_get)  # 结构化数据
                active_get = pickle.dumps(active_get)
                state = pickle.dumps(state)
                sql = f"""INSERT INTO user_limit (user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up, 
                rift_protect, offset_get, active_get, last_time, state)VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)"""
                await db.execute(sql,
                                 user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up, rift_protect,
                                 offset_get, active_get, now_time, state)

    async def redata_limit_by_key(self, reset_key):
        datetime.now().date()
        async with self.pool.acquire() as db:
            sql = f"UPDATE user_limit set {reset_key}=$1 "
            default_value = 0
            if reset_key in self.blob_data:  # 结构化数据
                default_value = {}
                default_value = pickle.dumps(default_value)

            await db.execute(sql, default_value)


limit_data = LimitData()


class LimitHandle:
    def __init__(self):
        self._database = limit_data
        self.blob_data = self._database.blob_data
        self.msg_list = ['name', 'desc']
        self.sql_limit = self._database.sql_limit
        self.keymap = {1: "stone_exp_up", 2: "send_stone", 3: "receive_stone", 4: "impart_pk",
                       5: "two_exp_up", 6: "offset_get", 7: "active_get", 8: "rift_protect"}
        pass

    async def get_active_msg(self):
        """活动简要信息"""
        idmap = await self._database.get_active_idmap()
        msg = "\r"
        if idmap:
            for name in idmap:
                msg += f"活动ID：{idmap[name]}  活动名称：{name}\r"
            return msg
        else:
            return None

    async def get_offset_list(self):
        """补偿简要列表"""
        idmap = await self._database.get_offset_idmap()
        msg = "\r"
        if idmap:
            for name in idmap:
                msg += f"补偿ID：{idmap[name]}  补偿名称：{name}\r"
            return msg
        else:
            return None

    @staticmethod
    async def change_offset_info_to_msg(offset_info):
        """
        格式化补偿数据为友好视图
        :param offset_info:
        :return:
        """
        if offset_info:
            offset_id = offset_info.get("offset_id")
            name = offset_info.get("offset_name")
            desc = offset_info.get("offset_desc")
            offset_items = offset_info.get("offset_items")
            last_time = offset_info.get("last_time")
            offset_info.get("state")
            daily_update = offset_info.get("daily_update")
            msg = f"补偿ID：{offset_id}\r补偿名称：{name}\r补偿介绍：{desc}\r"
            if offset_items:
                msg += "包含物品：\r"
                for item_id in offset_items:
                    msg += f"物品：{items.get_data_by_item_id(item_id).get('name', '不存在的物品')}  物品数量：{offset_items[item_id]}\r"
            msg += f"补偿领取截止时间：{last_time}\r"
            if daily_update:
                msg += "每日刷新领取\r"
            else:
                msg += "只可领取一次\r"
            return msg

    async def get_offset_msg(self, offset_id):
        """
        获取单个补偿的详情信息
        :param offset_id:
        :return:
        """
        offset_info = await self._database.get_offset_by_id(offset_id)
        offset_msg = await self.change_offset_info_to_msg(offset_info)
        return offset_msg

    async def get_all_user_offset_msg(self, user_id) -> list:
        """
        获取用户的所有补偿状态
        :param user_id:
        :return:
        """
        idmap = await self._database.get_offset_idmap()
        offset_list = []
        for offset_name, offset_id in idmap.items():
            is_get_offset = await self.check_user_offset(user_id, offset_id)
            offset_msg = await self.get_offset_msg(offset_id)
            if is_get_offset:
                offset_msg += "可领取\r"
            else:
                offset_msg += "无法领取\r"
            offset_list.append(offset_msg)
        return offset_list

    async def update_user_limit(self, user_id, limit_num: int, update_data: int, update_type: int = 0):
        """
        更新用户限制数据
        :param user_id: 用户ID
        :param limit_num: 更新目标值
        支持的值：1:"stone_exp_up"|2:"send_stone"|3:"receive_stone"|4:"impart_pk"|5:"two_exp_up"|8:"rift_protect"
        :param update_data: 更新的数据
        :param update_type: 更新类型 0为增加 1为减少
        :return: 是否成功
        """
        limit_key = self.keymap[limit_num]  # 懒狗只想打数字
        limit_dict, is_pass = await self._database.get_limit_by_user_id(user_id)
        goal_data = limit_dict[limit_key]
        if update_type:
            update_data = -update_data
        goal_data += update_data
        limit_dict[limit_key] = goal_data
        await self._database.update_limit_data_with_key(limit_key, limit_dict[limit_key], **limit_dict)
        return True

    async def reset_daily_limit(self, user_id):
        """
        完全重置状态，包括日志，补偿领取等，不建议使用
        :param user_id:
        :return:
        """
        date = datetime.now().date()
        now_time = date.today()
        now_time = str(now_time)

        limit_dict = {}
        for key in self.sql_limit:
            limit_dict[key] = 0
        limit_dict['user_id'] = user_id
        limit_dict['last_time'] = now_time
        for key in self.blob_data:
            limit_dict[key] = {}
        await self._database.update_limit_data(**limit_dict)

    async def update_user_offset(self, user_id, offset_id: int) -> tuple[bool, str]:
        """
        更新用户补偿状态，附带检查限制效果，通过获取参数传出布尔值可直接用于检查限制
        :param user_id: 用户ID
        :param offset_id: 补偿ID
        :return: bool
        """
        date = datetime.now().date()
        now_date = date.today()
        now_date_str = str(now_date)
        object_key = 'offset_get'  # 可变参数，记得修改方法
        offset_info = await self._database.get_offset_by_id(offset_id)
        daily = offset_info['daily_update']  # 是否日刷新
        start_time_str = offset_info['start_time']  # 开始日期
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d") \
            if start_time_str else datetime.now()  # 格式化至time对象
        start_time = start_time.date()
        last_time_str = offset_info['last_time']  # 结束日期
        last_time = datetime.strptime(last_time_str, "%Y-%m-%d")  # 格式化至time对象
        last_time = last_time.date()
        if start_time > now_date:
            msg = "该补偿未开放领取！！！"
            return False, msg
        elif last_time < now_date:
            msg = "该补偿已过期！！！"
            return False, msg

        limit_dict, is_pass = await self._database.get_limit_by_user_id(user_id)
        offset_get: dict = limit_dict[object_key]
        if not isinstance(offset_get, dict):
            offset_get = {}
        offset_state = offset_get.get(offset_id)

        if not offset_state:
            # 若无则初始化 返回True
            offset_get[offset_id] = [1, now_date_str]  # 数据为列表形式，格式为，[次数，日期]
            limit_dict[object_key] = offset_get
            await self._database.update_limit_data_with_key(object_key, limit_dict[object_key], **limit_dict)
            return True, ''  # 返回检查成功

        # 如果有该补偿数据则获取最后日期
        last_act_time = offset_state[1]
        # 格式字符串格式回datetime格式
        last_act_time = datetime.strptime(last_act_time, "%Y-%m-%d")  # 最后领取日期
        last_act_time = last_act_time.date()

        if daily:  # 检查补偿类型
            if now_date == last_act_time:  # 日刷新判断
                msg = "道友今日已经领取过该补偿啦！！"
            else:
                # 非同日则更新
                offset_state[0] += 1
                offset_state[1] = now_date_str
                offset_get[offset_id] = offset_state
                limit_dict[object_key] = offset_get
                await self._database.update_limit_data_with_key(object_key, limit_dict[object_key], **limit_dict)
                return True, ''  # 返回检查成功
        else:
            # 非日更检查是否为新补偿
            if start_time > last_act_time:
                # 新补偿覆盖旧补偿数据
                offset_get[offset_id] = [1, now_date_str]  # 数据为列表形式，格式为，[次数，日期]
                limit_dict[object_key] = offset_get
                await self._database.update_limit_data_with_key(object_key, limit_dict[object_key], **limit_dict)
                return True, ''  # 返回检查成功
            msg = "道友已经领取过该补偿啦！！！！"
        return False, msg  # 流程均检查失败 返回检查失败

    async def check_user_offset(self, user_id, offset_id: int) -> bool:
        """
        仅检查限制，通过获取参数传出布尔值用于检查限制
        :param user_id: 用户ID
        :param offset_id: 补偿ID
        :return: bool
        """
        date = datetime.now().date()
        now_date = date.today()
        object_key = 'offset_get'  # 可变参数，记得修改方法
        offset_info = await self._database.get_offset_by_id(offset_id)
        daily = offset_info['daily_update']  # 是否日刷新
        start_time_str = offset_info['start_time']  # 开始日期
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d") \
            if start_time_str else datetime.now()  # 格式化至time对象
        start_time = start_time.date()
        last_time_str = offset_info['last_time']  # 结束日期
        last_time = datetime.strptime(last_time_str, "%Y-%m-%d")  # 格式化至time对象
        last_time = last_time.date()
        if start_time > now_date or last_time < now_date:
            return False
        limit_dict, is_pass = await self._database.get_limit_by_user_id(user_id)
        offset_get = limit_dict[object_key]
        offset_state = offset_get.get(offset_id)
        if not offset_state:
            # 若无则初始化 返回True
            return True  # 返回检查成功
        # 如果有该补偿数据则获取最后日期
        last_act_time = offset_state[1]
        # 格式字符串格式回datetime格式
        last_act_time = datetime.strptime(last_act_time, "%Y-%m-%d")
        last_act_time = last_act_time.date()
        if daily:  # 检查补偿类型
            if now_date != last_act_time:  # 日刷新判断
                # 非同日则更新
                return True  # 返回检查成功
        else:
            # 非日更检查是否为新补偿
            if start_time > last_act_time:
                return True  # 返回检查成功
        return False  # 流程均检查失败 返回检查失败

    async def _update_user_log_data_by_keys(self, user_id, msg_body: str, log_name: str) -> bool:
        """
        通用文本日志接口
        写入用户日志信息
        :param user_id: 用户ID
        :param msg_body: 需要写入的信息
        :param log_name: 日志名称
        :return: bool
        """
        now_date = datetime.now()
        now_date = now_date.replace(microsecond=0)
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = await self._database.get_limit_by_user_id(user_id)
        state_dict: dict = limit_dict[object_key]

        logs: list = state_dict.get(log_name) if isinstance(state_dict, dict) else []

        log_data: str = "时间：" + str(now_date) + "\r" + msg_body
        if isinstance(logs, list):
            logs.append(log_data)
            if len(logs) > 10:
                logs = logs[1:]
        else:
            logs = [log_data]
        if isinstance(state_dict, dict):
            state_dict[log_name] = logs
        else:
            state_dict = {log_name: logs}
        limit_dict[object_key] = state_dict
        await self._database.update_limit_data_with_key(object_key, limit_dict[object_key], **limit_dict)
        return True

    async def _get_user_log_data_by_keys(self, user_id: int, log_name: str) -> list | int | None:
        """
        通用日志调取接口，低安全性
        """
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = await self._database.get_limit_by_user_id(user_id)
        state_dict = limit_dict[object_key]
        state_dict = state_dict if isinstance(state_dict, dict) else {}
        logs = state_dict.get(log_name)
        return logs if logs else None

    async def update_user_log_data(self, user_id: int, msg_body: str) -> bool:
        """
        写入用户日志信息
        :param user_id: 用户ID
        :param msg_body: 需要写入的信息
        :return: bool
        """
        log_name = 'log'
        await self._update_user_log_data_by_keys(user_id, msg_body, log_name)
        return True

    async def get_user_log_data(self, user_id: int) -> list | None:
        log_name: str = 'log'
        logs = await self._get_user_log_data_by_keys(user_id, log_name)
        return logs

    async def update_user_shop_log_data(self, user_id, msg_body: str) -> bool:
        """
        写入用户日志信息
        :param user_id: 用户ID
        :param msg_body: 需要写入的信息
        :return: bool
        """
        log_name: str = 'shop_log'
        await self._update_user_log_data_by_keys(user_id, msg_body, log_name)
        return True

    async def get_user_shop_log_data(self, user_id):
        log_name: str = 'shop_log'
        logs = await self._get_user_log_data_by_keys(user_id, log_name)
        return logs

    async def update_user_donate_log_data(self, user_id, msg_body: str) -> bool:
        """
        写入用户周贡献信息
        :param user_id: 用户ID
        :param msg_body: 需要写入的信息
        :return: bool
        """
        # now_date = datetime.now()
        # now_date = now_date.replace(microsecond=0)
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = await self._database.get_limit_by_user_id(user_id)
        state_dict = limit_dict[object_key]
        logs = state_dict.get('week_donate_log', 0) if isinstance(state_dict, dict) else 0
        log_data = get_num_from_str(msg_body)
        log_data = int(log_data[-1]) if log_data else 0
        logs += log_data
        try:
            state_dict['week_donate_log'] = logs
        except TypeError:
            state_dict = {'week_donate_log': logs}
        limit_dict[object_key] = state_dict
        await self._database.update_limit_data_with_key(object_key, limit_dict[object_key], **limit_dict)
        return True

    async def get_user_donate_log_data(self, user_id):
        log_name: str = 'week_donate_log'
        logs = await self._get_user_log_data_by_keys(user_id, log_name)
        return int(logs) if logs else 0

    async def update_user_world_power_data(self, user_id, world_power) -> bool:
        """
        写入用户天地精华信息
        :param user_id: 用户ID
        :param world_power:
        :return: bool
        """
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = await self._database.get_limit_by_user_id(user_id)
        state_dict = limit_dict[object_key]
        logs = world_power
        try:
            state_dict['world_power'] = logs
        except TypeError:
            state_dict = {'world_power': logs}
        limit_dict[object_key] = state_dict
        await self._database.update_limit_data_with_key(object_key, limit_dict[object_key], **limit_dict)
        return True

    async def get_user_world_power_data(self, user_id):
        log_name: str = 'world_power'
        logs = await self._get_user_log_data_by_keys(user_id, log_name)
        return int(logs) if logs else 0

    async def get_user_rift_protect(self, user_id):
        limit_dict, is_pass = await self._database.get_limit_by_user_id(user_id)
        rift_protect = limit_dict['rift_protect']
        return rift_protect

    async def get_user_lock_item_dict(self, user_id) -> dict[str, int]:
        user_limit, _ = await self._database.get_limit_by_user_id(user_id)
        return user_limit['lock_item']


limit_handle = LimitHandle()


@DRIVER.on_startup
async def check_limit_db():
    limit_data.pool = database.pool
    logger.opt(colors=True).info(f"<green>xiuxian_limit数据库已连接!</green>")
    logger.opt(colors=True).info(f"<green>检查xiuxian_limit数据库完整性中</green>")
    await limit_data.check_data()
    logger.opt(colors=True).info(f"<green>检查xiuxian_limit数据库完整性成功</green>")
