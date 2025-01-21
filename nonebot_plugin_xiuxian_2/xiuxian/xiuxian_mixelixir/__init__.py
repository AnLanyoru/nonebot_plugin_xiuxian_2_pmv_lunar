import random
import re
import time
from datetime import datetime

from nonebot import on_command, on_fullmatch
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent,
    ActionFailed, Message
)
from nonebot.params import CommandArg, RawCommand
from nonebot.permission import SUPERUSER

from .mix_elixir_config import MIXELIXIRCONFIG
from .mix_elixir_database import create_user_mix_elixir_info, get_user_mix_elixir_info
from .mixelixirutil import AlchemyFurnace, get_user_alchemy_furnace, move_mix_user
from ..xiuxian_back.back_util import get_user_elixir_back_msg, get_user_yaocai_back_msg, get_user_yaocai_back_msg_easy
from ..xiuxian_config import convert_rank
from ..xiuxian_database.database_connect import database
from ..xiuxian_utils.clean_utils import get_strs_from_str, get_args_num, get_paged_msg, get_num_from_str
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import (
    check_user, send_msg_handler,
    CommandObjectID, check_user_type
)
from ..xiuxian_utils.xiuxian2_handle import (
    sql_message, get_player_info, save_player_info,
    UserBuffDate, xiuxian_impart
)

cache_help = {}

alchemy_furnace_state = on_command("丹炉状态", priority=5, permission=GROUP, block=True)
alchemy_furnace_fire_control = on_command("丹炉升温", aliases={"丹炉降温"}, priority=5, permission=GROUP, block=True)
make_elixir = on_command("凝结丹药", aliases={"成丹"}, priority=5, permission=GROUP, block=True)
alchemy_furnace_add_herb = on_command("添加药材", priority=5, permission=GROUP, block=True)
mix_stop = on_command("停止炼丹", priority=5, permission=GROUP, block=True)
mix_elixir = on_fullmatch("丹方", priority=17, permission=GROUP, block=True)
mix_make = on_command("使用丹方", priority=5, permission=GROUP, block=True)
elixir_help = on_command("炼丹", priority=7, permission=GROUP, block=True)
mix_elixir_help = on_fullmatch("炼丹配方帮助", priority=7, permission=GROUP, block=True)
elixir_back = on_command("丹药背包", priority=10, permission=GROUP, block=True)
yaocai_back = on_command("药材背包", priority=10, permission=GROUP, block=True)
yaocai_get = on_command("灵田收取", aliases={"灵田结算"}, priority=8, permission=GROUP, block=True)
my_mix_elixir_info = on_fullmatch("我的炼丹信息", priority=6, permission=GROUP, block=True)
mix_elixir_sqdj_up = on_fullmatch("升级收取等级", priority=6, permission=GROUP, block=True)
mix_elixir_dykh_up = on_fullmatch("升级丹药控火", priority=6, permission=GROUP, block=True)
yaocai_get_op = on_command("op灵田收取", aliases={"op灵田结算"}, priority=8, permission=SUPERUSER, block=True)

__elixir_help__ = f"""
炼丹帮助信息:
可用指令：
1、丹炉状态
2、使用+丹炉 -》开始炼丹
3、添加药材 主药 xxxx 药引 xxxx 辅药 xxxx
（xxxx格式：某某药材n个 另外一个药材m个 -》 数量不限（小心炸炉））
4、丹炉（升|降）温 温度
5、凝结丹药|成丹
6、停止炼丹
"""

__mix_elixir_help__ = f"""
炼丹配方信息
1、炼丹需要主药、药引、辅药
3、草药的类型控制产出丹药的类型
"""


@make_elixir.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def make_elixir_(bot: Bot, event: GroupMessageEvent):
    """凝结丹药"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    is_type, _ = await check_user_type(user_id, 7)
    if not is_type:
        msg = "道友现在没在炼丹呢！！"
        await bot.send(event=event, message=msg)
        await make_elixir.finish()

    # 获取用户炼丹数据
    user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
    user_alchemy_furnace: AlchemyFurnace = await get_user_alchemy_furnace(user_id)
    msg, mix_elixir_info = user_alchemy_furnace.make_elixir()
    if not mix_elixir_info:
        await bot.send(event=event, message=msg)
        await make_elixir.finish()
    # 加入传承
    impart_data = await xiuxian_impart.get_user_info_with_id(user_id)
    impart_mix_per = impart_data['impart_mix_per'] if impart_data is not None else 0
    # 功法炼丹数加成
    main_dan_data = await UserBuffDate(user_id).get_user_main_buff_data()
    # 功法炼丹数量加成
    main_dan = main_dan_data['dan_buff'] if main_dan_data else 0
    # 炼丹数量提升
    num = 1 + user_alchemy_furnace.make_elixir_improve + impart_mix_per + main_dan
    await sql_message.send_back(user_id=user_id,
                                goods_id=mix_elixir_info['item_id'],
                                goods_name=mix_elixir_info['name'],
                                goods_type=mix_elixir_info['item_type'],
                                goods_num=num)
    msg += f"{num}颗"
    user_skill_improve_data = {
        'user_fire_control': mix_elixir_info['give_fire_control_exp']
                             + user_mix_elixir_info['user_fire_control'],
        'user_herb_knowledge': mix_elixir_info['give_herb_knowledge_exp']
                               + user_mix_elixir_info['user_herb_knowledge']}
    await database.update(table='mix_elixir_info',
                          where={'user_id': user_id},
                          **user_skill_improve_data)
    msg += (f"\r控火经验增加：{mix_elixir_info['give_fire_control_exp']}"
            f"（当前{mix_elixir_info['give_fire_control_exp'] + user_mix_elixir_info['user_fire_control']}）"
            f"\r药理知识增加：{mix_elixir_info['give_herb_knowledge_exp']}"
            f"（当前{mix_elixir_info['give_herb_knowledge_exp'] + user_mix_elixir_info['user_herb_knowledge']}）")

    # 保存丹炉数据
    await user_alchemy_furnace.save_data(user_id)
    await bot.send(event=event, message=msg)
    await make_elixir.finish()


@alchemy_furnace_fire_control.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def alchemy_furnace_fire_control_(
        bot: Bot, event: GroupMessageEvent, args: Message = CommandArg(), cmd: str = RawCommand()):
    """丹炉控制温度"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']

    # 检查是否在炼丹中
    is_type, _ = await check_user_type(user_id, 7)
    if not is_type:
        msg = "道友现在没在炼丹呢！！"
        await bot.send(event=event, message=msg)
        await alchemy_furnace_fire_control.finish()

    # 获取目标温度
    goal_fire_change = get_args_num(args, 1)
    if goal_fire_change < 10:
        msg = "目标温度变化至少为10！！"
        await bot.send(event=event, message=msg)
        await alchemy_furnace_fire_control.finish()

    # 获取用户炼丹数据
    user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
    user_alchemy_furnace: AlchemyFurnace = await get_user_alchemy_furnace(user_id)
    is_warm_up = False if cmd == "丹炉降温" else True
    msg = user_alchemy_furnace.change_temp(
        user_mix_elixir_info['user_fire_control'],
        goal_fire_change,
        is_warm_up=is_warm_up)

    # 保存丹炉数据
    await user_alchemy_furnace.save_data(user_id)
    await bot.send(event=event, message=msg)
    await alchemy_furnace_fire_control.finish()


@alchemy_furnace_state.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def alchemy_furnace_state_(bot: Bot, event: GroupMessageEvent):
    """丹炉状态"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    is_type, _ = await check_user_type(user_id, 7)
    if not is_type:
        msg = "道友现在没在炼丹呢！！"
        await bot.send(event=event, message=msg)
        await alchemy_furnace_state.finish()
    user_alchemy_furnace: AlchemyFurnace = await get_user_alchemy_furnace(user_id)
    msg = user_alchemy_furnace.get_state_msg()
    await bot.send(event=event, message=msg)
    await alchemy_furnace_state.finish()


@mix_stop.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def mix_stop_(bot: Bot, event: GroupMessageEvent):
    """结束炼丹"""
    user_type = 0  # 状态为空闲

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    is_type, msg = await check_user_type(user_id, 7)
    if is_type:
        await sql_message.in_closing(user_id, user_type)  # 退出修炼状态
        msg = "道友收起丹炉，停止了炼丹。"
        move_mix_user(user_id)
    else:
        msg = "道友现在没在炼丹呢！！"
    await bot.send(event=event, message=msg)
    await mix_stop.finish()


@alchemy_furnace_add_herb.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def alchemy_furnace_add_herb_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """丹炉加药"""

    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']
    is_type, _ = await check_user_type(user_id, 7)
    if not is_type:
        msg = "道友现在没在炼丹呢！！"
        await bot.send(event=event, message=msg)
        await alchemy_furnace_add_herb.finish()
    args = args.extract_plain_text()
    # 解析配方参数
    pattern = r"主药([\s\S]+)药引([\s\S]+)辅药([\s\S]+)"
    matched = re.search(pattern, args)
    matched = matched.groups()
    print(matched)
    msg = "获取到" + "|".join(matched)
    await bot.send(event=event, message=msg)
    msg_info = get_strs_from_str(args)
    num_info = get_num_from_str(args)
    item_name = msg_info[0] if msg_info else ''  # 获取第一个名称
    num = int(num_info[0]) if num_info else 1  # 获取第一个数量
    herb_use_as = item_name[:2]
    if herb_use_as in ['主药', '药引', '辅药']:
        herb_id = items.items_map.get(item_name[2:])
    else:
        msg = '输入格式有误，暂时只能输入 添加药材用作什么xx药n个，例如添加药材主药恒心草1'
        await bot.send(event=event, message=msg)
        await alchemy_furnace_add_herb.finish()
    if not herb_id:
        msg = '未知的药材名'
        await bot.send(event=event, message=msg)
        await alchemy_furnace_add_herb.finish()
    temp_dict = {herb_use_as: [(herb_id, num)]}

    # 获取用户炼丹数据
    user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
    user_alchemy_furnace: AlchemyFurnace = await get_user_alchemy_furnace(user_id)
    msg = user_alchemy_furnace.input_herbs(
        user_mix_elixir_info['user_fire_control'],
        user_mix_elixir_info['user_herb_knowledge'],
        temp_dict)

    # 保存丹炉数据
    await user_alchemy_furnace.save_data(user_id)
    await bot.send(event=event, message=msg)
    await alchemy_furnace_add_herb.finish()


@yaocai_get_op.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def yaocai_get_op_(bot: Bot, event: GroupMessageEvent):
    """灵田收取"""

    _, user_info, _ = await check_user(event)
    start_time = time.time()

    user_id = user_info['user_id']
    yaocai_id_list = items.get_random_id_list_by_rank_and_item_type(convert_rank(user_info['level'])[0],
                                                                    ['药材'])
    num = 100
    msg = '道友成功收获药材：\r'
    if not yaocai_id_list:
        await sql_message.send_back(user_id, 3001, '恒心草', '药材', num)  # 没有合适的，保底
        msg += f"恒心草 {num} 个！\r"
    else:
        give_dict = {}
        while num := num - 1:
            item_id = int(random.choice(yaocai_id_list))
            try:
                give_dict[item_id] += 1
            except LookupError:
                give_dict[item_id] = 1
        for k, v in give_dict.items():
            goods_info = items.get_data_by_item_id(k)
            msg += f"{goods_info['name']} {v} 个！\r"
        await sql_message.send_item(user_id, give_dict)
    end_time = time.time()
    use_time = (end_time - start_time) * 1000
    msg += f'耗时：{use_time}'
    await bot.send(event=event, message=msg)
    await yaocai_get_op.finish()


@mix_elixir_sqdj_up.handle(parameterless=[Cooldown(at_sender=False)])
async def mix_elixir_sqdj_up_(bot: Bot, event: GroupMessageEvent):
    """收取等级升级"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    if int(user_info['blessed_spot_flag']) == 0:
        msg = f"道友还没有洞天福地呢，请发送洞天福地购买吧~"
        await bot.send(event=event, message=msg)
        await mix_elixir_sqdj_up.finish()
    SQDJCONFIG = MIXELIXIRCONFIG['收取等级']
    mix_elixir_info = get_player_info(user_id, "mix_elixir_info")
    now_level = mix_elixir_info['收取等级']
    if now_level >= len(SQDJCONFIG):
        msg = f"道友的收取等级已达到最高等级，无法升级了"
        await bot.send(event=event, message=msg)
        await mix_elixir_sqdj_up.finish()
    next_level_cost = SQDJCONFIG[str(now_level + 1)]['level_up_cost']
    if mix_elixir_info['炼丹经验'] < next_level_cost:
        msg = f"下一个收取等级所需要的炼丹经验为{next_level_cost}点，道友请炼制更多的丹药再来升级吧~"
        await bot.send(event=event, message=msg)
        await mix_elixir_sqdj_up.finish()
    mix_elixir_info['炼丹经验'] = mix_elixir_info['炼丹经验'] - next_level_cost
    mix_elixir_info['收取等级'] = now_level + 1
    save_player_info(user_id, mix_elixir_info, 'mix_elixir_info')
    msg = f"道友的收取等级目前为：{mix_elixir_info['收取等级']}级，可以使灵田收获的药材增加{mix_elixir_info['收取等级']}个！"
    await bot.send(event=event, message=msg)
    await mix_elixir_sqdj_up.finish()


@mix_elixir_dykh_up.handle(parameterless=[Cooldown(at_sender=False)])
async def mix_elixir_dykh_up_(bot: Bot, event: GroupMessageEvent):
    """丹药控火升级"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    DYKHCONFIG = MIXELIXIRCONFIG['丹药控火']
    mix_elixir_info = get_player_info(user_id, "mix_elixir_info")
    now_level = mix_elixir_info['丹药控火']
    if now_level >= len(DYKHCONFIG):
        msg = f"道友的丹药控火等级已达到最高等级，无法升级了"
        await bot.send(event=event, message=msg)
        await mix_elixir_dykh_up.finish()
    next_level_cost = DYKHCONFIG[str(now_level + 1)]['level_up_cost']
    if mix_elixir_info['炼丹经验'] < next_level_cost:
        msg = f"下一个丹药控火等级所需要的炼丹经验为{next_level_cost}点，道友请炼制更多的丹药再来升级吧~"
        await bot.send(event=event, message=msg)
        await mix_elixir_dykh_up.finish()
    mix_elixir_info['炼丹经验'] = mix_elixir_info['炼丹经验'] - next_level_cost
    mix_elixir_info['丹药控火'] = now_level + 1
    save_player_info(user_id, mix_elixir_info, 'mix_elixir_info')
    msg = f"道友的丹药控火等级目前为：{mix_elixir_info['丹药控火']}级，可以使炼丹收获的丹药增加{mix_elixir_info['丹药控火']}个！"
    await bot.send(event=event, message=msg)
    await mix_elixir_dykh_up.finish()


@yaocai_get.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def yaocai_get_(bot: Bot, event: GroupMessageEvent):
    """灵田收取"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    if int(user_info['blessed_spot_flag']) == 0:
        msg = f"道友还没有洞天福地呢，请发送洞天福地购买吧~"
        await bot.send(event=event, message=msg)
        await yaocai_get.finish()
    mix_elixir_info = get_player_info(user_id, "mix_elixir_info")
    GETCONFIG = {
        "time_cost": 47,  # 单位小时
        "加速基数": 0.10
    }
    last_time = mix_elixir_info['收取时间']
    if last_time != 0:
        nowtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # str
        timedeff = round((datetime.strptime(nowtime, '%Y-%m-%d %H:%M:%S') - datetime.strptime(last_time,
                                                                                              '%Y-%m-%d %H:%M:%S')).total_seconds() / 3600,
                         2)
        user_buff_data = await UserBuffDate(user_id).buff_info
        if timedeff >= round(GETCONFIG['time_cost'] * (1 - (GETCONFIG['加速基数'] * mix_elixir_info['药材速度'])), 2):
            yaocai_id_list = items.get_random_id_list_by_rank_and_item_type(convert_rank(user_info['level'])[0],
                                                                            ['药材'])
            # 加入传承
            impart_data = await xiuxian_impart.get_user_info_with_id(user_id)
            impart_reap_per = impart_data['impart_reap_per'] if impart_data is not None else 0
            # 功法灵田收取加成
            main_reap = await UserBuffDate(user_id).get_user_main_buff_data()

            if main_reap is not None:  # 功法灵田收取加成
                reap_buff = main_reap['reap_buff']
            else:
                reap_buff = 0
            num = mix_elixir_info['灵田数量'] + mix_elixir_info['收取等级'] + impart_reap_per + reap_buff
            msg = '道友成功收获药材：\r'
            if not yaocai_id_list:
                await sql_message.send_back(user_info['user_id'], 3001, '恒心草', '药材', num)  # 没有合适的，保底
                msg += f"恒心草 {num} 个！\r"
            else:
                i = 1
                give_dict = {}
                while i <= num:
                    id = int(random.choice(yaocai_id_list))
                    try:
                        give_dict[id] += 1
                        i += 1
                    except LookupError:
                        give_dict[id] = 1
                        i += 1
                for k, v in give_dict.items():
                    goods_info = items.get_data_by_item_id(k)
                    msg += f"{goods_info['name']} {v} 个！\r"
                await sql_message.send_item(user_id, give_dict)
            mix_elixir_info['收取时间'] = nowtime
            save_player_info(user_id, mix_elixir_info, "mix_elixir_info")
            await bot.send(event=event, message=msg)
            await yaocai_get.finish()
        else:
            user_buff_data = await UserBuffDate(user_id).buff_info
            next_get_time = round(GETCONFIG['time_cost'] * (1 - (GETCONFIG['加速基数'] * mix_elixir_info['药材速度'])),
                                  2) - timedeff
            msg = f"道友的灵田还不能收取，下次收取时间为：{round(next_get_time, 2)}小时之后"
            await bot.send(event=event, message=msg)
            await yaocai_get.finish()


@my_mix_elixir_info.handle(parameterless=[Cooldown(at_sender=False)])
async def my_mix_elixir_info_(bot: Bot, event: GroupMessageEvent):
    """我的炼丹信息"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    mix_elixir_info = get_player_info(user_id, 'mix_elixir_info')

    # 获取用户炼丹数据
    user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
    l_msg = [f"☆----道友的炼丹信息----☆"]
    msg = f"药材收取等级：{mix_elixir_info['收取等级']}\r"
    msg += f"丹药控火经验：{user_mix_elixir_info['user_fire_control']}\r"
    msg += f"药理知识：{user_mix_elixir_info['user_herb_knowledge']}\r"
    msg += f"炼丹经验：{mix_elixir_info['炼丹经验']}\r"
    l_msg.append(msg)
    if mix_elixir_info['炼丹记录']:
        l_msg.append(f"☆------道友的炼丹记录------☆")
        i = 1
        for k, v in mix_elixir_info['炼丹记录'].items():
            msg = f"编号：{i},{v['name']}，炼成次数：{v['num']}次"
            l_msg.append(msg)
            i += 1
    await send_msg_handler(bot, event, '炼丹信息', bot.self_id, l_msg)
    await my_mix_elixir_info.finish()


@elixir_help.handle(parameterless=[Cooldown(at_sender=False)])
async def elixir_help_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    """炼丹帮助"""
    # 这里曾经是风控模块，但是已经不再需要了
    msg = __elixir_help__
    await bot.send(event=event, message=msg)
    await elixir_help.finish()


@mix_elixir_help.handle(parameterless=[Cooldown(at_sender=False)])
async def mix_elixir_help_(bot: Bot, event: GroupMessageEvent):
    """炼丹配方帮助"""
    # 这里曾经是风控模块，但是已经不再需要了
    msg = __mix_elixir_help__
    await bot.send(event=event, message=msg)
    await mix_elixir_help.finish()


user_ldl_dict = {}
user_ldl_flag = {}


@elixir_back.handle(parameterless=[Cooldown(at_sender=False)])
async def elixir_back_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """丹药背包
    ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
    "remake", "day_num", "all_num", "action_time", "state"]
    """

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    msg = await get_user_elixir_back_msg(user_id)

    args = args.extract_plain_text().strip()
    page = re.findall(r"\d+", args)  # 背包页数

    page_all = (len(msg) // 12) + 1 if len(msg) % 12 != 0 else len(msg) // 12  # 背包总页数

    if page:
        pass
    else:
        page = ["1"]
    page = int(page[0])
    if page_all < page != 1:
        msg = "道友的丹药背包没有那么广阔！！！"
        await bot.send(event=event, message=msg)
        await elixir_back.finish()
    if len(msg) != 0:
        # 获取页数物品数量
        item_num = page * 12 - 12
        item_num_end = item_num + 12
        msg = [f"\r{user_info['user_name']}的背包"] + msg[item_num:item_num_end]
        msg += [f"\r第 {page}/{page_all} 页\r☆————tips————☆\r可以发送丹药背包+页数来查看更多页数的物品哦"]
    else:
        msg = ["道友的丹药背包空空如也！"]
    try:
        await send_msg_handler(bot, event, '丹药背包', bot.self_id, msg)
    except ActionFailed:
        await elixir_back.finish("查看丹药背包失败!", reply_message=True)

    await elixir_back.finish()


@yaocai_back.handle(parameterless=[Cooldown(at_sender=False)])
async def yaocai_back_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg(), cmd: str = RawCommand()):
    """药材背包
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
        msg = await get_user_yaocai_back_msg(user_id)
        page_all = 12
    else:
        msg = await get_user_yaocai_back_msg_easy(user_id)
        page_all = 30

    if msg:
        msg_head = f"\r{user_info['user_name']}的药材背包"
        msg = get_paged_msg(msg_list=msg, page=page, cmd=cmd, per_page_item=page_all, msg_head=msg_head)
    else:
        msg = ["道友的药材背包空空如也！"]
    await send_msg_handler(bot, event, '背包', bot.self_id, msg)
    await yaocai_back.finish()


async def check_yaocai_name_in_back(user_id, yaocai_name, yaocai_num):
    flag = False
    goods_id = 0
    user_back = await sql_message.get_back_msg(user_id)
    for back in user_back:
        if back['goods_type'] == '药材':
            if items.get_data_by_item_id(back['goods_id'])['name'] == yaocai_name:
                if int(back['goods_num']) >= int(yaocai_num):
                    flag = True
                    goods_id = back['goods_id']
                    break
            else:
                continue
        else:
            continue
    return flag, goods_id


async def check_ldl_name_in_back(user_id, ldl_name):
    flag = False
    goods_info = {}
    user_back = await sql_message.get_back_msg(user_id)
    for back in user_back:
        if back['goods_type'] == '炼丹炉':
            if back['goods_name'] == ldl_name:
                flag = True
                goods_info = items.get_data_by_item_id(back['goods_id'])
                break
            else:
                continue
        else:
            continue
    return flag, goods_info
