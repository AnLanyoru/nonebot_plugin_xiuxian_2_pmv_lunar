import time

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent,
    Message
)
from nonebot.params import CommandArg

from .shop_database import create_goods, fetch_goal_goods_data, fetch_goods_data_by_id, mark_goods, \
    fetch_goods_min_price_type, fetch_self_goods_data, create_goods_many, fetch_self_goods_data_all, \
    fetch_self_goods_data_all_type, fetch_goal_goods_data_many
from ..types import UserInfo
from ..utils.shop_util import back_pick_tool
from ..xiuxian_utils.clean_utils import get_strs_from_str, get_args_num, simple_md, number_to, three_md, \
    msg_handler, main_md, get_args_uuid, get_paged_item, number_to_msg
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import (
    check_user
)
from ..xiuxian_utils.xiuxian2_handle import (
    sql_message
)

shop_goods_help = on_command("市场帮助", aliases={'坊市帮助'}, priority=5, permission=GROUP, block=True)
shop_goods_send = on_command("市场上架", aliases={'坊市上架'}, priority=5, permission=GROUP, block=True)
shop_goods_buy = on_command("市场购买", aliases={"坊市购买"}, priority=5, permission=GROUP, block=True)
my_shop_goods = on_command("我的市场", aliases={"我的坊市"}, priority=5, permission=GROUP, block=True)
shop_goods_back = on_command("市场下架", aliases={"坊市下架"}, priority=5, permission=GROUP, block=True)
shop_goods_buy_sure = on_command("确认市场购买", priority=5, permission=GROUP, block=True)
shop_goods_send_sure = on_command("确认市场上架", priority=5, permission=GROUP, block=True)
shop_goods_check = on_command("市场查看",
                              aliases={"坊市查看", "查看坊市", "查看市场"},
                              priority=5, permission=GROUP, block=True)
shop_goods_send_many = on_command("快速市场上架", aliases={'快速坊市上架', '市场快速上架', '坊市快速上架'}, priority=5,
                                  permission=GROUP, block=True)
shop_goods_buy_many = on_command("快速市场购买", aliases={'快速坊市购买', '市场快速购买', '坊市快速购买'}, priority=5,
                                 permission=GROUP, block=True)
shop_goods_back_many = on_command("快速市场下架", aliases={'快速坊市下架', '市场快速下架', '坊市快速下架'}, priority=5,
                                  permission=GROUP, block=True)

TYPE_DEF = {'功法': ('功法', '神通', '辅修功法'),
            '装备': ('法器', '防具'),
            '丹药': ('合成丹药',),
            '主功法': ('功法',),
            '辅修': ('辅修功法',)}

user_shop_temp_pick_dict: dict[int, list[str]] = {}


@shop_goods_help.handle(parameterless=[Cooldown(stamina_cost=0)])
async def shop_goods_help_(bot: Bot, event: GroupMessageEvent):
    """市场快速上架"""
    msg = three_md('市场帮助\r'
                   '基础指令：\r'
                   '1.', '市场查看', '市场查看',
                   '\r2.', '市场购买', '市场购买',
                   '\r3.', '市场上架', '市场上架',
                   '\r4.我的市场\r'
                   '便捷指令：\r'
                   '1.快速市场上架\r'
                   ' 🔹快速市场上架 物品类型 单价\r'
                   ' 快速上架符合对应类型的物品，可多个类型'
                   '2.快速市场购买\r'
                   ' 🔹快速坊市购买 物品名称 数量\r'
                   ' 快速购买对应数量的物品')
    await bot.send(event=event, message=msg)
    await shop_goods_help.finish()


@shop_goods_send_many.handle(parameterless=[Cooldown(stamina_cost=0)])
async def shop_goods_send_many_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """市场快速上架"""
    user_info: UserInfo = await check_user(event)

    user_id = user_info['user_id']
    user_stone = user_info['stone']

    arg_str = args.extract_plain_text()
    price = get_args_num(arg_str, 1, 500000)
    strs = get_strs_from_str(arg_str)
    if not strs:
        msg = '请输入要上架的物品类别！'
        await bot.send(event=event, message=msg)
        await shop_goods_send_many.finish()
    # 价格合理性检测
    if price % 100000:
        msg = '价格必须为10w的整数倍！'
        await bot.send(event=event, message=msg)
        await shop_goods_send_many.finish()
    if price < 500000:
        msg = '价格最低为50w灵石！'
        await bot.send(event=event, message=msg)
        await shop_goods_send_many.finish()
    user_back_items: list[dict] = await sql_message.get_back_msg(user_id)
    if not user_back_items:
        msg = '道友的背包空空如也！！'
        await bot.send(event=event, message=msg)
        await shop_goods_send_many.finish()
    # 解析物品
    all_pick_items: dict[int, int] = back_pick_tool(user_back_items, strs)
    # 检查手续费
    handle_price: int = int(price * 0.2) * sum(all_pick_items.values())
    if user_stone < handle_price:
        msg = f'道友的灵石不足以支付上架物品花费的手续费{number_to(handle_price)}灵石！！'
        await bot.send(event=event, message=msg)
        await shop_goods_send_many.finish()
    await sql_message.update_ls(user_id, handle_price, 2)
    await sql_message.decrease_user_item(user_id, all_pick_items, False)
    await create_goods_many(user_id, all_pick_items, price)
    item_msg: str = items.change_id_num_dict_to_msg(all_pick_items)
    msg = f"成功上架：{item_msg}\r单价：{number_to(price)}灵石\r收取道友{number_to(handle_price)}灵石手续费\r"
    msg = simple_md(msg, '继续上架', '市场快速上架', '物品')
    await bot.send(event=event, message=msg)
    await shop_goods_send_many.finish()


@shop_goods_back.handle(parameterless=[Cooldown(stamina_cost=0)])
async def shop_goods_back_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """市场下架"""
    user_info = await check_user(event)

    user_id = user_info['user_id']

    arg_str = args.extract_plain_text()
    strs: list = get_strs_from_str(arg_str)
    item_no: int = get_args_num(arg_str)
    if user_id in user_shop_temp_pick_dict:
        user_shop_temp_pick: list[str] = user_shop_temp_pick_dict[user_id]
        if item_no and item_no <= len(user_shop_temp_pick):
            strs: str = user_shop_temp_pick[item_no - 1]
    if not strs:
        msg = '请输入要下架的物品名称！'
        await bot.send(event=event, message=msg)
        await shop_goods_back.finish()
    # 解析物品名称
    item_name = strs[0] if isinstance(strs, list) else strs
    item_id = items.items_map.get(item_name)
    if not item_id:
        msg = '不存在的物品！'
        await bot.send(event=event, message=msg)
        await shop_goods_back.finish()
    goods_info = await fetch_self_goods_data(user_id=user_id, item_id=item_id)
    if not goods_info:
        msg = '道友没有在出售该物品！'
        await bot.send(event=event, message=msg)
        await shop_goods_back.finish()
    goods_id = goods_info['id']
    shop_result = await mark_goods(goods_id=goods_id, mark_user_id=user_id)
    if shop_result == 'UPDATE 0':
        msg = simple_md('道友的物品已被',
                        '购买', '市场购买',
                        f'！！')
        await bot.send(event=event, message=msg)
        await shop_goods_buy_sure.finish()
    await sql_message.send_item(user_id, {item_id: 1}, False)
    msg = f"成功下架{item_name} 1 \r"
    msg = simple_md(msg, '继续下架物品', f"市场下架", '。')
    await bot.send(event=event, message=msg)
    await shop_goods_back.finish()


@shop_goods_check.handle(parameterless=[Cooldown(stamina_cost=0)])
async def shop_goods_check_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """市场查看"""
    user_info = await check_user(event)

    user_id = user_info['user_id']

    arg_str = args.extract_plain_text()
    strs = get_strs_from_str(arg_str)
    page = get_args_num(arg_str, default=1)
    if not strs:
        msg = three_md('请输入要查看的物品类型：\r',
                       '功法', '市场查看功法', "|",
                       '装备', '市场查看装备', '|',
                       '丹药', '市场查看丹药', '\r其他类型请手动输入')
        await bot.send(event=event, message=msg)
        await shop_goods_check.finish()
    item_type = strs[0]
    if item_type in ['功法', '装备', '丹药']:
        all_type = TYPE_DEF[item_type]
    else:
        all_type = tuple(strs)
    item_price_data = await fetch_goods_min_price_type(user_id=user_id, item_type=all_type)
    item_price_data = get_paged_item(msg_list=item_price_data, page=page, per_page_item=24)
    item_price_data.sort(key=lambda item_per: item_per['item_id'])
    msg_list: list[str] = []
    temp_pick_list: list[str] = []
    item_no = 0
    for item_price_data_per in item_price_data:
        item_name = items.get_data_by_item_id(item_price_data_per['item_id'])['name']
        temp_pick_list.append(item_name)
        item_no += 1
        msg_per = (f"编号: {item_no} {item_name} "
                   f"价格：{number_to(item_price_data_per['item_price'])}"
                   f"|{item_price_data_per['item_price']}")
        msg_list.append(msg_per)
    user_shop_temp_pick_dict[user_id] = temp_pick_list
    text = msg_handler(msg_list)
    type_msg = '、'.join(all_type)
    msg_head = f"{type_msg}市场情况"
    msg = main_md(msg_head, text,
                  '上架物品', '市场上架',
                  '当前灵石', '灵石',
                  '下一页', f"市场查看{type_msg} {page + 1}",
                  '市场购买 物品名称|物品编号', '市场购买')
    await bot.send(event=event, message=msg)
    await shop_goods_check.finish()


@my_shop_goods.handle(parameterless=[Cooldown(stamina_cost=0)])
async def my_shop_goods_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """市场查看"""
    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_name = user_info['user_name']

    arg_str = args.extract_plain_text()
    strs = get_strs_from_str(arg_str)
    page = get_args_num(arg_str, default=1)
    if not strs:
        # 未指定则获取所有
        item_price_data = await fetch_self_goods_data_all(user_id=user_id)
        type_msg: str = ''
    else:
        item_type = strs[0]
        if item_type in ['功法', '装备', '丹药']:
            all_type = TYPE_DEF[item_type]
        else:
            all_type = tuple(strs)
        item_price_data = await fetch_self_goods_data_all_type(user_id=user_id, item_type=all_type)
        type_msg: str = '、'.join(all_type)
    item_price_data = get_paged_item(msg_list=item_price_data, page=page, per_page_item=24)
    item_price_data.sort(key=lambda item_per: item_per['item_id'])
    msg_list: list[str] = []
    temp_pick_list: list[str] = []
    item_no = 0
    for item_price_data_per in item_price_data:
        item_name = items.get_data_by_item_id(item_price_data_per['item_id'])['name']
        temp_pick_list.append(item_name)
        item_no += 1
        msg_per = (f"编号: {item_no} {item_name} "
                   f"价格：{number_to(item_price_data_per['item_price'])}"
                   f"|{item_price_data_per['item_price']}")
        msg_list.append(msg_per)
    user_shop_temp_pick_dict[user_id] = temp_pick_list
    text = msg_handler(msg_list)
    msg_head = f"{user_name}道友的{type_msg}市场上架物品情况"
    msg = main_md(msg_head, text,
                  '上架物品', '市场上架',
                  '当前灵石', '灵石',
                  '下一页', f"我的市场{type_msg} {page + 1}",
                  '市场下架 物品名称|物品编号', '市场下架')
    await bot.send(event=event, message=msg)
    await my_shop_goods.finish()


@shop_goods_send_sure.handle(parameterless=[Cooldown(stamina_cost=0)])
async def shop_goods_send_sure_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """市场上架"""
    user_info = await check_user(event)

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
    if price < 500000:
        msg = '价格最低为50w灵石！'
        await bot.send(event=event, message=msg)
        await shop_goods_send_many.finish()
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
    user_info = await check_user(event)

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
    if price < 500000:
        msg = '价格最低为50w灵石！'
        await bot.send(event=event, message=msg)
        await shop_goods_send_many.finish()
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
    if not item_in_back:
        msg = f'道友没有{item_name}！！'
        await bot.send(event=event, message=msg)
        await shop_goods_send.finish()
    own_num = item_in_back['goods_num'] - item_in_back['bind_num']
    if own_num < 1:
        msg = f'道友的{item_name}不足！！'
        await bot.send(event=event, message=msg)
        await shop_goods_send.finish()
    msg = f"上架：{item_name} 1个 \r价格：{number_to(price)}灵石\r将收取道友{number_to(handle_price)}灵石手续费\r请"
    msg = simple_md(msg, '确认', f'确认市场上架{item_name} {price}', '操作')
    await bot.send(event=event, message=msg)
    await shop_goods_send.finish()


@shop_goods_buy.handle(parameterless=[Cooldown(stamina_cost=0)])
async def shop_goods_buy_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """市场上架"""
    user_info: UserInfo = await check_user(event)

    user_id: int = user_info['user_id']
    user_stone: int = user_info['stone']

    arg_str: str = args.extract_plain_text()
    item_no: int = get_args_num(arg_str)
    strs = get_strs_from_str(arg_str)
    if user_id in user_shop_temp_pick_dict:
        user_shop_temp_pick: list[str] = user_shop_temp_pick_dict[user_id]
        if item_no and item_no <= len(user_shop_temp_pick):
            strs = user_shop_temp_pick[item_no - 1]
    if not strs:
        msg = '请输入要购买的物品名称！'
        await bot.send(event=event, message=msg)
        await shop_goods_buy.finish()
    # 解析物品名称
    item_name = strs[0] if isinstance(strs, list) else strs
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
    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_stone = user_info['stone']

    arg_str = args.extract_plain_text()
    goods_id = get_args_uuid(arg_str, default=0)
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


@shop_goods_buy_many.handle(parameterless=[Cooldown(stamina_cost=0)])
async def shop_goods_buy_many_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """市场快速购买"""
    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_stone = user_info['stone']

    arg_str = args.extract_plain_text()
    strs = get_strs_from_str(arg_str)
    want_price = get_args_num(arg_str, default=500000, no=1)
    want_num = get_args_num(arg_str, default=1, no=2)
    if user_stone < (want_price * want_num):
        msg = simple_md('道友的灵石不足以支持本次',
                        '批量购买', '快速市场购买',
                        f'！！')
        await bot.send(event=event, message=msg)
        await shop_goods_buy_many.finish()
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
    start_time = time.time()
    msg = f'尝试以{number_to_msg(want_price)}为最高价购买{want_num}个{item_name}'
    if want_num > 100:
        want_num = 100
        msg += '\r单次快速购买最多只能购买100个物品哦！！'
    sum_price = 0
    sum_num = 0
    send_stone_dict: dict[int, int] = {}
    goods_info_list = await fetch_goal_goods_data_many(user_id=user_id, item_id=item_id, num=want_num)
    for goods_info in goods_info_list:
        goods_id = goods_info['id']
        item_id = goods_info['item_id']
        price = goods_info['item_price']
        seller_id = goods_info['owner_id']
        item_info = items.get_data_by_item_id(item_id)
        item_name = item_info['name']
        if price > want_price:
            break
        shop_result = await mark_goods(goods_id=goods_id, mark_user_id=user_id)
        if shop_result == 'UPDATE 0':
            msg = f'\r{item_name} 1 购买失败！物品已被购买'
            continue
        msg += f"\r{item_name} 1 购买成功！花费{number_to(price)}灵石"
        send_stone_dict[seller_id] = price
        sum_price += price
        sum_num += 1
    if not sum_num:
        msg = '该物品市场中没有人在出售！'
        await bot.send(event=event, message=msg)
        await shop_goods_buy.finish()
    await sql_message.update_stone_many(send_stone_dict, 1)
    await sql_message.update_ls(user_id, sum_price, 2)
    await sql_message.send_item(user_id, {item_id: sum_num}, False)
    end_time = time.time()
    use_time = (end_time - start_time) * 1000
    tips = f"\r成功购买{item_name} {sum_num}个 花费: {number_to_msg(sum_price)}灵石\r耗时：{use_time}"
    msg = main_md(
        tips, msg,
        '上架物品', '市场上架',
        '查看市场', '查看市场',
        '当前灵石', '灵石',
        '继续购买该物品',
        f"快速市场购买{item_name} {want_price} {want_num}")
    await bot.send(event=event, message=msg)
    await shop_goods_buy_many.finish()
