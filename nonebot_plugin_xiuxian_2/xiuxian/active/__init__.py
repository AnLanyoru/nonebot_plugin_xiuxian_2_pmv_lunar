import json
import random
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
from ..xiuxian_utils.clean_utils import three_md
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import check_user
from ..xiuxian_utils.xiuxian2_handle import sql_message, xiuxian_impart

active_daily_reset = require("nonebot_plugin_apscheduler").scheduler
all_problems = [{"题目": "我国的全称是叫什么答案七个字", "答案": ["中华人民共和国"]},
                {"题目": "新中国成立于多少年答案四个数字", "答案": ["1949"]},
                {"题目": "改革开放是哪一年答案四个数字", "答案": ["1978"]},
                {"题目": "我国禁枪是哪一年答案四个数字", "答案": ["1996"]},
                {"题目": "前往灵界需要什么境界答案三个字", "答案": ["天人境"]},
                {"题目": "前往仙界需要什么境界答案五个字", "答案": ["登仙境后期"]},
                {"题目": "凡界塔一共有多少层答案两个数字或者汉字", "答案": ["40", "四十"]},
                {"题目": "什么物品能增加240体力值答案三个字", "答案": ["复元水"]},
                {"题目": "元朝一共统治了多少年答案两个数字", "答案": ["97"]},
                {"题目": "日本投降于多少年答案四个数字", "答案": ["1945"]},
                {"题目": "日本投降赔偿我国多少美金答案三个数字", "答案": ["216"]},
                {"题目": "我国有多少个少数民族答案两个数字", "答案": ["55"]},
                {"题目": "我国由多少个民族组成答案两个数字", "答案": ["56"]}].copy()

NUM_LIST = [3, 3, 3, 3, 6, 6, 6, 8, 8, 10]


def get_num_new_year():
    return random.choice(NUM_LIST)


async def send_impart_stone(user_id):
    num = get_num_new_year()
    await xiuxian_impart.update_stone_num(impart_num=num, user_id=user_id, type_=1)
    return f'思恋结晶 {num}个', {}


async def send_buff_elixir(user_id):
    num = get_num_new_year()
    elixir_list = [2035, 2026, 2015]
    elixir_id = random.choice(elixir_list)
    elixir_info = items.get_data_by_item_id(elixir_id)
    elixir_name = elixir_info['name']
    return f"{elixir_name} {num}个", {elixir_id: num}


async def send_stam_tool(user_id):
    """复元水 3-10个"""
    num = get_num_new_year()
    item_id = 610004
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


async def send_work(user_id):
    """悬赏衙令 3-10个"""
    num = get_num_new_year()
    item_id = 640001
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


async def send_money(user_id):
    """金元宝 3-10个"""
    num = random.choice([3, 3, 3, 3, 3, 3, 6, 6, 8, 10])
    item_id = 990001
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


async def send_jiao_zi(user_id):
    """饺子 3-10个"""
    num = get_num_new_year()
    item_id = 25012
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


gift_list = {'思恋结晶': send_impart_stone,
             '增益丹药': send_buff_elixir,
             '复元水': send_stam_tool,
             '悬赏衙令': send_work,
             '金元宝': send_money,
             '饺子': send_jiao_zi}

daily_gift_list = {1: {'msg':
                           '年夜饭一桌，年年有余！\r福包 1个\r',
                       'items':
                           {610005: 1, 700001: 1}},
                   2: {'msg':
                           '金元宝十个，金银满堂！\r福包 1个\r',
                       'items':
                           {990001: 10, 700001: 1}},
                   3: {'msg':
                           '汤圆十个，团团圆圆！\r福包 1个\r',
                       'items':
                           {25011: 10, 700001: 1}},
                   4: {'msg':
                           '饺子十个，平安如意！\r福包 2个\r',
                       'items':
                           {25012: 10, 700001: 2}},
                   5: {'msg':
                           '复元水五瓶，精力充沛！\r福包 2个\r',
                       'items':
                           {610004: 5, 700001: 2}},
                   6: {'msg':
                           '悬赏衙令五个，诸事无阻！\r福包 2个\r',
                       'items':
                           {640001: 5, 700001: 2}},
                   7: {'msg':
                           '福包五个，五福临门！！\r',
                       'items':
                           {700001: 5}}}


# 创建一个临时活动数据库
@DRIVER.on_startup
async def new_year_prepare():
    async with database.pool.acquire() as conn:
        try:
            await conn.execute(f"select count(1) from new_year_temp")
        except asyncpg.exceptions.UndefinedTableError:
            await conn.execute(f"""CREATE TABLE "new_year_temp" (
                "user_id" bigint PRIMARY KEY,
                "daily_sign" smallint DEFAULT 0,
                "fight_num" smallint DEFAULT 0,
                "today_answered" smallint DEFAULT 0,
                "all_sign_num" smallint DEFAULT 0,
                "now_problem" json,
                "fight_damage" numeric DEFAULT 0
                );""")


async def get_user_new_year_info(user_id: int) -> dict:
    user_new_year_info = await database.select(table='new_year_temp',
                                               where={'user_id': user_id})
    if not user_new_year_info:
        data = {'user_id': user_id}
        await database.insert(table='new_year_temp', create_column=0, **data)
        user_new_year_info = {
            "user_id": user_id,
            "daily_sign": 0,
            "fight_num": 0,
            "today_answered": 0,
            "all_sign_num": 0,
            "now_problem": None,
            "fight_damage": 0, }
    return user_new_year_info


async def update_user_new_year_info(user_id: int, user_new_year_info: dict):
    await database.update(table='new_year_temp',
                          where={'user_id': user_id},
                          **user_new_year_info)


# 活动日常刷新
@active_daily_reset.scheduled_job("cron", hour=0, minute=10)
async def active_daily_reset_():
    await database.sql_execute("update new_year_temp set daily_sign=0, fight_num=0, today_answered=0")


new_year_active_menu = on_command("新春", priority=9, permission=GROUP, block=True)
new_year_guess_menu = on_command("猜谜活动菜单", priority=9, permission=GROUP, block=True)
new_year_guess_get = on_command("获取谜题", priority=9, permission=GROUP, block=True)
new_year_guess_answer = on_command("答题", priority=9, permission=GROUP, block=True)
new_year_gift_get = on_command("拆福袋", priority=9, permission=GROUP, block=True)
new_year_daily_gift_get = on_command("新春祈愿", priority=8, permission=GROUP, block=True)
new_year_fight = on_command("年兽菜单", priority=9, permission=GROUP, block=True)

time_set_new_year = on_command('逆转新春', priority=15, permission=SUPERUSER, block=True)


@time_set_new_year.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def time_set_new_year_(bot: Bot, event: GroupMessageEvent):
    """春节活动重载！！"""

    _, user_info, _ = await check_user(event)
    await database.sql_execute("update new_year_temp set daily_sign=0, fight_num=0, today_answered=0")
    msg = f"又是一年好新春！！"
    await bot.send(event=event, message=msg)
    await time_set_new_year.finish()


@new_year_daily_gift_get.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_daily_gift_get_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """新春签到"""

    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']
    user_name = user_info['user_name']
    user_new_year_info = await get_user_new_year_info(user_id)
    is_sign = user_new_year_info['daily_sign']
    if is_sign:
        msg = f"道友今天已经签到过啦，快去参与其他新春活动吧！！\r"
        msg = three_md(msg, "查看福包奖励", "查二零二五新春福包", "\r - 查看所有福包内含奖励！！\r",
                       "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r - 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_daily_gift_get.finish()

    all_sign_num = user_new_year_info['all_sign_num']
    if all_sign_num > 6:
        msg = f"道友已经完成全部签到啦，新春快乐！！新的一年里顺顺利利，开开心心！！\r"
        msg = three_md(msg, "查看福包奖励", "查二零二五新春福包", "\r - 查看所有福包内含奖励！！\r",
                       "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r - 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_daily_gift_get.finish()
    user_new_year_info['all_sign_num'] += 1
    user_new_year_info['daily_sign'] = 1
    gift_today = daily_gift_list[user_new_year_info['all_sign_num']]
    item_send = gift_today['items']
    item_msg = gift_today['msg']
    await sql_message.send_item(user_id, item_send, 1)
    await update_user_new_year_info(user_id, user_new_year_info)
    msg = f"{user_name}道友新年快乐！！\r今天是道友第{all_sign_num + 1}次新春祈愿\r获取了以下奖励：\r" + item_msg
    msg = three_md(msg, "查看驱逐年兽排行", "年兽伤害排行", "\r - 查看为驱逐年兽做出巨大贡献的玩家！！\r",
                   "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                   f"去拆福袋", "拆福袋", "\r - 打开福袋获取丰厚奖励！！")
    await bot.send(event=event, message=msg)
    await new_year_daily_gift_get.finish()


@new_year_gift_get.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_gift_get_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """拆福包"""

    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']
    user_name = user_info['user_name']
    new_year_gift_info = await sql_message.get_item_by_good_id_and_user_id(user_id, 700001)
    if not new_year_gift_info:
        msg = f"道友还没有福包呢，去参与新春活动获取一些吧！！\r"
        msg = three_md(msg, "查看福包奖励", "查二零二五新春福包", "\r - 查看所有福包内含奖励！！\r",
                       "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r - 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_gift_get.finish()
    if (gift_num := new_year_gift_info.get('goods_num')) <= 0:
        msg = f"道友的福包不够呢，去参与新春活动多获取一些吧！！\r"
        msg = three_md(msg, "查看福包奖励", "查二零二五新春福包", "\r - 查看所有福包内含奖励！！\r",
                       "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r - 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_gift_get.finish()

    all_gift = list(gift_list.keys())
    random.shuffle(all_gift)
    msg_list = []
    item_send = {}
    for gift_type in all_gift[:3]:
        msg_per, item_dict = await gift_list[gift_type](user_id)
        item_send.update(item_dict)
        msg_list.append(msg_per)
    await sql_message.send_item(user_id, item_send, 1)
    await sql_message.update_back_j(user_id, 700001, 1, 2)
    msg = f"恭喜{user_name}道友打开福包获取了以下奖励：\r" + '\r'.join(msg_list) + '\r'
    msg = three_md(msg, "查看驱逐年兽排行", "年兽伤害排行", "\r - 查看为驱逐年兽做出巨大贡献的玩家！！\r",
                   "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                   f"继续拆福袋(余剩{gift_num - 1})", "拆福袋", "\r - 打开福袋获取丰厚奖励！！")
    await bot.send(event=event, message=msg)
    await new_year_gift_get.finish()


@new_year_guess_answer.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_guess_answer_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """答题"""

    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']
    user_new_year_info = await get_user_new_year_info(user_id)
    user_problem = user_new_year_info['now_problem']
    user_name = user_info['user_name']
    if not user_problem:
        msg = f"{user_name}道友暂时没有谜题需要解答！！\r"
        msg = three_md(msg, "获取题目", "获取题目", "\r - 答题成功将获得福袋奖励！！\r",
                       "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r - 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_guess_answer.finish()

    problem = json.loads(user_new_year_info['now_problem'])
    answer = args.extract_plain_text()
    if answer not in problem['答案']:
        msg = f"{user_name}道友的答案不对哦，道友再好好猜猜看吧\r"
        msg = three_md(msg, "继续答题", "答题", "\r - 答题成功将获得福袋奖励！！\r",
                       "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r - 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_guess_answer.finish()

    user_new_year_info['now_problem'] = None
    await update_user_new_year_info(user_id, user_new_year_info)
    await sql_message.send_item(user_id, {700001: 1}, is_bind=1)
    msg = (f"恭喜{user_name}道友成功答对谜题！！\r"
           f"获得了：福袋 1个\r"
           f" - 快去拆福袋看看里面有什么好东西吧！！\r")
    msg = three_md(msg, "继续答题", "获取题目", "\r - 答题成功将获得福袋奖励！！\r",
                   "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                   "拆福袋", "拆福袋", "\r - 打开福袋获取丰厚奖励！！")
    await bot.send(event=event, message=msg)
    await new_year_guess_answer.finish()


@new_year_guess_get.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_guess_get_(bot: Bot, event: GroupMessageEvent):
    """获取谜题"""

    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']
    user_new_year_info = await get_user_new_year_info(user_id)
    user_problem = user_new_year_info['now_problem']
    user_name = user_info['user_name']
    if user_problem:
        problem = json.loads(user_problem)
        msg = (f"道友已经有谜题啦！！\r"
               f"{user_name}道友的谜题：\r"
               f"{problem['题目']}\r")
        msg = three_md(msg, "答题", "答题", "\r - 答题成功将获得福袋奖励！！\r",
                       "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r - 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_guess_get.finish()
    if user_new_year_info['today_answered'] > 2:
        msg = f"道友今天已经答了够多的谜题啦！！\r去看看别的活动吧"
        msg = three_md(msg, "驱逐年兽", "年兽菜单", "\r - 答题成功将获得福袋奖励！！\r",
                       "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r - 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_guess_get.finish()

    problem = random.choice(all_problems)
    user_new_year_info['now_problem'] = json.dumps(problem)
    user_new_year_info['today_answered'] += 1
    await update_user_new_year_info(user_id, user_new_year_info)
    msg = (f"{user_name}道友的谜题：\r"
           f"{problem['题目']}\r")
    msg = three_md(msg, "答题", "答题", "\r - 答题成功将获得福袋奖励！！\r",
                   "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                   "拆福袋", "拆福袋", "\r - 打开福袋获取丰厚奖励！！")
    await bot.send(event=event, message=msg)
    await new_year_guess_get.finish()


@new_year_guess_menu.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_guess_menu_(bot: Bot, event: GroupMessageEvent):
    """猜谜活动菜单！！"""

    _, user_info, _ = await check_user(event)

    user_name = user_info['user_name']
    msg = (f"祝{user_name}道友新春快乐！！\r"
           f"新春猜谜菜单：\r")
    msg = three_md(msg, "开始猜谜", "获取谜题", "\r - 参加答题获得福袋奖励！！\r",
                   "主菜单", "新春菜单", "\r - 查看全部新春活动！！\r",
                   "拆福袋", "拆福袋", "\r - 打开福袋获取丰厚奖励！！\r"
                                       "新春活动于大年初一开放，初七过后结束，祈愿签到活动额外持续七日！")
    await bot.send(event=event, message=msg)
    await new_year_guess_menu.finish()


@new_year_active_menu.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_active_menu_(bot: Bot, event: GroupMessageEvent):
    """春节活动菜单！！"""

    _, user_info, _ = await check_user(event)

    user_name = user_info['user_name']
    msg = (f"祝{user_name}道友新春快乐！！\r"
           f"进行中的新春活动：\r")
    msg = three_md(msg, "新春猜谜", "猜谜活动菜单", "\r - 参加答题获得福袋奖励！！\r",
                   "驱逐年兽", "年兽菜单", "\r - 共同击退年兽获取丰厚奖励！！\r",
                   "新春祈愿", "新春祈愿", "\r - 每日签到获得丰厚奖励！！\r"
                                           "新春活动于大年初一开放，初七过后结束，祈愿签到活动额外持续七日！")
    await bot.send(event=event, message=msg)
    await new_year_active_menu.finish()
