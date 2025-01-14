import asyncio

from nonebot import on_command, require, on_fullmatch
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    GROUP_ADMIN,
    GROUP_OWNER,
    ActionFailed
)
from nonebot.log import logger
from nonebot.params import CommandArg, RawCommand
from nonebot.permission import SUPERUSER

from .back_util import (
    get_user_main_back_msg, get_use_equipment_sql, get_shop_data, save_shop,
    get_item_msg, get_item_msg_rank, check_use_elixir,
    get_use_jlq_msg, get_no_use_equipment_sql, get_use_tool_msg,
    get_user_main_back_msg_easy, get_user_back_msg)
from ..xiuxian_config import XiuConfig, convert_rank
from ..xiuxian_limit import limit_handle
from ..xiuxian_place import place
from ..xiuxian_utils.clean_utils import (
    get_args_num, get_num_from_str,
    get_strs_from_str, get_paged_msg, main_md,
    msg_handler, three_md)
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown, CooldownIsolateLevel
from ..xiuxian_utils.utils import (
    check_user, send_msg_handler,
    number_to, get_id_from_str
)
from ..xiuxian_utils.xiuxian2_handle import (
    sql_message, get_weapon_info_msg, get_armor_info_msg,
    get_sec_msg, get_main_info_msg, get_sub_info_msg, UserBuffDate
)

auction = {}
AUCTIONSLEEPTIME = 120  # 拍卖初始等待时间（秒）
cache_help = {}
auction_offer_flag = False  # 拍卖标志
AUCTIONOFFERSLEEPTIME = 30  # 每次拍卖增加拍卖剩余的时间（秒）
auction_offer_time_count = 0  # 计算剩余时间
auction_offer_all_count = 0  # 控制线程等待时间
# 定时任务
set_auction_by_scheduler = require("nonebot_plugin_apscheduler").scheduler
reset_day_num_scheduler = require("nonebot_plugin_apscheduler").scheduler

goods_re_root = on_command("炼金", priority=6, permission=GROUP, block=True)
goods_re_root_fast = on_command("快速炼金", aliases={"批量炼金"}, priority=6, permission=GROUP, block=True)
shop = on_command("坊市查看", aliases={"查看坊市"}, priority=8, permission=GROUP, block=True)
auction_view = on_command("拍卖品查看", aliases={"查看拍卖品"}, priority=8, permission=GROUP, block=True)
shop_added_by_admin = on_command("系统坊市上架", priority=5, permission=SUPERUSER, block=True)
shop_off_all = on_fullmatch("清空坊市", priority=3, permission=SUPERUSER, block=True)
main_back = on_command('我的背包', aliases={'我的物品', '背包'}, priority=2, permission=GROUP, block=True)
skill_back = on_command('功法背包', priority=2, permission=GROUP, block=True)
check_back = on_command('别人的背包', aliases={'检查背包'}, priority=2, permission=SUPERUSER, block=True)
use = on_command("使用", priority=15, permission=GROUP, block=True)
no_use_zb = on_command("换装", aliases={"卸载"}, priority=5, permission=GROUP, block=True)
buy = on_command("坊市购买", priority=5, block=True)
auction_added = on_command("提交拍卖品", aliases={"拍卖品提交"}, priority=3, permission=GROUP, block=True)
auction_withdraw = on_command("撤回拍卖品", aliases={"拍卖品撤回"}, priority=3, permission=GROUP, block=True)
set_auction = on_command("群拍卖会", priority=4, permission=GROUP and (SUPERUSER | GROUP_ADMIN | GROUP_OWNER),
                         block=True)
creat_auction = on_fullmatch("举行拍卖会", priority=5, permission=GROUP and SUPERUSER, block=True)
offer_auction = on_command("拍卖", priority=5, permission=GROUP, block=True)
back_help = on_command("背包帮助", aliases={"坊市帮助"}, priority=8, permission=GROUP, block=True)
xiuxian_stone = on_fullmatch("灵石", priority=4, permission=GROUP, block=True)
master_rename = on_command("超管改名", priority=2, permission=SUPERUSER, block=True)
check_items = on_command("查看", aliases={"查", "查看物品", "查看效果", "详情"}, priority=25, permission=GROUP,
                         block=True)
back_fix = on_fullmatch("背包修复", priority=1, permission=GROUP, block=True)
test_md = on_command("测试模板", priority=25, permission=SUPERUSER, block=True)
check_item_json = on_command("物品结构", aliases={"json"}, priority=25, permission=SUPERUSER, block=True)

__back_help__ = f"""
指令：
1：我的背包:
 - 查看自身背包内的物品信息
2：使用+物品名字
 - 使用物品,可批量使用
3：换装+装备名字
 - 卸载目标装备
4注释：交易请上灵宝楼
 - 发送 灵宝楼帮助
5：炼金+物品名字
 - 将物品炼化为灵石,支持批量炼金
6：快速炼金+目标物品品阶
 - 将指定品阶的物品全部炼金  例（快速炼金 先天品级）
——tips——
官方群914556251
""".strip()


@test_md.handle()
async def md_test_(bot: Bot, event: GroupMessageEvent):
    msg = three_md(
        '<qqbot-cmd-input text="', '指令1指令0" /> a[aa', '悬赏令接取1', "测试",
        '指令2', '悬赏令接取2', "测试",
        '指令3', '悬赏令接取3', "测试",
    )
    await bot.send(event, msg)
    await test_md.finish()


@back_fix.handle(parameterless=[Cooldown(at_sender=False, parallel_block=True)])
async def back_help_(bot: Bot, event: GroupMessageEvent):
    """背包修复"""
    _, user_info, _ = await check_user(event)
    user_id = user_info["user_id"]
    user_backs = await sql_message.get_back_msg_all(user_id)  # list(back)
    item_check = {}
    msg = '开始进行背包修复，请稍等'
    await bot.send(event=event, message=msg)
    msg = "尝试进行背包修复："
    for item in user_backs:
        item_id = item["goods_id"]
        if item_check.get(item_id):
            old_item_info = await sql_message.get_item_by_good_id_and_user_id(user_id, item_id)
            old_name = old_item_info['goods_name']
            old_type = old_item_info['goods_type']
            old_num = max(old_item_info['goods_num'], 1)
            old_bind_num = min(max(old_item_info['bind_num'], 0), old_num)
            if item_id == 640001:
                old_num += 5
                old_bind_num += 6
                old_bind_num = min(old_bind_num, old_num)
            elif item_id == 610004:
                old_num += 11
                old_bind_num += 12
                old_bind_num = min(old_bind_num, old_num)
            if old_type == '丹药':
                old_bind_num = old_num
            await sql_message.del_back_item(user_id, item_id)
            await  sql_message.send_back(user_id, item_id, old_name, old_type, max((old_num - old_bind_num), 0))
            await  sql_message.send_back(user_id, item_id, old_name, old_type, old_bind_num, 1)
            msg += f"\r检测到 {old_name} 重复，遗失数据：{old_num}个，绑定数量{old_bind_num}个"
        else:
            item_check[item_id] = 1
    await bot.send(event=event, message=msg)
    await back_fix.finish()


# 重置丹药每日使用次数
@reset_day_num_scheduler.scheduled_job("cron", hour=0, minute=0, )
async def reset_day_num_scheduler_():
    await sql_message.day_num_reset()
    logger.opt(colors=True).info(f"<green>每日丹药使用次数重置成功！</green>")


@back_help.handle(parameterless=[Cooldown(at_sender=False)])
async def back_help_(bot: Bot, event: GroupMessageEvent):
    """背包帮助"""
    msg = __back_help__
    await bot.send(event=event, message=msg)
    await back_help.finish()


@xiuxian_stone.handle(parameterless=[Cooldown(at_sender=False)])
async def xiuxian_stone_(bot: Bot, event: GroupMessageEvent):
    """我的灵石信息"""
    _, user_info, _ = await check_user(event)
    msg = f"当前灵石：{number_to(user_info['stone'])} | {user_info['stone']}"
    await bot.send(event=event, message=msg)
    await xiuxian_stone.finish()


buy_lock = asyncio.Lock()


@buy.handle(parameterless=[Cooldown(1.4, at_sender=False, isolate_level=CooldownIsolateLevel.GROUP)])
async def buy_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """购物"""
    async with buy_lock:
        isUser, user_info, msg = await check_user(event)
        user_id = user_info['user_id']
        user_name = user_info['user_name']
        place_id = str(await place.get_now_place_id(user_id))
        shop_data = get_shop_data(place_id)

        if shop_data[place_id] == {}:
            msg = "此地的坊市目前空空如也！"
            await bot.send(event=event, message=msg)
            await buy.finish()
        input_args = args.extract_plain_text().strip().split()
        if len(input_args) < 1:
            # 没有输入任何参数
            msg = "请输入正确指令！例如：坊市购买 物品编号 数量"
            await bot.send(event=event, message=msg)
            await buy.finish()
        else:
            try:
                arg = int(input_args[0])
                if len(input_args) == 0:
                    "请输入正确指令！例如：坊市购买 物品编号 数量"

                goods_info = shop_data[place_id].get(str(arg))
                if not goods_info:
                    raise ValueError("编号对应的商品不存在！")

                purchase_quantity = int(input_args[1]) if len(input_args) > 1 else 1
                if purchase_quantity <= 0:
                    raise ValueError("购买数量必须是正数！")

                if 'stock' in goods_info and purchase_quantity > goods_info['stock']:
                    raise ValueError("购买数量超过库存限制！")
            except ValueError:
                msg = f"请输入正确的物品编号而不是物品名称！！！"
                await bot.send(event=event, message=msg)
                await buy.finish()
        shop_user_id = shop_data[place_id][str(arg)]['user_id']
        goods_price = goods_info['price'] * purchase_quantity
        goods_stock = goods_info.get('stock', 1)
        if user_info['stone'] < goods_price:
            msg = '没钱还敢来买东西！！'
            await bot.send(event=event, message=msg)
            await buy.finish()
        elif int(user_id) == int(shop_data[place_id][str(arg)]['user_id']):
            msg = "道友自己的东西就不要自己购买啦！"
            await bot.send(event=event, message=msg)
            await buy.finish()
        elif purchase_quantity > goods_stock and shop_user_id != 0:
            msg = "库存不足，无法购买所需数量！"
            await bot.send(event=event, message=msg)
        else:
            shop_goods_name = shop_data[place_id][str(arg)]['goods_name']
            shop_user_name = shop_data[place_id][str(arg)]['user_name']
            shop_goods_id = shop_data[place_id][str(arg)]['goods_id']
            shop_goods_type = shop_data[place_id][str(arg)]['goods_type']
            await sql_message.update_ls(user_id, goods_price, 2)
            await sql_message.send_back(user_id, shop_goods_id, shop_goods_name, shop_goods_type, purchase_quantity)
            save_shop(shop_data)

            if shop_user_id == 0:  # 0为系统
                msg = f"{user_name}道友成功购买{purchase_quantity}个{shop_goods_name}，消耗灵石{goods_price}枚！"
            else:
                goods_info['stock'] -= purchase_quantity
                if goods_info['stock'] <= 0:
                    del shop_data[place_id][str(arg)]  # 库存为0，移除物品
                else:
                    shop_data[place_id][str(arg)] = goods_info
                service_charge = int(goods_price * 0.1)  # 手续费10%
                give_stone = goods_price - service_charge
                msg = f"{user_name}道友成功购买{purchase_quantity}个{shop_user_name}道友寄售的{shop_goods_name}，消耗灵石{goods_price}枚,坊市收取手续费：{service_charge}枚灵石！"
                await sql_message.update_ls(shop_user_id, give_stone, 1)
            shop_data[place_id] = reset_dict_num(shop_data[place_id])
            save_shop(shop_data)
            await limit_handle.update_user_shop_log_data(user_id, msg)
            await limit_handle.update_user_shop_log_data(shop_user_id, msg)
            await bot.send(event=event, message=msg)
            await buy.finish()


@shop.handle(parameterless=[Cooldown(at_sender=False)])
async def shop_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """坊市查看"""
    _, user_info, _ = await check_user(event)
    user_id = user_info["user_id"]
    place_id = str(await place.get_now_place_id(user_id))
    shop_data = get_shop_data(place_id)
    data_list = []
    if shop_data[place_id] == {}:
        msg = "此地的坊市目前空空如也！"
        await bot.send(event=event, message=msg)
        await shop.finish()
    page = get_num_from_str(args.extract_plain_text())
    arg = get_strs_from_str(args.extract_plain_text())
    desc_on = True if "详情" in arg else False
    for k, v in shop_data[place_id].items():
        msg = f"编号：{k}\r"
        if desc_on:
            msg += f"{v['desc']}"
        else:
            msg += f"{v['goods_name']}"
        msg += f"\r价格：{number_to(v['price'])}|{v['price']}枚灵石\r"
        if v['user_id'] != 0:
            msg += f"拥有人：{v['user_name']}道友\r"
            msg += f"数量：{v['stock']}\r"
        else:
            msg += f"百宝楼寄售\r"
        data_list.append(msg)
    items_all = len(data_list)
    page_all = ((items_all // 12) + 1) if (items_all % 12 != 0) else (items_all // 12)  # 总页数
    if page:
        page = page[0]
        pass
    else:
        page = 1
    page = int(page)
    if page_all < page:
        msg = "此地坊市没有那么多东西！！！"
        await bot.send(event=event, message=msg)
        await shop.finish()
    items_start = page * 12 - 12
    items_end = items_start + 12
    data_list = data_list[items_start:items_end]
    page_info = f"第{page}/{page_all}页\r———tips———\r可以发送 查看坊市 页数 来查看更多商品哦"
    data_list.append(page_info)
    await send_msg_handler(bot, event, '坊市', bot.self_id, data_list)
    await shop.finish()


@shop_added_by_admin.handle(
    parameterless=[Cooldown(1.4, at_sender=False, isolate_level=CooldownIsolateLevel.GROUP, parallel=1)])
async def shop_added_by_admin_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """系统上架坊市"""
    args = args.extract_plain_text().split()
    if not args:
        msg = "请输入正确指令！例如：系统坊市上架 物品 金额"
        await bot.send(event=event, message=msg)
        await shop_added_by_admin.finish()
    goods_name = args[0]
    goods_id = -1
    for k, v in items.items.items():
        if goods_name == v['name']:
            goods_id = k
            break
        else:
            continue
    if goods_id == -1:
        msg = f"不存在该物品的信息，请检查名字是否输入正确！"
        await bot.send(event=event, message=msg)
        await shop_added_by_admin.finish()
    price = None
    try:
        price = args[1]
    except LookupError:
        msg = "请输入正确指令！例如：系统坊市上架 物品 金额"
        await bot.send(event=event, message=msg)
        await shop_added_by_admin.finish()
    try:
        price = int(price)
        if price < 0:
            msg = "请不要设置负数！"
            await bot.send(event=event, message=msg)
            await shop_added_by_admin.finish()
    except LookupError:
        msg = "请输入正确的金额！"
        await bot.send(event=event, message=msg)
        await shop_added_by_admin.finish()

    try:
        var = args[2]
        msg = "请输入正确指令！例如：系统坊市上架 物品 金额"
        await bot.send(event=event, message=msg)
        await shop_added_by_admin.finish()
    except LookupError:
        pass

    group_id = str(event.group_id)
    shop_data = get_shop_data(group_id)
    if shop_data == {}:
        shop_data[group_id] = {}
    goods_info = items.get_data_by_item_id(goods_id)

    id_ = len(shop_data[group_id]) + 1
    shop_data[group_id][id_] = {}
    shop_data[group_id][id_]['user_id'] = 0
    shop_data[group_id][id_]['goods_name'] = goods_name
    shop_data[group_id][id_]['goods_id'] = goods_id
    shop_data[group_id][id_]['goods_type'] = goods_info['type']
    shop_data[group_id][id_]['desc'] = get_item_msg(goods_id)
    shop_data[group_id][id_]['price'] = price
    shop_data[group_id][id_]['user_name'] = '系统'
    save_shop(shop_data)
    msg = f"物品：{goods_name}成功上架坊市，金额：{price}枚灵石！"
    await bot.send(event=event, message=msg)
    await shop_added_by_admin.finish()


@goods_re_root.handle(parameterless=[Cooldown(at_sender=False)])
async def goods_re_root_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """炼金"""
    isUser, user_info, msg = await check_user(event)
    user_id = user_info['user_id']
    strs = args.extract_plain_text()
    args = get_strs_from_str(strs)
    num = get_num_from_str(strs)
    if num:
        num = int(num[0])
    else:
        num = 1
    if args:
        goods_name = args[0]
        pass
    else:
        goods_name = None
        msg = "请输入要炼化的物品！"
        await bot.send(event=event, message=msg)
        await goods_re_root.finish()
    back_msg = await sql_message.get_back_msg(user_id)  # 背包sql信息,list(back)
    if back_msg is None:
        msg = "道友的背包空空如也！"
        await bot.send(event=event, message=msg)
        await goods_re_root.finish()
    in_flag = False  # 判断指令是否正确，道具是否在背包内
    goods_id = None
    goods_type = None
    goods_state = None
    goods_num = None
    for back in back_msg:
        if goods_name == back['goods_name']:
            in_flag = True
            goods_id = back['goods_id']
            goods_type = back['goods_type']
            goods_state = back['state']
            goods_num = back['goods_num']
            break
    if not in_flag:
        msg = f"请检查该道具 {goods_name} 是否在背包内！"
        await bot.send(event=event, message=msg)
        await goods_re_root.finish()

    if goods_num < num:
        msg = f"道友的包内没有那么多 {goods_name} ！"
        await bot.send(event=event, message=msg)
        await goods_re_root.finish()

    if goods_type == "装备" and int(goods_state) == 1 and int(goods_num) == 1:
        msg = f"装备：{goods_name}已经被道友装备在身，无法炼金！"
        await bot.send(event=event, message=msg)
        await goods_re_root.finish()

    if get_item_msg_rank(goods_id) == 520:
        msg = "此类物品不支持！"
        await bot.send(event=event, message=msg)
        await goods_re_root.finish()

    price = int(1000000 + abs(get_item_msg_rank(goods_id) - 55) * 100000) * num
    if price <= 0:
        msg = f"物品：{goods_name}炼金失败，凝聚{price}枚灵石，记得通知超管！"
        await bot.send(event=event, message=msg)
        await goods_re_root.finish()

    await sql_message.update_back_j(user_id, goods_id, num=num, use_key=2)
    await sql_message.update_ls(user_id, price, 1)
    msg = f"物品：{goods_name} 数量：{num} 炼金成功，凝聚{number_to(price)}|{price}枚灵石！"
    await bot.send(event=event, message=msg)
    await goods_re_root.finish()


@goods_re_root_fast.handle(parameterless=[Cooldown(at_sender=False)])
async def goods_re_root_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """快速炼金"""
    is_user, user_info, msg = await check_user(event)
    user_id = user_info['user_id']
    strs = args.extract_plain_text()
    args = get_strs_from_str(strs)
    if args:
        the_same = XiuConfig().elixir_def  # 若无配置自行替换为 {}
        real_args = [the_same[i] if i in the_same else i for i in args]
    else:
        msg = "请输入要炼化的物品等阶！"
        await bot.send(event=event, message=msg)
        await goods_re_root_fast.finish()
    msg = "快速炼金以下品阶物品：\r" + "|".join(args)
    price_sum = 0
    for goal_level, goal_level_name in zip(real_args, args):
        back_msg = await sql_message.get_back_msg(user_id)  # 背包sql信息,list(back)
        msg += f"\r快速炼金【{goal_level_name}】结果如下："
        if back_msg is None:
            msg += "道友的背包已空！！！"
            break
        price_pass = 0
        for back in back_msg:
            goods_id = back['goods_id']
            goods_state = back['state']
            num = back['goods_num']
            goods_type = back['goods_type']
            goods_name = back['goods_name']
            item_info = items.get_data_by_item_id(goods_id)
            buff_type = item_info.get('buff_type')
            if ((item_level := item_info.get('level') if item_info else None) == goal_level
                    or goods_name == goal_level
                    or buff_type == goal_level
                    or goods_type == goal_level):
                if goods_type == "装备" and int(goods_state) == 1:
                    msg += f"\r装备：{goods_name}已经被道友装备在身，无法炼金！"
                    price_pass = 1
                elif (item_rank := get_item_msg_rank(goods_id)) != 520:
                    price = int(1000000 + abs(item_rank - 55) * 100000) * num  # 复制炼金价格逻辑
                    await sql_message.update_back_j(user_id, goods_id, num=num, use_key=2)
                    await sql_message.update_ls(user_id, price, 1)
                    price_sum += price
                    msg += f"\r物品：{goods_name} 数量：{num} 炼金成功，凝聚{number_to(price)}|{price}枚灵石！"
                    price_pass = 1
        if not price_pass:
            msg += f"\r道友没有【{goal_level_name}】"
    msg += f"\r总计凝聚{number_to(price_sum)}|{price_sum}枚灵石"
    await bot.send(event=event, message=msg)
    await goods_re_root_fast.finish()


@main_back.handle(parameterless=[Cooldown(cd_time=10, at_sender=False)])
async def main_back_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg(), cmd: str = RawCommand()):
    """我的背包
    ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
    "remake", "day_num", "all_num", "action_time", "state"]
    """
    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']

    args = args.extract_plain_text()
    arg = get_strs_from_str(args)
    desc_on = True if "详情" in arg else False
    page = get_args_num(args, 1)  # 背包页数
    page = page if page else 1
    if desc_on:
        msg = await get_user_main_back_msg(user_id)
        page_all = 12
        argp = '详情'
    else:
        msg = await get_user_main_back_msg_easy(user_id)
        page_all = 30
        argp = ''

    if msg:
        text = get_paged_msg(msg_list=msg, page=page, cmd=cmd, per_page_item=page_all)
        text = msg_handler(text)
        msg = f"\r{user_info['user_name']}的背包，持有灵石：{number_to(user_info['stone'])}枚"
        msg = main_md(
            msg, text,
            '下一页', f'我的背包{argp} {page + 1}',
            '丹药背包', '丹药背包',
            '药材背包', '药材背包',
            '背包帮助', '背包帮助')
    else:
        msg = "道友的背包空空如也！"
    await bot.send(event, msg)
    await main_back.finish()


@skill_back.handle(parameterless=[Cooldown(cd_time=10, at_sender=False)])
async def skill_back_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg(), cmd: str = RawCommand()):
    """我的背包
    ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
    "remake", "day_num", "all_num", "action_time", "state"]
    """
    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']

    args = args.extract_plain_text()
    page = get_args_num(args, 1)  # 背包页数
    page = page if page else 1
    msg = await get_user_back_msg(user_id, ['技能'])
    page_all = 30

    if msg:
        text = get_paged_msg(msg_list=msg, page=page, cmd=cmd, per_page_item=page_all)
        text = msg_handler(text)
        msg = f"{user_info['user_name']}的背包，持有灵石：{number_to(user_info['stone'])}枚"
        msg = main_md(
            msg, text,
            '背包帮助', '背包帮助',
            '丹药背包', '丹药背包',
            '药材背包', '药材背包',
            '下一页', f'功法背包 {page + 1}')
    else:
        msg = "道友的背包空空如也！"
    await bot.send(event, msg)
    await skill_back.finish()


@check_back.handle(parameterless=[Cooldown(cd_time=10, at_sender=False)])
async def check_back_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg(), cmd: str = RawCommand()):
    """别人的背包
    ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
    "remake", "day_num", "all_num", "action_time", "state"]
    """
    _, user_info, _ = await check_user(event)

    args = args.extract_plain_text()
    arg = get_strs_from_str(args)
    user_id = await get_id_from_str(args)
    desc_on = True if "详情" in arg else False
    page = get_args_num(args, 1)  # 背包页数
    page = page if page else 1
    if desc_on:
        msg = await get_user_main_back_msg(user_id)
        page_all = 12
    else:
        msg = await get_user_main_back_msg_easy(user_id)
        page_all = 30

    if msg:
        text = get_paged_msg(msg_list=msg, page=page, cmd=cmd, per_page_item=page_all)
        text = msg_handler(text)
        msg = f"\r{user_info['user_name']}的背包，持有灵石：{number_to(user_info['stone'])}枚"
        msg = main_md(
            msg, text,
            '下一页', f'我的背包{page + 1}',
            '丹药背包', '丹药背包',
            '药材背包', '药材背包',
            '背包帮助', '背包帮助')
    else:
        msg = "道友的背包空空如也！"
    await bot.send(event, msg)
    await check_back.finish()


@no_use_zb.handle(parameterless=[Cooldown(at_sender=False)])
async def no_use_zb_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """卸载物品（只支持装备）
    ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
    "remake", "day_num", "all_num", "action_time", "state"]
    """
    isUser, user_info, msg = await check_user(event)
    user_id = user_info['user_id']
    args = args.extract_plain_text()
    msg_info = get_strs_from_str(args)
    item_name = msg_info[0] if msg_info else None  # 获取第一个名称
    goods_id = items.items_map.get(item_name)
    item_info = await sql_message.get_item_by_good_id_and_user_id(user_id, goods_id)
    goods_type = item_info['goods_type']
    if not (item_info and item_info['goods_num']):
        msg = f"请检查道具是否在背包内！"
        await bot.send(event=event, message=msg)
        await no_use_zb.finish()
    if goods_type == "装备":
        if item_info['state']:
            sql_str, item_type = await get_no_use_equipment_sql(user_id, goods_id)
            for sql in sql_str:
                await sql_message.update_back_equipment(sql)
            if item_type == "法器":
                await sql_message.updata_user_faqi_buff(user_id, 0)
            if item_type == "防具":
                await sql_message.updata_user_armor_buff(user_id, 0)
            msg = f"成功卸载装备{item_name}！"
            await bot.send(event=event, message=msg)
            await no_use_zb.finish()
        else:
            msg = "装备没有被使用，无法卸载！"
            await bot.send(event=event, message=msg)
            await no_use_zb.finish()
    else:
        msg = "目前只支持卸载装备！"
        await bot.send(event=event, message=msg)
        await no_use_zb.finish()


@use.handle(parameterless=[Cooldown(at_sender=False)])
async def use_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """使用物品
    ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
    "remake", "day_num", "all_num", "action_time", "state"]
    """
    is_user, user_info, msg = await check_user(event)
    user_id = user_info['user_id']
    args = args.extract_plain_text()
    msg_info = get_strs_from_str(args)
    num_info = get_num_from_str(args)
    item_name = msg_info[0] if msg_info else None  # 获取第一个名称
    num = int(num_info[0]) if num_info else 1  # 获取第一个数量
    goods_id = items.items_map.get(item_name)
    item_info = await sql_message.get_item_by_good_id_and_user_id(user_id, goods_id)
    if not item_info:
        msg = f"请检查该道具是否在背包内！"
        await bot.send(event=event, message=msg)
        await use.finish()
    goods_type = item_info['goods_type']
    goods_num = item_info['goods_num']
    if not item_info['goods_num']:
        msg = f"请检查该道具是否充足！！"
        await bot.send(event=event, message=msg)
        await use.finish()
    if goods_type == "装备":
        if item_info['state']:
            msg = "该装备已被装备，请勿重复装备！"
            await bot.send(event=event, message=msg)
            await use.finish()
        else:  # 可以装备
            sql_str, item_type = await get_use_equipment_sql(user_id, goods_id)
            for sql in sql_str:
                await sql_message.update_back_equipment(sql)
            if item_type == "法器":
                await sql_message.updata_user_faqi_buff(user_id, goods_id)
            if item_type == "防具":
                await sql_message.updata_user_armor_buff(user_id, goods_id)
            msg = f"成功装备{item_name}！"
            await bot.send(event=event, message=msg)
            await use.finish()
    elif goods_type == "技能":
        user_buff_info = await UserBuffDate(user_id).buff_info
        skill_info = items.get_data_by_item_id(goods_id)
        skill_type = skill_info['item_type']
        if skill_type == "神通":
            if int(user_buff_info['sec_buff']) == int(goods_id):
                msg = f"道友已学会该神通：{skill_info['name']}，请勿重复学习！"
            else:  # 学习sql

                power = await limit_handle.get_user_world_power_data(user_id)
                if int(skill_info['rank']) > 120:
                    if power >= 2048:
                        power -= 2048
                        use_power = f"\r消耗天地精华2048点，余剩{power}点！！"
                        await limit_handle.update_user_world_power_data(user_id, power)
                        await sql_message.update_back_j(user_id, goods_id, use_key=2)
                        await sql_message.updata_user_sec_buff(user_id, goods_id)
                        msg = f"恭喜道友学会神通：{skill_info['name']}！" + use_power
                        pass
                    else:
                        msg = f"需要拥有天地精华2048点，才可练就神通：{skill_info['name']}！"
                else:
                    await sql_message.update_back_j(user_id, goods_id, use_key=2)
                    await sql_message.updata_user_sec_buff(user_id, goods_id)
                    msg = f"恭喜道友学会神通：{skill_info['name']}！"
        elif skill_type == "功法":
            if int(user_buff_info['main_buff']) == int(goods_id):
                msg = f"道友已学会该功法：{skill_info['name']}，请勿重复学习！"
            else:  # 学习sql
                await sql_message.update_back_j(user_id, goods_id, use_key=2)
                await sql_message.updata_user_main_buff(user_id, goods_id)
                msg = f"恭喜道友学会功法：{skill_info['name']}！"
        elif skill_type == "辅修功法":  # 辅修功法1
            if int(user_buff_info['sub_buff']) == int(goods_id):
                msg = f"道友已学会该辅修功法：{skill_info['name']}，请勿重复学习！"
            else:  # 学习sql
                await sql_message.update_back_j(user_id, goods_id, use_key=2)
                await sql_message.updata_user_sub_buff(user_id, goods_id)
                msg = f"恭喜道友学会辅修功法：{skill_info['name']}！"
        else:
            msg = "发生未知错误！"
        await bot.send(event=event, message=msg)
        await use.finish()
    elif goods_type == "丹药":
        if num > int(goods_num):
            msg = f"道友背包中的{item_name}数量不足，当前仅有{goods_num}个！"
            await bot.send(event=event, message=msg)
            await use.finish()

        msg = await check_use_elixir(user_id, goods_id, num)
        await bot.send(event=event, message=msg)
        await use.finish()
    elif goods_type == "神物":
        if len(args) > 1 and 1 <= int(num) <= int(goods_num):
            num = int(num)
        elif len(args) > 1 and int(num) > int(goods_num):
            msg = f"道友背包中的{item_name}数量不足，当前仅有{goods_num}个！"
            await bot.send(event=event, message=msg)
            await use.finish()
        goods_info = items.get_data_by_item_id(goods_id)
        user_info = await sql_message.get_user_info_with_id(user_id)
        user_rank = convert_rank(user_info['level'])[0]
        goods_rank = goods_info['rank']
        goods_name = goods_info['name']
        if abs(goods_rank - 55) > user_rank:  # 使用限制
            msg = f"神物：{goods_name}的使用境界为{goods_info['境界']}以上，道友不满足使用条件！"
        else:
            await sql_message.update_back_j(user_id, goods_id, num, 2)
            goods_buff = goods_info["buff"]
            exp = goods_buff * num
            user_hp = int(user_info['hp'] + (exp / 2))
            user_mp = int(user_info['mp'] + exp)
            user_atk = int(user_info['atk'] + (exp / 10))
            await sql_message.update_exp(user_id, exp)
            await sql_message.update_power2(user_id)  # 更新战力
            await sql_message.update_user_attribute(user_id, user_hp, user_mp, user_atk)  # 这种事情要放在update_exp方法里

            msg = f"道友成功使用神物：{goods_name} {num}个 ,修为增加{number_to(exp)}|{exp}点！"
        await bot.send(event=event, message=msg)
        await use.finish()
    elif goods_type == "礼包":
        if len(args) > 1 and 1 <= int(num) <= int(goods_num):
            num = int(num)
        elif len(args) > 1 and int(num) > int(goods_num):
            msg = f"道友背包中的{item_name}数量不足，当前仅有{goods_num}个！"
            await bot.send(event=event, message=msg)
            await use.finish()
        goods_info = items.get_data_by_item_id(goods_id)
        goods_name = goods_info['name']
        goods_id1 = goods_info['buff_1']
        goods_id2 = goods_info['buff_2']
        goods_id3 = goods_info['buff_3']
        goods_name1 = goods_info['name_1']
        goods_name2 = goods_info['name_2']
        goods_name3 = goods_info['name_3']
        goods_type1 = goods_info['type_1']
        goods_type2 = goods_info['type_2']
        goods_type3 = goods_info['type_3']

        await sql_message.send_back(user_id, goods_id1, goods_name1, goods_type1, 1 * num, 1)  # 增加用户道具
        await sql_message.send_back(user_id, goods_id2, goods_name2, goods_type2, 2 * num, 1)
        await sql_message.send_back(user_id, goods_id3, goods_name3, goods_type3, 2 * num, 1)
        await sql_message.update_back_j(user_id, goods_id, num, 0)
        msg = f"道友打开了{num}个{goods_name},里面居然是{goods_name1}{int(1 * num)}个、{goods_name2}{int(2 * num)}个、{goods_name3}{int(2 * num)}个"
        await bot.send(event=event, message=msg)
        await use.finish()

    elif goods_type == "聚灵旗":
        msg = await get_use_jlq_msg(user_id, goods_id)
        await bot.send(event=event, message=msg)
        await use.finish()

    elif goods_type == "天地奇物":
        if num > int(goods_num):
            msg = f"道友背包中的{item_name}数量不足，当前仅有{goods_num}个！"
            await bot.send(event=event, message=msg)
            await use.finish()
        goods_info = items.get_data_by_item_id(goods_id)
        power = await limit_handle.get_user_world_power_data(user_id)
        msg = f"道友使用天地奇物{goods_info['name']}{num}个，将{goods_info['buff'] * num}点天地精华纳入丹田。\r请尽快利用！！否则天地精华将会消散于天地间！！"
        power += goods_info['buff'] * num
        await limit_handle.update_user_world_power_data(user_id, power)
        await sql_message.update_back_j(user_id, goods_id, num, 2)
        await bot.send(event=event, message=msg)
        await use.finish()
    elif goods_type == "道具":
        if num > int(goods_num):
            msg = f"道友背包中的{item_name}数量不足，当前仅有{goods_num}个！"
            await bot.send(event=event, message=msg)
            await use.finish()

        msg, is_pass = await get_use_tool_msg(user_id, goods_id, num)
        if is_pass:
            await sql_message.update_back_j(user_id, goods_id, num, 2)
        await bot.send(event=event, message=msg)
        await use.finish()
    else:
        msg = '该类型物品调试中，未开启！'
        await bot.send(event=event, message=msg)
        await use.finish()


@check_items.handle(parameterless=[Cooldown(cd_time=10, at_sender=False)])
async def check_items_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """查看修仙界物品"""
    args = args.extract_plain_text()
    items_id = get_num_from_str(args)
    items_name = get_strs_from_str(args)
    if items_id:
        items_id = items_id[0]
        try:
            msg = get_item_msg(items_id)
        except KeyError:
            msg = "请输入正确的物品id！！！"
    elif items_name:
        items_id = items.items_map.get(items_name[0])
        if items_id:
            msg = get_item_msg(items_id)
        else:
            msg = f"不存在该物品的信息，请检查名字是否输入正确！"
    else:
        msg = "请输入正确的物品id！！！"

    await bot.send(event=event, message=msg)
    await check_items.finish()


@check_item_json.handle(parameterless=[Cooldown(cd_time=10, at_sender=False)])
async def check_item_json_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """查看修仙界物品"""
    args = args.extract_plain_text()
    items_id = get_num_from_str(args)
    items_name = get_strs_from_str(args)
    if items_id:
        items_id = items_id[0]
        try:
            msg = get_item_msg(items_id)
        except KeyError:
            msg = "请输入正确的物品id！！！"
    elif items_name:
        items_id = items.items_map.get(items_name[0])
        if items_id:
            msg = str(items.get_data_by_item_id(items_id))
        else:
            msg = f"不存在该物品的信息，请检查名字是否输入正确！"
    else:
        msg = "请输入正确的物品id！！！"

    await bot.send(event=event, message=msg)
    await check_item_json.finish()


@master_rename.handle(parameterless=[Cooldown(isolate_level=CooldownIsolateLevel.GROUP, parallel=1)])
async def master_rename_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """超管改名"""
    # 这里曾经是风控模块，但是已经不再需要了
    arg = args.extract_plain_text()
    user_id = get_num_from_str(arg)
    user_name = get_strs_from_str(arg)
    user_id = user_id[0] if user_id else None
    user_name = user_name[0] if user_name else None
    user_info = await sql_message.get_user_info_with_id(user_id)
    if user_info:
        msg = await sql_message.update_user_name(user_id, user_name)
        pass
    else:
        msg = f"没有ID：{user_id} 的用户！！"
    await bot.send(event=event, message=msg)
    await master_rename.finish()


@shop_off_all.handle(parameterless=[Cooldown(60, isolate_level=CooldownIsolateLevel.GROUP, parallel=1)])
async def shop_off_all_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """坊市清空"""
    group_id = get_args_num(args, 1)
    shop_data = get_shop_data(group_id)
    if not shop_data.get(group_id):
        msg = "坊市目前空空如也！"
        await bot.send(event=event, message=msg)
        await shop_off_all.finish()

    msg = "正在清空,稍等！"
    await bot.send(event=event, message=msg)

    list_msg = []
    msg = ""
    num = len(shop_data[group_id])
    for x in range(num):
        x = num - x
        if shop_data[group_id][str(x)]['user_id'] == 0:  # 这么写为了防止bot.send发送失败，不结算
            msg += f"成功下架系统物品：{shop_data[group_id][str(x)]['goods_name']}!\r"
            del shop_data[group_id][str(x)]
            save_shop(shop_data)
        else:
            await sql_message.send_back(shop_data[group_id][str(x)]['user_id'], shop_data[group_id][str(x)]['goods_id'],
                                        shop_data[group_id][str(x)]['goods_name'],
                                        shop_data[group_id][str(x)]['goods_type'], shop_data[group_id][str(x)]['stock'])
            msg += f"成功下架{shop_data[group_id][str(x)]['user_name']}的{shop_data[group_id][str(x)]['stock']}个{shop_data[group_id][str(x)]['goods_name']}!\r"
            del shop_data[group_id][str(x)]
            save_shop(shop_data)
    shop_data[group_id] = reset_dict_num(shop_data[group_id])
    save_shop(shop_data)
    list_msg.append(
        {"type": "node", "data": {"name": "执行清空坊市ing", "uin": bot.self_id,
                                  "content": msg}})
    try:
        await send_msg_handler(bot, event, list_msg)
    except ActionFailed:
        await bot.send(event=event, message=msg)
    await shop_off_all.finish()


def reset_dict_num(dict_):
    i = 1
    temp_dict = {}
    for k, v in dict_.items():
        temp_dict[i] = v
        temp_dict[i]['编号'] = i
        i += 1
    return temp_dict


def get_auction_msg(auction_id):
    item_info = items.get_data_by_item_id(auction_id)
    _type = item_info['type']
    msg = None
    if _type == "装备":
        if item_info['item_type'] == "防具":
            msg = get_armor_info_msg(auction_id, item_info)
        if item_info['item_type'] == '法器':
            msg = get_weapon_info_msg(auction_id, item_info)

    if _type == "技能":
        if item_info['item_type'] == '神通':
            msg = f"{item_info['level']}-{item_info['name']}:\r"
            msg += f"效果：{get_sec_msg(item_info)}"
        if item_info['item_type'] == '功法':
            msg = f"{item_info['level']}-{item_info['name']}\r"
            msg += f"效果：{get_main_info_msg(auction_id)[1]}"
        if item_info['item_type'] == '辅修功法':  # 辅修功法10
            msg = f"{item_info['level']}-{item_info['name']}\r"
            msg += f"效果：{get_sub_info_msg(auction_id)[1]}"

    if _type == "神物":
        msg = f"{item_info['name']}\r"
        msg += f"效果：{item_info['desc']}"

    if _type == "丹药":
        msg = f"{item_info['name']}\r"
        msg += f"效果：{item_info['desc']}"

    return msg
