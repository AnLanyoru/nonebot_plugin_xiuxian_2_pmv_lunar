from nonebot import on_command, on_fullmatch
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
)
from nonebot.params import CommandArg, RawCommand
from nonebot.permission import SUPERUSER

from .back_util import (
    get_user_main_back_msg, get_use_equipment_sql, get_shop_data, save_shop,
    get_item_msg, get_item_msg_rank, check_use_elixir,
    get_use_jlq_msg, get_no_use_equipment_sql, get_use_tool_msg,
    get_user_main_back_msg_easy, get_user_back_msg)
from ..xiuxian_config import XiuConfig, convert_rank
from ..xiuxian_limit import limit_handle
from ..xiuxian_mixelixir.mixelixirutil import mix_user_temp, AlchemyFurnace
from ..xiuxian_utils.clean_utils import (
    get_args_num, get_num_from_str,
    get_strs_from_str, get_paged_msg, main_md,
    msg_handler, three_md)
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown, CooldownIsolateLevel
from ..xiuxian_utils.utils import (
    check_user, number_to,
    get_id_from_str, check_user_type
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

goods_re_root = on_command("炼金", priority=6, permission=GROUP, block=True)
goods_re_root_fast = on_command("快速炼金", aliases={"批量炼金"}, priority=6, permission=GROUP, block=True)
main_back = on_command('我的背包', aliases={'我的物品', '背包'}, priority=2, permission=GROUP, block=True)
skill_back = on_command('功法背包', priority=2, permission=GROUP, block=True)
check_back = on_command('别人的背包', aliases={'检查背包'}, priority=2, permission=SUPERUSER, block=True)
use = on_command("使用", priority=15, permission=GROUP, block=True)
no_use_zb = on_command("换装", aliases={"卸载"}, priority=5, permission=GROUP, block=True)
back_help = on_command("背包帮助", aliases={"坊市帮助"}, priority=8, permission=GROUP, block=True)
xiuxian_stone = on_fullmatch("灵石", priority=4, permission=GROUP, block=True)
master_rename = on_command("超管改名", priority=2, permission=SUPERUSER, block=True)
check_items = on_command("查看", aliases={"查", "查看物品", "查看效果", "详情"}, priority=25, permission=GROUP,
                         block=True)
back_fix = on_fullmatch("背包修复", priority=1, permission=GROUP, block=True)
test_md = on_command("测试模板", priority=25, permission=SUPERUSER, block=True)
check_item_json = on_command("物品结构", aliases={"json"}, priority=25, permission=SUPERUSER, block=True)
gm_goods_delete = on_command("回收", aliases={"没收"}, priority=6, permission=SUPERUSER, block=True)

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


@gm_goods_delete.handle(parameterless=[Cooldown()])
async def gm_goods_delete_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """炼金"""
    strs = args.extract_plain_text()
    args = get_strs_from_str(strs)
    user_id = await get_id_from_str(args, 2)
    num = get_num_from_str(strs)
    if num:
        num = int(num[0])
    else:
        num = 1
    if args:
        goods_name = args[0]
    else:
        goods_name = None
    if goods_name is None:
        msg = "请输入要没收的物品！"
        await bot.send(event=event, message=msg)
        await gm_goods_delete.finish()
    if not user_id:
        msg = "请输入正确的用户道号！"
        await bot.send(event=event, message=msg)
        await gm_goods_delete.finish()

    back_msg = await sql_message.get_back_msg(user_id)  # 背包sql信息,list(back)
    if back_msg is None:
        msg = "对方的背包空空如也！"
        await bot.send(event=event, message=msg)
        await gm_goods_delete.finish()
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
        msg = f"请检查该道具 {goods_name} 是否在对方背包内！"
        await bot.send(event=event, message=msg)
        await gm_goods_delete.finish()

    if goods_num < num:
        msg = f"对方的包内没有那么多 {goods_name} ！"
        await bot.send(event=event, message=msg)
        await gm_goods_delete.finish()

    if goods_type == "装备" and int(goods_state) == 1 and int(goods_num) == 1:
        msg = f"装备：{goods_name}已经被对方装备在身，无法没收！"
        await bot.send(event=event, message=msg)
        await gm_goods_delete.finish()

    await sql_message.update_back_j(user_id, goods_id, num=num, use_key=0)
    msg = f"物品：{goods_name} 数量：{num} 没收成功"
    await bot.send(event=event, message=msg)
    await gm_goods_delete.finish()


@test_md.handle()
async def md_test_(bot: Bot, event: GroupMessageEvent):
    msg = three_md(
        '<qqbot-cmd-input text="', '指令1指令0" /> a[aa', '悬赏令接取1', "测试",
        '指令2', '悬赏令接取2', "测试",
        '指令3', '悬赏令接取3', "测试",
    )
    await bot.send(event, msg)
    await test_md.finish()


@back_fix.handle(parameterless=[Cooldown(parallel_block=True)])
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


@back_help.handle(parameterless=[Cooldown()])
async def back_help_(bot: Bot, event: GroupMessageEvent):
    """背包帮助"""
    msg = __back_help__
    await bot.send(event=event, message=msg)
    await back_help.finish()


@xiuxian_stone.handle(parameterless=[Cooldown()])
async def xiuxian_stone_(bot: Bot, event: GroupMessageEvent):
    """我的灵石信息"""
    _, user_info, _ = await check_user(event)
    msg = f"当前灵石：{number_to(user_info['stone'])} | {user_info['stone']}"
    await bot.send(event=event, message=msg)
    await xiuxian_stone.finish()


@goods_re_root.handle(parameterless=[Cooldown()])
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


@goods_re_root_fast.handle(parameterless=[Cooldown()])
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


@main_back.handle(parameterless=[Cooldown()])
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


@skill_back.handle(parameterless=[Cooldown()])
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


@check_back.handle(parameterless=[Cooldown()])
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


@no_use_zb.handle(parameterless=[Cooldown()])
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


@use.handle(parameterless=[Cooldown()])
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

    # 使用实现
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
            if int(user_buff_info['sec_buff']) == goods_id:
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
            if int(user_buff_info['main_buff']) == goods_id:
                msg = f"道友已学会该功法：{skill_info['name']}，请勿重复学习！"
            else:  # 学习sql
                await sql_message.update_back_j(user_id, goods_id, use_key=2)
                await sql_message.updata_user_main_buff(user_id, goods_id)
                msg = f"恭喜道友学会功法：{skill_info['name']}！"
        elif skill_type == "辅修功法":  # 辅修功法1
            if int(user_buff_info['sub_buff']) == goods_id:
                msg = f"道友已学会该辅修功法：{skill_info['name']}，请勿重复学习！"
            else:  # 学习sql
                await sql_message.update_back_j(user_id, goods_id, use_key=2)
                await sql_message.updata_user_sub_buff(user_id, goods_id)
                msg = f"恭喜道友学会辅修功法：{skill_info['name']}！"
        else:
            msg = "发生未知错误！"
        await bot.send(event=event, message=msg)
        await use.finish()
    elif goods_type in ["丹药", "合成丹药"]:
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

        await sql_message.send_back(user_id, int(goods_id1), goods_name1, goods_type1, 1 * num, 1)  # 增加用户道具
        await sql_message.send_back(user_id, int(goods_id2), goods_name2, goods_type2, 2 * num, 1)
        await sql_message.send_back(user_id, int(goods_id3), goods_name3, goods_type3, 2 * num, 1)
        await sql_message.update_back_j(user_id, int(goods_id), num, 0)
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
    elif goods_type == "炼丹炉":
        if num > int(goods_num):
            msg = f"道友没有{item_name}！"
            await bot.send(event=event, message=msg)
            await use.finish()

        # 检查是否空闲
        is_type, msg = await check_user_type(user_id, 0)
        if not is_type:
            await bot.send(event=event, message=msg)
            await use.finish()

        # 进入炼丹状态
        await sql_message.in_closing(user_id, 7)
        mix_user_temp[user_id] = AlchemyFurnace(goods_id)
        msg = f'道友取出{item_name}, 开始炼丹'

        # 保存丹炉数据
        await mix_user_temp[user_id].save_data(user_id)
        await bot.send(event=event, message=msg)
        await use.finish()
    else:
        msg = '该类型物品调试中，未开启！'
        await bot.send(event=event, message=msg)
        await use.finish()


@check_items.handle(parameterless=[Cooldown()])
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


@check_item_json.handle(parameterless=[Cooldown()])
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
    user_id = int(user_id[0]) if user_id else None
    user_name = user_name[0] if user_name else None
    user_info = await sql_message.get_user_info_with_id(user_id)
    if user_info:
        msg = await sql_message.update_user_name(user_id, user_name)
        pass
    else:
        msg = f"没有ID：{user_id} 的用户！！"
    await bot.send(event=event, message=msg)
    await master_rename.finish()


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
