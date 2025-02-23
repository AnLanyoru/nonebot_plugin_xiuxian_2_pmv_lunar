import asyncio

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent,
    Message
)
from nonebot.params import CommandArg

from .shop_database import create_goods, fetch_goal_goods_data, fetch_goods_data_by_id, mark_goods
from ..xiuxian_utils.clean_utils import get_strs_from_str, get_args_num, simple_md, number_to
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import (
    check_user
)
from ..xiuxian_utils.xiuxian2_handle import (
    sql_message
)

shop_goods_send = on_command("市场上架", aliases={'坊市上架'}, priority=5, permission=GROUP, block=True)
shop_goods_buy = on_command("市场购买", aliases={"坊市购买"}, priority=5, permission=GROUP, block=True)
shop_goods_buy_sure = on_command("确认市场购买", priority=5, permission=GROUP, block=True)
shop_goods_send_sure = on_command("确认市场上架", priority=5, permission=GROUP, block=True)
shop_goods_check = on_command("市场查看", aliases={"坊市查看", "查看坊市", "查看市场"}, priority=5, permission=GROUP,
                              block=True)


@shop_goods_send_sure.handle(parameterless=[Cooldown(stamina_cost=0)])
async def shop_goods_send_sure_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """市场上架"""
    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    user_stone = user_info['stone']

    arg_str = args.extract_plain_text()
    price = get_args_num(arg_str, 1, 500000)
    strs = get_strs_from_str(arg_str)
    if not strs:
        msg = '请输入要上架的物品名称！'
        await bot.send(event=event, message=msg)
        await shop_goods_send_sure.finish()
    # 价格合理性检测
    if price % 100000:
        msg = '价格必须为10w的整数倍！'
        await bot.send(event=event, message=msg)
        await shop_goods_send_sure.finish()
    # 解析物品名称
    item_name = strs[0]
    item_id = items.items_map.get(item_name)
    if not item_id:
        msg = '不存在的物品！'
        await bot.send(event=event, message=msg)
        await shop_goods_send_sure.finish()
    # 检查手续费
    handle_price = int(price * 0.2)
    if user_stone < handle_price:
        msg = f'道友的灵石不足以支付上架物品花费的手续费{number_to(handle_price)}灵石！！'
        await bot.send(event=event, message=msg)
        await shop_goods_send_sure.finish()
    item_in_back = await sql_message.get_item_by_good_id_and_user_id(user_id, item_id)
    own_num = item_in_back['goods_num'] - item_in_back['bind_num']
    if own_num < 1:
        msg = f'道友的{item_name}不足！！'
        await bot.send(event=event, message=msg)
        await shop_goods_send_sure.finish()
    item_info = items.get_data_by_item_id(item_id)
    item_type = item_info['item_type']
    await create_goods(user_id, item_id, item_type, price)
    msg = f"成功上架：{item_name} 1个 \r价格：{number_to(price)}灵石\r收取道友{number_to(handle_price)}灵石手续费\r"
    msg = simple_md(msg, '继续上架', '市场上架', '物品')
    await sql_message.update_ls(user_id, handle_price, 2)
    await sql_message.decrease_user_item(user_id, {item_id: 1}, False)
    await bot.send(event=event, message=msg)
    await shop_goods_send_sure.finish()


@shop_goods_send.handle(parameterless=[Cooldown(stamina_cost=0)])
async def shop_goods_send_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """市场上架"""
    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    user_stone = user_info['stone']

    arg_str = args.extract_plain_text()
    price = get_args_num(arg_str, 1, 500000)
    strs = get_strs_from_str(arg_str)
    if not strs:
        msg = '请输入要上架的物品名称！'
        await bot.send(event=event, message=msg)
        await shop_goods_send.finish()
    # 价格合理性检测
    if price % 100000:
        msg = '价格必须为10w的整数倍！'
        await bot.send(event=event, message=msg)
        await shop_goods_send.finish()
    # 解析物品名称
    item_name = strs[0]
    item_id = items.items_map.get(item_name)
    if not item_id:
        msg = '不存在的物品！'
        await bot.send(event=event, message=msg)
        await shop_goods_send.finish()
    # 检查手续费
    handle_price = int(price * 0.2)
    if user_stone < handle_price:
        msg = f'道友的灵石不足以支付上架物品花费的手续费{number_to(handle_price)}灵石！！'
        await bot.send(event=event, message=msg)
        await shop_goods_send.finish()
    item_in_back = await sql_message.get_item_by_good_id_and_user_id(user_id, item_id)
    own_num = item_in_back['goods_num'] - item_in_back['bind_num']
    if own_num < 1:
        msg = f'道友的{item_name}不足！！'
        await bot.send(event=event, message=msg)
        await shop_goods_send.finish()
    msg = f"上架：{item_name} 1个 \r价格：{number_to(price)}灵石\r将收取道友{number_to(handle_price)}灵石手续费\r请"
    msg = simple_md(msg, '确认', f'确认市场上架{item_name}', '操作')
    await bot.send(event=event, message=msg)
    await shop_goods_send.finish()


@shop_goods_buy.handle(parameterless=[Cooldown(stamina_cost=0)])
async def shop_goods_buy_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """市场上架"""
    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    user_stone = user_info['stone']

    arg_str = args.extract_plain_text()
    strs = get_strs_from_str(arg_str)
    if not strs:
        msg = '请输入要购买的物品名称！'
        await bot.send(event=event, message=msg)
        await shop_goods_buy.finish()
    # 解析物品名称
    item_name = strs[0]
    item_id = items.items_map.get(item_name)
    if not item_id:
        msg = '不存在的物品！'
        await bot.send(event=event, message=msg)
        await shop_goods_buy.finish()
    goods_info = await fetch_goal_goods_data(user_id=user_id, item_id=item_id)
    if not goods_info:
        msg = '该物品市场中没有人在出售！'
        await bot.send(event=event, message=msg)
        await shop_goods_buy.finish()
    price = goods_info['item_price']
    if user_stone < price:
        msg = simple_md('道友的灵石不足以',
                        '购买', '市场购买',
                        f'市场中的{item_name}\r该物品的市场最低价为{number_to(price)}灵石！！')
        await bot.send(event=event, message=msg)
        await shop_goods_buy.finish()
    item_info = items.get_data_by_item_id(item_id)
    msg = f"{item_name}的市场情况：\r效果：{item_info.get('desc', '无')} \r最低价格：{number_to(price)}灵石\r"
    msg = simple_md(msg, '确认购买', f"确认市场购买{goods_info['id']}", '该物品')
    await bot.send(event=event, message=msg)
    await shop_goods_buy.finish()


@shop_goods_buy_sure.handle(parameterless=[Cooldown(stamina_cost=0)])
async def shop_goods_buy_sure_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """市场上架"""
    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    user_stone = user_info['stone']

    arg_str = args.extract_plain_text()
    goods_id = get_args_num(arg_str, default=0)
    if not goods_id:
        msg = '请输入要购买的商品id！'
        await bot.send(event=event, message=msg)
        await shop_goods_buy_sure.finish()
    goods_info = await fetch_goods_data_by_id(user_id=user_id, item_shop_id=goods_id)
    if not goods_info:
        msg = '不存在的商品！'
        await bot.send(event=event, message=msg)
        await shop_goods_buy_sure.finish()
    item_id = goods_info['item_id']
    price = goods_info['item_price']
    seller_id = goods_info['owner_id']
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    if user_stone < price:
        msg = simple_md('道友的灵石不足以',
                        '购买', '市场购买',
                        f'{item_name}\r购买该物品需要{number_to(price)}灵石！！')
        await bot.send(event=event, message=msg)
        await shop_goods_buy_sure.finish()
    shop_result = await mark_goods(goods_id=goods_id, mark_user_id=user_id)
    await bot.send(event=event, message="获取到商品信息，尝试购买")
    await asyncio.sleep(5)
    if shop_result == 'UPDATE 0':
        msg = simple_md('物品已被',
                        '购买', '市场购买',
                        f'！！')
        await bot.send(event=event, message=msg)
        await shop_goods_buy_sure.finish()
    msg = f"{item_name} 1 购买成功！\r花费{number_to(price)}灵石\r"
    msg = simple_md(msg, '继续购买', f"市场购买{item_name}", '。')
    await sql_message.update_ls(seller_id, price, 1)
    await sql_message.update_ls(user_id, price, 2)
    await sql_message.send_item(user_id, {item_id: 1}, False)
    await bot.send(event=event, message=msg)
    await shop_goods_buy_sure.finish()
