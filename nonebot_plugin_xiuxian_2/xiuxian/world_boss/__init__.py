import json
import operator
import random
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

from .world_boss_database import update_user_world_boss_info, get_user_world_boss_info
from .. import DRIVER
from ..user_data_handle import UserBuffHandle
from ..xiuxian_config import convert_rank
from ..xiuxian_database.database_connect import database
from ..xiuxian_impart.impart_uitls import impart_check
from ..xiuxian_place import place
from ..xiuxian_utils.clean_utils import three_md, msg_handler, number_to, main_md, zips, get_args_num, simple_md, \
    get_num_from_str
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown, UserCmdLock
from ..xiuxian_utils.player_fight import boss_fight
from ..xiuxian_utils.utils import check_user, check_user_type
from ..xiuxian_utils.xiuxian2_handle import sql_message

boss_daily_reset = require("nonebot_plugin_apscheduler").scheduler
boss_names = [
    "九寒",
    "精卫",
    "少姜",
    "陵光",
    "莫女",
    "术方",
    "卫起",
    "血枫",
    "以向",
    "砂鲛",
    "鲲鹏",
    "天龙",
    "莉莉丝",
    "霍德尔",
    "历飞雨",
    "神风王",
    "衣以候",
    "金凰儿",
    "元磁道人",
    "外道贩卖鬼",
    "散发着威压的尸体"
]  # 生成的Boss名字
boss_name_now = random.choice(boss_names)

with open(Path(__file__).parent / 'world_boss_shop.json', "r", encoding="UTF-8") as file_data:
    problem_data = file_data.read()
WORLD_BOSS_SHOP: dict[int, dict] = {int(item_no): item_info for item_no, item_info in json.loads(problem_data).items()}


# 创建一个世界boss数据库
@DRIVER.on_startup
async def world_boss_prepare():
    async with database.pool.acquire() as conn:
        try:
            await conn.execute(f"select count(1) from world_boss")
        except asyncpg.exceptions.UndefinedTableError:
            await conn.execute(f"""CREATE TABLE "world_boss" (
                "user_id" bigint PRIMARY KEY,
                "fight_num" smallint DEFAULT 0,
                "world_id" smallint DEFAULT 0,
                "world_point" bigint DEFAULT 0,
                "fight_damage" numeric DEFAULT 0
                );""")


async def get_world_boss_battle_info(user_id):
    """获取Boss战事件的内容"""
    player = await UserBuffHandle(user_id).get_user_fight_info()
    impart_data_draw = await impart_check(user_id)
    player['道号'] = player['user_name']
    player['气血'] = player['fight_hp']
    player['攻击'] = player['atk'] * (1 + impart_data_draw['boss_atk'])
    player['真元'] = player['fight_mp']

    world_boss_fight_hp = player['max_hp'] * 100
    boss_info = {
        "name": boss_name_now,
        "气血": world_boss_fight_hp,
        "总血量": world_boss_fight_hp,
        "攻击": 0,
        "真元": 0,
        "jj": f"{convert_rank()[1][65][:3]}",
        'stone': 1,
        'defence': 0.05
    }

    result, _, final_boss_info, _ = await boss_fight(player, boss_info)  # 未开启，1不写入，2写入

    return result, final_boss_info


async def get_world_boss_fight_top(world_id):
    """挑战排行"""
    sql = (f"SELECT "
           f"(SELECT max(user_name) FROM user_xiuxian WHERE user_xiuxian.user_id = world_boss.user_id) "
           f"as user_name, "
           f"fight_damage "
           f"FROM world_boss "
           f"WHERE world_id=$1 "
           f"ORDER BY fight_damage DESC "
           f"limit 100")
    async with database.pool.acquire() as db:
        result = await db.fetch(sql, world_id)
        result_all = [zips(**result_per) for result_per in result]
        return result_all


world_boss_active_menu = on_command("世界boss",
                                    aliases={'世界Boss', '世界BOSS'},
                                    priority=9, permission=GROUP, block=True)
world_boss_shop_menu = on_command("世界boss商店",
                                  aliases={'世界Boss商店', '世界BOSS商店'},
                                  priority=8, permission=GROUP, block=True)
world_boss_shop_buy = on_command("世界boss商店兑换",
                                 aliases={'世界Boss商店兑换', '世界BOSS商店兑换',
                                          '世界boss积分兑换', '世界Boss积分兑换', '世界BOSS积分兑换'},
                                 priority=8, permission=GROUP, block=True)
world_boss_fight = on_command("挑战世界boss",
                              aliases={'挑战世界Boss', '挑战世界BOSS'},
                              priority=3, permission=GROUP, block=True)
world_boss_fight_top = on_command("世界boss伤害排行",
                                  aliases={'世界boss排行', '世界Boss排行', '世界BOSS排行'},
                                  priority=8, permission=GROUP, block=True)

time_set_world_boss = on_command('重置世界BOSS', priority=15, permission=SUPERUSER, block=True)
world_boss_shop_reload = on_command('重载世界BOSS商店', priority=15, permission=SUPERUSER, block=True)


@time_set_world_boss.handle(parameterless=[Cooldown(cd_time=5)])
async def time_set_world_boss_(bot: Bot, event: GroupMessageEvent):
    """挑战世界boss"""
    await database.sql_execute("update world_boss set fight_num=0")
    msg = f"重置世界boss成功"
    await bot.send(event=event, message=msg)
    await time_set_world_boss.finish()


@world_boss_shop_reload.handle(parameterless=[Cooldown(cd_time=5)])
async def world_boss_shop_reload_(bot: Bot, event: GroupMessageEvent):
    """挑战世界boss"""
    global WORLD_BOSS_SHOP
    with open(Path(__file__).parent / 'world_boss_shop.json', "r", encoding="UTF-8") as file:
        data = file.read()
    WORLD_BOSS_SHOP = {int(item_no): item_info for item_no, item_info in json.loads(data).items()}
    msg = f"重载世界boss商店成功"
    await bot.send(event=event, message=msg)
    await world_boss_shop_reload.finish()


@world_boss_shop_buy.handle(
    parameterless=[
        Cooldown(cd_time=5)])
async def world_boss_shop_buy_(
        bot: Bot,  # 机器人实例
        event: GroupMessageEvent,  # 消息主体
        args: Message = CommandArg()  # 命令参数
):
    """挑战积分兑换"""
    user_info = await check_user(event)
    user_id = user_info['user_id']
    user_cmd_lock = UserCmdLock(user_id)
    with user_cmd_lock:
        arg_str = args.extract_plain_text()
        nums = get_num_from_str(arg_str)
        goods_id = int(nums[0]) if nums else 0
        goods_num = int(nums[1]) if len(nums) > 1 else 1
        user_world_boss_info = await get_user_world_boss_info(user_id)
        point = user_world_boss_info['world_point']
        goods_info = WORLD_BOSS_SHOP
        goods = goods_info.get(goods_id, 0)
        if not goods:
            msg = "请输入正确的物品编号！！！"
            await bot.send(event=event, message=msg)
            await world_boss_shop_buy.finish()
        goods_price = operator.mul(goods['price'], goods_num)
        item_id = goods.get('item', 0)
        if item_id:
            item = items.get_data_by_item_id(item_id)
            item_name = item['name']
        else:  # 兼容性处理
            item = {}
            item_name = "未知物品"
        if operator.gt(goods_price, point):
            msg = f"兑换{goods_num}个{item_name},需要{goods_price}点积分，道友仅有{point}点积分！！！"
            await bot.send(event=event, message=msg)
            await world_boss_shop_buy.finish()
        user_world_boss_info['world_point'] -= goods_price
        await update_user_world_boss_info(user_id, user_world_boss_info)
        if item_id:
            await sql_message.send_back(user_id, item_id, item_name, item['type'], goods_num, 1)
        msg = f"成功兑换{item_name}{goods_num}个"
        text = f"消耗{goods_price}世界boss积分，余剩{user_world_boss_info['world_point']}积分"
        msg = main_md(
            msg, text,
            '世界boss商店兑换 物品编号 数量', '世界boss商店兑换',
            '世界boss排行', '世界boss排行',
            '世界boss菜单', '世界boss',
            '挑战世界boss', '挑战世界boss')
        await bot.send(event=event, message=msg)
        await world_boss_shop_buy.finish()


@world_boss_shop_menu.handle(
    parameterless=[
        Cooldown(cd_time=3)])
async def world_boss_shop_menu_(
        bot: Bot,  # 机器人实例
        event: GroupMessageEvent,  # 消息主体
):
    user_info = await check_user(event)
    user_id = user_info['user_id']
    user_world_boss_info = await get_user_world_boss_info(user_id)
    point = user_world_boss_info['world_point']
    msg_list = []
    msg_head = (f"世界boss积分兑换商店\r"
                f"当前拥有积分：{point}")
    shop = WORLD_BOSS_SHOP
    for goods_no, goods in shop.items():
        msg = (f"商品编号：{goods_no}\r"
               f"物品名称：{items.get_data_by_item_id(goods.get('item')).get('name')}\r"
               f"兑换需要积分：{goods.get('price')}")
        msg_list.append(msg)
    text = msg_handler(bot, event, msg_list)
    msg = main_md(
        msg_head, text,
        '世界boss商店兑换 物品编号 数量', '世界boss商店兑换',
        '世界boss排行', '世界boss排行',
        '世界boss菜单', '世界boss',
        '挑战世界boss', '挑战世界boss')
    await bot.send(event=event, message=msg)
    await world_boss_shop_menu.finish()


@world_boss_fight_top.handle(parameterless=[Cooldown()])
async def world_boss_fight_top_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """世界boss伤害排行榜"""
    user_info = await check_user(event)
    user_id = user_info['user_id']
    place_id = await place.get_now_place_id(user_id=user_id)
    world_id = place.get_world_id(place_id)
    world_name = place.get_world_name(place_id)
    page = get_args_num(args, 1, default=1)
    lt_rank = await get_world_boss_fight_top(world_id)
    long_rank = len(lt_rank)
    page_all = (long_rank // 20) + 1 if long_rank % 20 != 0 else long_rank // 20  # 总页数
    if page_all < page != 1:
        msg = f"挑战排行榜没有那么广阔！！！"
        await bot.send(event=event, message=msg)
        await world_boss_fight_top.finish()
    if long_rank != 0:
        # 获取页数物品数量
        item_num = page * 20 - 20
        item_num_end = item_num + 20
        lt_rank = lt_rank[item_num:item_num_end]
        top_msg = f"✨【{world_name}】世界boss伤害排行TOP{item_num_end}✨"
        msg = ''
        num = item_num
        for i in lt_rank:
            i = list(i.values())
            num += 1
            msg += f"第{num}位 {i[0]} 总计造成:{number_to(i[1])}伤害\r"
        msg += f"第 {page}/{page_all} 页"
        msg = main_md(top_msg, msg,
                      '下一页', f'世界boss排行 {page + 1}',
                      '世界boss商店', '世界boss商店',
                      '世界boss菜单', '世界boss',
                      '前往挑战世界boss', '挑战世界boss')
    else:
        msg = f"该排行榜空空如也！"
    await bot.send(event=event, message=msg)
    await world_boss_fight_top.finish()


@world_boss_fight.handle(parameterless=[Cooldown(cd_time=5)])
async def world_boss_fight_(bot: Bot, event: GroupMessageEvent):
    """挑战世界boss"""

    user_info = await check_user(event)
    user_id = user_info['user_id']
    is_type, msg = await check_user_type(user_id, 0)
    if not is_type:
        await bot.send(event=event, message=msg)
        await world_boss_fight.finish()
    user_cmd_lock = UserCmdLock(user_id)
    with user_cmd_lock:
        user_world_boss_info = await get_user_world_boss_info(user_id)
        user_name = user_info['user_name']
        if user_world_boss_info['fight_num'] > 2:
            msg = f"道友今天已经挑战了足够多次世界boss了\r"
            msg = simple_md(msg, "查看日常", "日常中心", "。")
            await bot.send(event=event, message=msg)
            await world_boss_fight.finish()

        place_id = await place.get_now_place_id(user_id=user_id)
        world_id = place.get_world_id(place_id)
        msg_list, boss_info = await get_world_boss_battle_info(user_id)
        new_damage = boss_info['总血量'] - boss_info['气血']
        user_world_boss_info['fight_num'] += 1
        user_world_boss_info['world_point'] += 15
        user_world_boss_info['world_id'] = world_id
        user_world_boss_info['fight_damage'] += new_damage
        await update_user_world_boss_info(user_id, user_world_boss_info)
        text = msg_handler(msg_list)
        msg = (f"{user_name}道友全力施为，对{boss_name_now}造成{number_to(new_damage)}伤害！！"
               f"\r当前总计造成{number_to(user_world_boss_info['fight_damage'])}伤害"
               f"\r获得15点世界boss积分")
        msg = main_md(
            msg, text,
            '世界boss排行', '世界boss排行',
            '世界boss商店', '世界boss商店',
            '世界boss菜单', '世界boss',
            '继续挑战世界boss', '挑战世界boss')
        await bot.send(event=event, message=msg)
        await world_boss_fight.finish()


@world_boss_active_menu.handle(parameterless=[Cooldown(cd_time=5)])
async def world_boss_active_menu_(bot: Bot, event: GroupMessageEvent):
    """挑战世界boss"""

    user_info = await check_user(event)
    user_id = user_info['user_id']
    user_world_boss_info = await get_user_world_boss_info(user_id)
    msg = (f"世界boss菜单：\r"
           f"每日共有3次世界boss挑战机会\r"
           f"排行榜按本周造成总计伤害排序\r"
           f"每周日晚九点结算排名奖励:\r"
           f"第一；150\r"
           "第二；120\r"
           "第三；100\r"
           "第四～十；50\r"
           "第11~100；30\r"
           "100以后参与奖10分\r"
           f"当前累计造成{number_to(user_world_boss_info['fight_damage'])}点伤害\r")
    msg = three_md(
        msg, '挑战世界boss', '挑战世界boss',
        f"\r🔹今日余剩次数{user_world_boss_info['fight_num']}/3\r",
        '世界boss商店', '世界boss商店',
        f"\r🔹当前积分{user_world_boss_info['world_point']}\r",
        '世界boss排行', '世界boss伤害排行', '。')
    await bot.send(event=event, message=msg)
    await world_boss_active_menu.finish()
