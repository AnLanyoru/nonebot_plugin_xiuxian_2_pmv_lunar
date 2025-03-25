import datetime
import json
import random
from datetime import timedelta
from pathlib import Path

import asyncpg

from nonebot import on_command, require
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent
)
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .. import DRIVER
from ..xiuxian_database.database_connect import database
from ..xiuxian_utils.clean_utils import three_md, number_to, main_md, zips, get_args_num, simple_md
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import check_user
from ..xiuxian_utils.xiuxian2_handle import sql_message, xiuxian_impart

active_daily_reset = require("nonebot_plugin_apscheduler").scheduler
with open(Path(__file__).parent / '灯谜.json', "r", encoding="UTF-8") as f:
    data = f.read()
yuan_xiao_problem = json.loads(data)

YUAN_XIAO_NUM_LIST = [3, 3, 3, 3, 2, 2, 2, 1, 1, 1]


def get_num_yuan_xiao():
    return random.choice(YUAN_XIAO_NUM_LIST)


async def yuan_xiao_send_impart_stone(user_id):
    num = get_num_yuan_xiao()
    await xiuxian_impart.update_stone_num(impart_num=num, user_id=user_id, type_=1)
    return f'思恋结晶 {num}个', {}


async def yuan_xiao_send_stam_tool(user_id):
    """复元水 3-1个"""
    num = get_num_yuan_xiao()
    item_id = 610004
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


async def yuan_xiao_send_work(user_id):
    """悬赏衙令 3-1个"""
    num = get_num_yuan_xiao()
    item_id = 640001
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


async def yuan_xiao_send_jiao_zi(user_id):
    """汤圆 3-1个"""
    num = get_num_yuan_xiao()
    item_id = 25011
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


yuan_xiao_gift_list = {'思恋结晶': yuan_xiao_send_impart_stone,
                       '复元水': yuan_xiao_send_stam_tool,
                       '悬赏衙令': yuan_xiao_send_work,
                       '汤圆': yuan_xiao_send_jiao_zi}

yuan_xiao_daily_gift_list = {1: {'msg':
                                     '复元水3个，出货！\r刷新令 3个\r',
                                 'items':
                                     {640001: 3, 610004: 3}},
                             2: {'msg':
                                     '复元水3个，出货！\r刷新令 3个\r',
                                 'items':
                                     {640001: 3, 610004: 3}},
                             3: {'msg':
                                     '无敌的聚灵阵一盏。\r复元水3个，出货！\r刷新令 3个\r',
                                 'items':
                                     {2507: 1, 640001: 3, 610004: 3}},
                             4: {'msg':
                                     '王道神兵一把。\r复元水3个，出货！\r刷新令 3个\r',
                                 'items':
                                     {444001: 1, 640001: 3, 610004: 3}},
                             5: {'msg':
                                     '王道神兵一把。\r复元水3个，出货！\r刷新令 3个\r',
                                 'items':
                                     {443001: 1, 640001: 3, 610004: 3}}}


# 创建一个临时活动数据库
@DRIVER.on_startup
async def yuan_xiao_prepare():
    async with database.pool.acquire() as conn:
        try:
            await conn.execute(f"select count(1) from yuan_xiao_temp")
        except asyncpg.exceptions.UndefinedTableError:
            await conn.execute(f"""CREATE TABLE "yuan_xiao_temp" (
                "user_id" bigint PRIMARY KEY,
                "daily_sign" smallint DEFAULT 0,
                "today_answered" smallint DEFAULT 0,
                "all_sign_num" smallint DEFAULT 0,
                "all_pass_problem_num" smallint DEFAULT 0,
                "get_problem_time" timestamp,
                "now_problem" json
                );""")


async def get_user_yuan_xiao_info(user_id: int) -> dict:
    user_yuan_xiao_info = await database.select(table='yuan_xiao_temp',
                                                where={'user_id': user_id})
    if not user_yuan_xiao_info:
        insert_data = {'user_id': user_id}
        await database.insert(table='yuan_xiao_temp', create_column=0, **insert_data)
        user_yuan_xiao_info = {
            "user_id": user_id,
            "daily_sign": 0,
            "today_answered": 0,
            "all_sign_num": 0,
            "all_pass_problem_num": 0,
            "get_problem_time": None,
            "now_problem": None}
    return user_yuan_xiao_info


async def update_user_yuan_xiao_info(user_id: int, user_yuan_xiao_info: dict):
    await database.update(table='yuan_xiao_temp',
                          where={'user_id': user_id},
                          **user_yuan_xiao_info)


async def get_yuan_xiao_top():
    """挑战排行"""
    sql = (f"SELECT "
           f"(SELECT max(user_name) FROM user_xiuxian WHERE user_xiuxian.user_id = yuan_xiao_temp.user_id) "
           f"as user_name, "
           f"all_pass_problem_num "
           f"FROM yuan_xiao_temp "
           f"ORDER BY all_pass_problem_num DESC "
           f"limit 100")
    async with database.pool.acquire() as db:
        result = await db.fetch(sql)
        result_all = [zips(**result_per) for result_per in result]
        return result_all


# 活动日常刷新
@active_daily_reset.scheduled_job("cron", hour=0, minute=0)
async def active_daily_reset_():
    await database.sql_execute("update yuan_xiao_temp set daily_sign=0")


new_active_menu = on_command("元宵", priority=9, permission=GROUP, block=True)
yuan_xiao_gift_get = on_command("拆福袋", aliases={'使用二零二五元宵福包'}, priority=1, permission=GROUP, block=True)
active_daily_gift_get = on_command("愚人节签到", priority=8, permission=GROUP, block=True)
time_set_new_active = on_command('活动刷新', priority=15, permission=SUPERUSER, block=True)
yuan_xiao_problem_get = on_command("获取灯谜", priority=8, permission=GROUP, block=True)
yuan_xiao_problem_answer = on_command("答题", priority=8, permission=GROUP, block=True)
yuan_xiao_problem_menu = on_command("元宵灯谜", priority=8, permission=GROUP, block=True)
yuan_xiao_problem_reset = on_command("灯谜重载", priority=8, permission=SUPERUSER, block=True)
yuan_xiao_problem_top = on_command("猜谜排行", priority=8, permission=GROUP, block=True)

YUAN_XIAO_START_TIME = datetime.date(year=2025, month=2, day=10)


@yuan_xiao_problem_reset.handle(parameterless=[Cooldown()])
async def yuan_xiao_problem_reset_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """灯谜重载"""
    global yuan_xiao_problem
    with open(Path(__file__).parent / '灯谜.json', "r", encoding="UTF-8") as file_data:
        problem_data = file_data.read()
    yuan_xiao_problem = json.loads(problem_data)
    msg = '重载完成！'
    await bot.send(event=event, message=msg)
    await yuan_xiao_problem_reset.finish()


@yuan_xiao_problem_top.handle(parameterless=[Cooldown()])
async def yuan_xiao_problem_top_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """猜谜排行"""
    page = get_args_num(args, 1, default=1)
    lt_rank = await get_yuan_xiao_top()
    long_rank = len(lt_rank)
    page_all = (long_rank // 20) + 1 if long_rank % 20 != 0 else long_rank // 20  # 总页数
    if page_all < page != 1:
        msg = f"猜谜排行榜没有那么广阔！！！"
        await bot.send(event=event, message=msg)
        await yuan_xiao_problem_top.finish()
    if long_rank != 0:
        # 获取页数物品数量
        item_num = page * 20 - 20
        item_num_end = item_num + 20
        lt_rank = lt_rank[item_num:item_num_end]
        top_msg = f"✨灯谜解密排行TOP{item_num_end}✨"
        msg = ''
        num = item_num
        for i in lt_rank:
            i = list(i.values())
            num += 1
            msg += f"第{num}位 {i[0]} 共成功解答:{number_to(i[1])}题\r"
        msg += f"第 {page}/{page_all} 页"
        msg = main_md(top_msg, msg,
                      '主菜单', '元宵',
                      '元宵灯谜', '元宵灯谜',
                      '拆福袋', '拆福袋',
                      '其他排行榜', '排行榜')
    else:
        msg = f"该排行榜空空如也！"
    await bot.send(event=event, message=msg)
    await yuan_xiao_problem_top.finish()


@yuan_xiao_problem_answer.handle(parameterless=[Cooldown(cd_time=5)])
async def yuan_xiao_problem_answer_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """答题"""
    now_day = datetime.date.today()
    if not (YUAN_XIAO_START_TIME < now_day):
        msg = "活动尚未开始！！"
        await bot.send(event=event, message=msg)
        await yuan_xiao_problem_answer.finish()

    if not (datetime.date(year=2025, month=2, day=16) > now_day):
        msg = "活动已结束！！"
        await bot.send(event=event, message=msg)
        await yuan_xiao_problem_answer.finish()

    user_info = await check_user(event)
    user_id = user_info['user_id']
    user_new_year_info = await get_user_yuan_xiao_info(user_id)
    user_problem = user_new_year_info['now_problem']
    user_name = user_info['user_name']
    if not user_problem:
        msg = f"{user_name}道友暂时没有灯谜需要解答！！\r"
        msg = three_md(msg, "获取灯谜", "获取灯谜", "\r —— 答题成功将获得福袋奖励！！\r",
                       "主菜单", "元宵", "\r —— 查看全部元宵活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取奖励！！")
        await bot.send(event=event, message=msg)
        await yuan_xiao_problem_answer.finish()

    problem = json.loads(user_new_year_info['now_problem'])
    answer = args.extract_plain_text()
    start_time = user_new_year_info['get_problem_time']
    now_datetime = datetime.datetime.now()
    pass_time: timedelta = now_datetime - start_time
    if pass_time.seconds > 60:
        msg = f"{user_name}道友的灯谜超时了哦，很遗憾本次不能给你奖励了\r"
        user_new_year_info['now_problem'] = None
        await update_user_yuan_xiao_info(user_id, user_new_year_info)
        msg = three_md(msg, "获取灯谜", "获取灯谜", "\r —— 答题成功将获得福袋奖励！！\r",
                       "主菜单", "元宵", "\r —— 查看全部元宵活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取奖励！！")
        await bot.send(event=event, message=msg)
        await yuan_xiao_problem_answer.finish()

    if answer not in problem['答案']:
        msg = f"{user_name}道友的答案不对哦，很遗憾本次不能给你奖励了\r"
        user_new_year_info['now_problem'] = None
        await update_user_yuan_xiao_info(user_id, user_new_year_info)
        msg = three_md(msg, "获取灯谜", "获取灯谜", "\r —— 答题成功将获得福袋奖励！！\r",
                       "主菜单", "元宵", "\r —— 查看全部元宵活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取奖励！！")
        await bot.send(event=event, message=msg)
        await yuan_xiao_problem_answer.finish()

    user_new_year_info['now_problem'] = None
    user_new_year_info['all_pass_problem_num'] += 1
    await update_user_yuan_xiao_info(user_id, user_new_year_info)
    await sql_message.send_item(user_id, {700002: 1}, is_bind=1)
    msg = (f"恭喜{user_name}道友成功答对灯谜！！\r"
           f"获得了：元宵福袋 1个\r"
           f" —— 快去拆福袋看看里面有什么东西吧！！\r")
    msg = three_md(msg, "继续答题", "获取灯谜", "\r —— 答题成功将获得福袋奖励！！\r",
                   "猜谜排行", "猜谜排行", "\r —— 查看元宵猜谜排行！！\r",
                   "拆福袋", "拆福袋", "\r —— 打开福袋获取奖励！！")
    await bot.send(event=event, message=msg)
    await yuan_xiao_problem_answer.finish()


@yuan_xiao_problem_get.handle(parameterless=[Cooldown(cd_time=5)])
async def yuan_xiao_problem_get_(bot: Bot, event: GroupMessageEvent):
    """获取谜题"""
    now_day = datetime.date.today()
    if not (YUAN_XIAO_START_TIME < now_day):
        msg = "活动尚未开始！！"
        await bot.send(event=event, message=msg)
        await yuan_xiao_problem_get.finish()

    if not (datetime.date(year=2025, month=2, day=16) > now_day):
        msg = "活动已结束！！"
        await bot.send(event=event, message=msg)
        await yuan_xiao_problem_get.finish()

    user_info = await check_user(event)
    user_id = user_info['user_id']
    user_new_year_info = await get_user_yuan_xiao_info(user_id)
    user_problem = user_new_year_info['now_problem']
    user_name = user_info['user_name']
    if user_problem:
        problem = json.loads(user_problem)
        msg = (f"道友已经有谜题啦！！\r"
               f"{user_name}道友的谜题：\r"
               f"{problem['题目']}\r")
        msg = three_md(msg, "答题", "答题", "\r —— 答题成功将获得福袋奖励！！\r",
                       "主菜单", "元宵", "\r —— 查看全部元宵活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取奖励！！")
        await bot.send(event=event, message=msg)
        await yuan_xiao_problem_get.finish()
    if user_new_year_info['today_answered'] > 4:
        msg = f"道友今天已经尝试了够多的灯谜啦！！\r"
        msg = three_md(msg, "查看日常", "日常中心", "\r —— 看看今日日常吧！！\r",
                       "主菜单", "元宵", "\r —— 查看全部元宵活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取奖励！！")
        await bot.send(event=event, message=msg)
        await yuan_xiao_problem_get.finish()

    problem = random.choice(yuan_xiao_problem)
    user_new_year_info['now_problem'] = json.dumps(problem)
    user_new_year_info['today_answered'] += 1
    user_new_year_info['get_problem_time'] = datetime.datetime.now()
    await update_user_yuan_xiao_info(user_id, user_new_year_info)
    msg = (f"{user_name}道友的谜题：\r"
           f"{problem['题目']}\r")
    msg = three_md(msg, "答题", "答题", "\r —— 答题成功将获得福袋奖励！！\r",
                   "主菜单", "元宵", "\r —— 查看全部元宵活动！！\r",
                   "拆福袋", "拆福袋", "\r —— 打开福袋获取奖励！！")
    await bot.send(event=event, message=msg)
    await yuan_xiao_problem_get.finish()


@yuan_xiao_problem_menu.handle(parameterless=[Cooldown(cd_time=5)])
async def yuan_xiao_problem_menu_(bot: Bot, event: GroupMessageEvent):
    """猜谜活动菜单！！"""
    now_day = datetime.date.today()
    if not (YUAN_XIAO_START_TIME < now_day):
        msg = "活动尚未开始！！"
        await bot.send(event=event, message=msg)
        await yuan_xiao_problem_menu.finish()

    if not (datetime.date(year=2025, month=2, day=16) > now_day):
        msg = "活动已结束！！"
        await bot.send(event=event, message=msg)
        await yuan_xiao_problem_menu.finish()

    user_info = await check_user(event)

    user_name = user_info['user_name']
    msg = (f"祝{user_name}道友元宵快乐！！\r"
           f"元宵灯谜规则介绍：\r"
           f"元宵灯谜难度为炼狱难度:\r"
           f"每题限时60s，每题仅有一次答题机会。\r"
           f"答错后直接失去奖励机会\r"
           f"每日有5次答题机会\r")
    msg = three_md(msg, "猜灯谜", "获取灯谜", "\r —— 参加答题并答题正确可获得福袋奖励！！\r",
                   "主菜单", "元宵", "\r —— 查看全部元宵活动！！\r",
                   "拆福袋", "拆福袋", "\r —— 打开福袋获取奖励！！\r"
                                       "活动时间 2月12日——15日！")
    await bot.send(event=event, message=msg)
    await yuan_xiao_problem_menu.finish()


@yuan_xiao_gift_get.handle(parameterless=[Cooldown(cd_time=5)])
async def yuan_xiao_gift_get_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """二零二五元宵福包"""

    user_info = await check_user(event)
    user_id = user_info['user_id']
    user_name = user_info['user_name']
    new_year_gift_info = await sql_message.get_item_by_good_id_and_user_id(user_id, 700002)
    if not new_year_gift_info:
        msg = f"道友没有二零二五元宵福包呢！！\r"
        msg = simple_md(msg,
                        "查看福包奖励", "查二零二五元宵福包",
                        "\r —— 查看所有该福包内含奖励"
                        "\r如果有未使用的新春福包，请发送 使用二零二五新春福包 哦！")
        await bot.send(event=event, message=msg)
        await yuan_xiao_gift_get.finish()
    if (gift_num := new_year_gift_info.get('goods_num')) <= 0:
        msg = f"道友的二零二五元宵福包不够呢！！\r"
        msg = simple_md(msg, "查看福包奖励",
                        "查二零二五元宵福包",
                        "\r —— 查看所有该福包内含奖励"
                        "\r如果有未使用的新春福包，请发送 使用二零二五新春福包 哦！")
        await bot.send(event=event, message=msg)
        await yuan_xiao_gift_get.finish()

    all_gift = list(yuan_xiao_gift_list.keys())
    random.shuffle(all_gift)
    msg_list = []
    item_send = {}
    gift_type = all_gift[0]
    msg_per, item_dict = await yuan_xiao_gift_list[gift_type](user_id)
    item_send.update(item_dict)
    msg_list.append(msg_per)
    await sql_message.send_item(user_id, item_send, 1)
    await sql_message.update_back_j(user_id, 700002, 1, 2)
    msg = f"恭喜{user_name}道友打开福包获取了以下奖励：\r" + '\r'.join(msg_list) + '\r'
    msg = simple_md(msg,
                    f"继续拆(余剩{gift_num - 1})",
                    "拆福袋",
                    "！！")
    await bot.send(event=event, message=msg)
    await yuan_xiao_gift_get.finish()


@time_set_new_active.handle(parameterless=[Cooldown(cd_time=5)])
async def time_set_new_year_(bot: Bot, event: GroupMessageEvent):
    """当前活动重载！！"""

    user_info = await check_user(event)
    await database.sql_execute("update yuan_xiao_temp set daily_sign=0, today_answered=0")
    msg = f"活动重置！！"
    await bot.send(event=event, message=msg)
    await time_set_new_active.finish()


@active_daily_gift_get.handle(parameterless=[Cooldown(cd_time=5)])
async def yuan_xiao_daily_gift_get_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """元宵签到"""

    now_day = datetime.date.today()
    if not (datetime.date(year=2025, month=3, day=25) < now_day):
        msg = "活动尚未开始！！"
        await bot.send(event=event, message=msg)
        await active_daily_gift_get.finish()

    if not (datetime.date(year=2025, month=4, day=8) > now_day):
        msg = "活动已结束！！"
        await bot.send(event=event, message=msg)
        await active_daily_gift_get.finish()

    user_info = await check_user(event)
    user_id = user_info['user_id']
    user_name = user_info['user_name']
    user_yuan_xiao_info = await get_user_yuan_xiao_info(user_id)
    is_sign = user_yuan_xiao_info['daily_sign']
    if is_sign:
        msg = simple_md(f"道友今天已经",
                        "签到", "愚人节签到", "过啦！！")
        await bot.send(event=event, message=msg)
        await active_daily_gift_get.finish()

    all_sign_num = user_yuan_xiao_info['all_sign_num']
    if all_sign_num > 4:
        msg = simple_md(f"道友已经完成了所有",
                        "签到", "愚人节签到", "啦！！")
        await bot.send(event=event, message=msg)
        await active_daily_gift_get.finish()
    user_yuan_xiao_info['all_sign_num'] += 1
    user_yuan_xiao_info['daily_sign'] = 1
    gift_today = yuan_xiao_daily_gift_list[user_yuan_xiao_info['all_sign_num']]
    item_send = gift_today['items']
    item_msg = gift_today['msg']
    await sql_message.send_item(user_id, item_send, 1)
    await update_user_yuan_xiao_info(user_id, user_yuan_xiao_info)
    msg = simple_md(f"@{user_name}道友\r今天是道友第{all_sign_num + 1}次",
                    "愚人节签到", "愚人节签到",
                    f"\r获取了以下奖励：\r" + item_msg)
    await bot.send(event=event, message=msg)
    await active_daily_gift_get.finish()


@new_active_menu.handle(parameterless=[Cooldown(cd_time=5)])
async def new_active_menu_(bot: Bot, event: GroupMessageEvent):
    """元宵活动菜单！！"""

    user_info = await check_user(event)
    user_id = user_info['user_id']
    user_name = user_info['user_name']
    user_yuan_xiao_info = await get_user_yuan_xiao_info(user_id)
    new_year_pray_num = user_yuan_xiao_info['daily_sign']
    today_answered = user_yuan_xiao_info['today_answered']
    msg = (f"祝{user_name}道友元宵快乐！！\r"
           f"进行中的元宵活动：\r")
    msg = three_md(msg, f"元宵灯谜(今日{today_answered}/5)", "元宵灯谜",
                   "\r —— 参加答题获得福袋奖励！！\r",
                   f"元宵签到(今日{new_year_pray_num}/1)", "元宵签到",
                   "\r —— 每日签到获得奖励！！\r",
                   f"查看日常", "日常中心",
                   "\r灯谜活动开放时间：2月12日-15日，签到活动开放时间：2月12日-20日")
    await bot.send(event=event, message=msg)
    await new_active_menu.finish()
