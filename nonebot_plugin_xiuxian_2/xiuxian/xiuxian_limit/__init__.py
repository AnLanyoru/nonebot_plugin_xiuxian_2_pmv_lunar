from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent
)
from nonebot.params import CommandArg

from .limit_database import limit_data, limit_handle
from ..xiuxian_utils.clean_utils import get_num_from_str
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import (
    check_user, send_msg_handler
)
from ..xiuxian_utils.xiuxian2_handle import sql_message

limit = limit_data
offset = on_command('补偿', priority=1, permission=GROUP, block=True)
offset_get = on_command('领取补偿', priority=1, permission=GROUP, block=True)
get_log = on_command('查日志', aliases={"日志查询", "查询日志", "查看日志", "日志记录"}, priority=1, permission=GROUP,
                     block=True)
get_shop_log = on_command('坊市日志', aliases={"查询坊市日志", "查看坊市日志"}, priority=1, permission=GROUP,
                          block=True)


@offset.handle(parameterless=[Cooldown()])
async def offset_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    user_info = await check_user(event)

    user_id = user_info['user_id']
    msg_list = await limit_handle.get_all_user_offset_msg(user_id)  # 存入需要被翻页的数据
    if msg_list:
        page_msg = get_num_from_str(args.extract_plain_text())
        items_all = len(msg_list)
        per_item = 3  # 每页物品数量
        page_all = ((items_all // per_item) + 1) if (items_all % per_item != 0) else (items_all // per_item)  # 总页数
        page = int(page_msg[0]) if page_msg else 1
        if page_all < page:
            msg = "\r补偿没有那么多页！！！"
            await bot.send(event=event, message=msg)
            await offset.finish()
        item_num = page * per_item - per_item
        item_num_end = item_num + per_item
        msg_hand = ["当前可领补偿如下："]  # 页面头
        page_info = [
            f"第{page}/{page_all}页\r——tips——\r可以发送 补偿 页数 来查看更多页\r领取补偿 补偿id 来领取补偿哦"]  # 页面尾
        msg_list = msg_hand + msg_list[item_num:item_num_end] + page_info
        pass
    else:
        msg = "\r补偿列表当前空空如也！！！"
        await bot.send(event=event, message=msg)
        await offset.finish()
    await send_msg_handler(bot, event, '补偿列表', bot.self_id, msg_list)
    await offset.finish()


@offset_get.handle(parameterless=[Cooldown(cd_time=3)])
async def offset_get_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    user_info = await check_user(event)

    user_id = user_info['user_id']
    num_msg = get_num_from_str(args.extract_plain_text())
    num = int(num_msg[0]) if num_msg else 1
    offset_info = await limit_data.get_offset_by_id(num)
    if not offset_info:  # 补偿合理性检测
        msg = f"不存在ID为 {num}，的补偿，请检查！！"
        await bot.send(event=event, message=msg)
        await offset.finish()
    is_pass, msg = await limit_handle.update_user_offset(user_id, num)  # 申领检查
    if not is_pass:
        await bot.send(event=event, message=msg)
        await offset.finish()
    # 检查通过，发放奖励
    items_info = offset_info.get("offset_items")
    msg = "领取补偿成功：\r获取了：\r"
    for item_id in items_info:
        item_info = items.get_data_by_item_id(item_id)
        if item_info:
            item_name = item_info['name']
            item_type = item_info['type']
            item_num = items_info[int(item_id)]
            await sql_message.send_back(user_id, int(item_id), item_name, item_type, item_num, 1)
            msg += f"\r{item_name} {item_num}个！"
        else:
            msg += f"\r不存在的物品 0个"
    if offset_info['daily_update']:
        msg += "\r明天还可继续领取哦！！"
    await bot.send(event=event, message=msg)
    await offset.finish()


@get_log.handle(parameterless=[Cooldown(cd_time=30)])
async def offset_(bot: Bot, event: GroupMessageEvent):
    user_info = await check_user(event)

    user_id = user_info['user_id']
    logs = await limit_handle.get_user_log_data(user_id)
    if logs:
        await send_msg_handler(bot, event, '日志', bot.self_id, logs)
        await get_log.finish()
    else:
        msg = "未查询到道友的日志信息！"
        await bot.send(event=event, message=msg)
        await get_log.finish()


@get_shop_log.handle(parameterless=[Cooldown(cd_time=30)])
async def offset_(bot: Bot, event: GroupMessageEvent):
    user_info = await check_user(event)

    user_id = user_info['user_id']
    logs = await limit_handle.get_user_shop_log_data(user_id)
    if logs:
        await send_msg_handler(bot, event, '坊市日志', bot.self_id, logs)
        await get_shop_log.finish()
    else:
        msg = "未查询到道友的坊市日志信息！"
        await bot.send(event=event, message=msg)
        await get_shop_log.finish()
