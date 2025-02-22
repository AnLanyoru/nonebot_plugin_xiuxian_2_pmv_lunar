import random
import re
import time
from datetime import datetime

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent,
    Message
)
from nonebot.params import CommandArg, RawCommand
from nonebot.permission import SUPERUSER

from .mix_elixir_config import MIXELIXIRCONFIG
from .mix_elixir_database import create_user_mix_elixir_info, get_user_mix_elixir_info
from .mixelixirutil import AlchemyFurnace, get_user_alchemy_furnace, remove_mix_user
from ..xiuxian_back.back_util import get_user_yaocai_back_msg, get_user_yaocai_back_msg_easy, \
    get_user_back_msg
from ..xiuxian_config import convert_rank
from ..xiuxian_database.database_connect import database
from ..xiuxian_utils.clean_utils import get_strs_from_str, get_args_num, get_paged_msg, get_num_from_str, main_md, \
    three_md, simple_md, zips
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import (
    check_user, send_msg_handler, check_user_type
)
from ..xiuxian_utils.xiuxian2_handle import (
    sql_message, UserBuffDate, xiuxian_impart
)

cache_help = {}
# 初始化药材列表
herb_id_map = {herb_name: herb_id for herb_name, herb_id in items.items_map.items()
               if items.get_data_by_item_id(herb_id).get('type') == '药材'}


async def get_yuan_xiao_top():
    """挑战排行"""
    sql = (f"SELECT "
           f"(SELECT max(user_name) FROM user_xiuxian WHERE user_xiuxian.user_id = mix_elixir_info.user_id) "
           f"as user_name, "
           f"sum_mix_num "
           f"FROM mix_elixir_info "
           f"ORDER BY sum_mix_num DESC "
           f"limit 100")
    async with database.pool.acquire() as db:
        result = await db.fetch(sql)
        result_all = [zips(**result_per) for result_per in result]
        return result_all


alchemy_furnace_state = on_command("丹炉状态", priority=5, permission=GROUP, block=True)
alchemy_furnace_fire_control = on_command("丹炉升温", aliases={"丹炉降温"}, priority=5, permission=GROUP, block=True)
make_elixir = on_command("凝结丹药", aliases={"成丹", "开"}, priority=10, permission=GROUP, block=True)
alchemy_furnace_add_herb = on_command("添加药材", priority=5, permission=GROUP, block=True)
mix_stop = on_command("停止炼丹", aliases={'退出炼丹'}, priority=5, permission=GROUP, block=True)
mix_elixir = on_command("丹方", priority=17, permission=GROUP, block=True)
mix_make = on_command("使用丹方", priority=5, permission=GROUP, block=True)
elixir_help = on_command("炼丹", priority=7, permission=GROUP, block=True)
mix_elixir_help = on_command("炼丹帮助", priority=6, permission=GROUP, block=True)
elixir_back = on_command("丹药背包", priority=10, permission=GROUP, block=True)
yaocai_back = on_command("药材背包", priority=10, permission=GROUP, block=True)
yaocai_get = on_command("灵田收取", aliases={"灵田结算"}, priority=8, permission=GROUP, block=True)
my_mix_elixir_info = on_command("我的炼丹信息", aliases={"炼丹信息"}, priority=6, permission=GROUP, block=True)
mix_elixir_fire_improve = on_command("丹火升级", aliases={"升级丹火"}, priority=6, permission=GROUP, block=True)
mix_elixir_fire_improve_num = on_command("丹火升级塑形", priority=5, permission=GROUP, block=True)
mix_elixir_fire_improve_power = on_command("丹火升级萃取", priority=5, permission=GROUP, block=True)
yaocai_get_op = on_command("op灵田收取", aliases={"op灵田结算"}, priority=8, permission=SUPERUSER, block=True)
elixir_top = on_command("炼丹排行榜", priority=8, permission=GROUP, block=True)
alchemy_furnace_get = on_command("购买丹炉", priority=8, permission=GROUP, block=True)
mix_elixir_fire_remake = on_command("重塑丹火", priority=5, permission=GROUP, block=True)

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
7、购买丹炉
8、丹火升级
9、重塑丹火
10、炼丹帮助
"""

__mix_elixir_help__ = f"""
炼丹教程
1、炼丹需要主药、药引、辅药
3、草药的类型控制产出丹药的类型
3、使用 炼丹炉 来开始炼丹
4、通过丹炉升温/丹炉降温来控制丹炉温度稳定在500上下
5、丹炉温度稳定后，开始加入药材
6、可以利用低级药材探索成丹规律并且练习控制丹炉火焰来为炼制高级药材做准备
7、发送 炼丹 来查看所有炼丹具体指令
"""

level_up_need_exp = {0: 1000,
                     1: 5000,
                     2: 10000,
                     3: 50000,
                     4: 100000}.copy()

fire_name_by_level = {0: '普通火焰',
                      1: '蕴丹玄火',
                      2: '蕴丹灵火',
                      3: '混元灵火',
                      4: '万象灵火'}.copy()


@alchemy_furnace_get.handle(parameterless=[Cooldown(stamina_cost=0)])
async def alchemy_furnace_get_(bot: Bot, event: GroupMessageEvent):
    """结束炼丹"""
    user_type = 0  # 状态为空闲

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    user_stone = user_info['stone']
    if user_stone < 5000000:
        msg = '道友的灵石不足呢，购置丹炉需要花费500w灵石！'
        await bot.send(event=event, message=msg)
        await alchemy_furnace_get.finish()
    alchemy_furnace_in_back = await sql_message.get_item_by_good_id_and_user_id(user_id=user_id,
                                                                                goods_id=4003)
    if alchemy_furnace_in_back:
        msg = '道友已经购置过丹炉了呢！'
        await bot.send(event=event, message=msg)
        await alchemy_furnace_get.finish()

    msg = "陨铁炉*1 购买成功，道友还请好好爱惜！"
    await sql_message.update_ls(user_id, 5000000, 2)
    await sql_message.send_item(user_id, {4003: 1}, 1)
    await bot.send(event=event, message=msg)
    await alchemy_furnace_get.finish()


@elixir_top.handle(parameterless=[Cooldown()])
async def elixir_top_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """炼丹排行榜"""
    page = get_args_num(args, 1, default=1)
    lt_rank = await get_yuan_xiao_top()
    long_rank = len(lt_rank)
    page_all = (long_rank // 20) + 1 if long_rank % 20 != 0 else long_rank // 20  # 总页数
    if page_all < page != 1:
        msg = f"炼丹排行榜没有那么广阔！！！"
        await bot.send(event=event, message=msg)
        await elixir_top.finish()
    if long_rank != 0:
        # 获取页数物品数量
        item_num = page * 20 - 20
        item_num_end = item_num + 20
        lt_rank = lt_rank[item_num:item_num_end]
        top_msg = f"✨炼丹排行TOP{item_num_end}✨"
        msg = ''
        num = item_num
        for i in lt_rank:
            i = list(i.values())
            num += 1
            msg += f"第{num}位 {i[0]} 总成丹数:{i[1]}颗\r"
        msg += f"第 {page}/{page_all} 页"
        msg = main_md(top_msg, msg,
                      '灵石排行榜', '灵石排行榜',
                      '修为排行榜', '排行榜',
                      '宗门排行榜', '宗门排行榜',
                      '下一页', f'炼丹排行榜 {page + 1}')
    else:
        msg = f"该排行榜空空如也！"
    await bot.send(event=event, message=msg)
    await elixir_top.finish()


@mix_elixir_fire_remake.handle(
    parameterless=[Cooldown(stamina_cost=0, parallel_block=True)])
async def mix_elixir_fire_remake_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """丹火重塑"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']

    # 获取用户炼丹数据
    user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
    user_fire_num = user_mix_elixir_info['user_fire_more_num']
    user_fire_power = user_mix_elixir_info['user_fire_more_power']
    if '确认' not in args.extract_plain_text():
        msg = simple_md(f"道友当前丹火升级状态为："
                        f"萃取lv.{user_fire_power}, 塑形lv.{user_fire_num}\r"
                        f"若确定清空当前丹火升级，请自行在指令后加上",
                        "确认", "确认",
                        f"。")
        await bot.send(event=event, message=msg)
        await mix_elixir_fire_remake.finish()

    user_skill_improve_data = {
        'user_fire_more_power': 0,
        'user_fire_more_num': 0}
    await database.update(table='mix_elixir_info',
                          where={'user_id': user_id},
                          **user_skill_improve_data)

    msg = simple_md(f"道友成功重塑丹火，丹火等级归0\r",
                    "升级丹火", "升级丹火",
                    f"。")
    await bot.send(event=event, message=msg)
    await mix_elixir_fire_remake.finish()


@mix_elixir_fire_improve_num.handle(
    parameterless=[Cooldown(stamina_cost=0, parallel_block=True)])
async def mix_elixir_fire_improve_num_(bot: Bot, event: GroupMessageEvent):
    """丹火升级塑形"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    user_name = user_info['user_name']

    # 获取用户炼丹数据
    user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
    user_elixir_exp = user_mix_elixir_info['user_mix_elixir_exp']
    user_fire_num = user_mix_elixir_info['user_fire_more_num']
    user_fire_power = user_mix_elixir_info['user_fire_more_power']
    sum_level = user_fire_num + user_fire_power

    if sum_level == 4:
        msg = f"道友的丹火已暂时提升到顶了！"
        await bot.send(event=event, message=msg)
        await mix_elixir_fire_improve_power.finish()

    if (need_exp := level_up_need_exp.get(sum_level)) > user_elixir_exp:
        msg = f"道友当前炼丹经验不足以提升丹火，当前：{user_elixir_exp} 所需：{need_exp}"
        await bot.send(event=event, message=msg)
        await mix_elixir_fire_improve_num.finish()

    user_skill_improve_data = {
        'user_fire_more_num': 1 + user_mix_elixir_info['user_fire_more_num'],
        'user_mix_elixir_exp': user_mix_elixir_info['user_mix_elixir_exp']
                               - need_exp}
    await database.update(table='mix_elixir_info',
                          where={'user_id': user_id},
                          **user_skill_improve_data)

    msg = simple_md(f"丹火升级方向：塑形，升级成功\r{user_name}道友本次升级丹火消耗{need_exp}",
                    "炼丹经验", "我的炼丹信息",
                    f"\r丹药凝结数量提升 1"
                    f"\r当前等级：{user_skill_improve_data['user_fire_more_num']}"
                    f"\r余剩炼丹经验：{user_skill_improve_data['user_mix_elixir_exp']}")
    await bot.send(event=event, message=msg)
    await mix_elixir_fire_improve_num.finish()


@mix_elixir_fire_improve_power.handle(
    parameterless=[Cooldown(stamina_cost=0, parallel_block=True)])
async def mix_elixir_fire_improve_power_(bot: Bot, event: GroupMessageEvent):
    """丹火升级萃取"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    user_name = user_info['user_name']

    # 获取用户炼丹数据
    user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
    user_elixir_exp = user_mix_elixir_info['user_mix_elixir_exp']
    user_fire_num = user_mix_elixir_info['user_fire_more_num']
    user_fire_power = user_mix_elixir_info['user_fire_more_power']
    sum_level = user_fire_num + user_fire_power

    if sum_level == 4:
        msg = f"道友的丹火已暂时提升到顶了！"
        await bot.send(event=event, message=msg)
        await mix_elixir_fire_improve_power.finish()

    if (need_exp := level_up_need_exp.get(sum_level)) > user_elixir_exp:
        msg = f"道友当前炼丹经验不足以提升丹火，当前：{user_elixir_exp} 所需：{need_exp}"
        await bot.send(event=event, message=msg)
        await mix_elixir_fire_improve_power.finish()

    user_skill_improve_data = {
        'user_fire_more_power': 1 + user_mix_elixir_info['user_fire_more_power'],
        'user_mix_elixir_exp': user_mix_elixir_info['user_mix_elixir_exp']
                               - need_exp}
    await database.update(table='mix_elixir_info',
                          where={'user_id': user_id},
                          **user_skill_improve_data)

    msg = simple_md(f"丹火升级方向：萃取，升级成功\r{user_name}道友本次升级丹火消耗{need_exp}",
                    "炼丹经验", "我的炼丹信息",
                    f"\r药材药力萃取提升 30%"
                    f"\r当前等级：{user_skill_improve_data['user_fire_more_power']}"
                    f"\r余剩炼丹经验：{user_skill_improve_data['user_mix_elixir_exp']}")
    await bot.send(event=event, message=msg)
    await mix_elixir_fire_improve_power.finish()


@mix_elixir_fire_improve.handle(parameterless=[Cooldown(stamina_cost=0)])
async def mix_elixir_fire_improve_(bot: Bot, event: GroupMessageEvent):
    """丹火升级"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    user_name = user_info['user_name']

    # 获取用户炼丹数据
    user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
    user_elixir_exp = user_mix_elixir_info['user_mix_elixir_exp']
    user_fire_num = user_mix_elixir_info['user_fire_more_num']
    user_fire_power = user_mix_elixir_info['user_fire_more_power']
    sum_level = user_fire_num + user_fire_power

    if sum_level == 4:
        msg = f"道友的丹火已暂时提升到顶了！"
        await bot.send(event=event, message=msg)
        await mix_elixir_fire_improve.finish()

    if (need_exp := level_up_need_exp.get(sum_level)) > user_elixir_exp:
        msg = f"道友当前炼丹经验不足以提升丹火，当前：{user_elixir_exp} 所需：{need_exp}"
        await bot.send(event=event, message=msg)
        await mix_elixir_fire_improve.finish()

    msg = three_md(f"{user_name}道友本次升级丹火将消耗{need_exp}", "炼丹经验", "我的炼丹信息",
                   "道友可以选择将丹火向两个方向提升：\r  1.", "塑形", "丹火升级塑形",
                   ": 提升丹药成型数量(每级1)\r  2.", "萃取", "丹火升级萃取",
                   ": 炼丹加入药材时药性萃取率提升(每级30%)")
    await bot.send(event=event, message=msg)
    await mix_elixir_fire_improve.finish()


@make_elixir.handle(parameterless=[Cooldown(stamina_cost=0)])
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
    # 丹火炼丹数量提升
    fire_num_up = user_mix_elixir_info['user_fire_more_num']

    # 总炼丹数量提升
    num = 1 + user_alchemy_furnace.make_elixir_improve + impart_mix_per + main_dan + fire_num_up
    await sql_message.send_back(user_id=user_id,
                                goods_id=mix_elixir_info['item_id'],
                                goods_name=mix_elixir_info['name'],
                                goods_type=mix_elixir_info['type'],
                                goods_num=num)
    msg += f"{num}颗"

    # 提升炼丹经验计算
    main_dan_exp = main_dan_data['dan_exp'] if main_dan_data else 0
    final_dan_exp = max(20, mix_elixir_info['rank'] - 50) + main_dan_exp * num

    user_skill_improve_data = {
        'user_fire_control': mix_elixir_info['give_fire_control_exp']
                             + user_mix_elixir_info['user_fire_control'],
        'user_herb_knowledge': mix_elixir_info['give_herb_knowledge_exp']
                               + user_mix_elixir_info['user_herb_knowledge'],
        'user_mix_elixir_exp': final_dan_exp
                               + user_mix_elixir_info['user_mix_elixir_exp'],
        'sum_mix_num': num
                       + user_mix_elixir_info['sum_mix_num']
    }
    await database.update(table='mix_elixir_info',
                          where={'user_id': user_id},
                          **user_skill_improve_data)
    msg += (f"\r控火经验增加：{mix_elixir_info['give_fire_control_exp']}"
            f"（当前{user_skill_improve_data['user_fire_control']}）"
            f"\r药理知识增加：{mix_elixir_info['give_herb_knowledge_exp']}"
            f"（当前{user_skill_improve_data['user_herb_knowledge']}）"
            f"\r炼丹经验增加：{final_dan_exp}"
            f"（当前{user_skill_improve_data['user_mix_elixir_exp']}）")

    # 保存丹炉数据
    await user_alchemy_furnace.save_data(user_id)
    await bot.send(event=event, message=msg)
    await make_elixir.finish()


@mix_make.handle(parameterless=[Cooldown(stamina_cost=0)])
async def mix_make_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """丹炉加药"""

    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']
    is_type, _ = await check_user_type(user_id, 7)
    if not is_type:
        msg = "道友现在没在炼丹呢！！"
        await bot.send(event=event, message=msg)
        await mix_make.finish()
    args = args.extract_plain_text()

    # 解析配方参数
    as_main = r'([\s\S]*)主药([\s\S][^主药引辅]*)'
    as_ing = r'([\s\S]*)药引([\s\S][^主药引辅]*)'
    as_sub = r'([\s\S]*)辅药([\s\S][^主药引辅]*)'

    matched_main = re.search(as_main, args)
    matched_ing = re.search(as_ing, args)
    matched_sub = re.search(as_sub, args)

    if not matched_main and not matched_ing and not matched_sub:
        msg = '输入格式有误，输入格式为 添加药材主药xxxx药引xxxx辅药xxxx'
        await bot.send(event=event, message=msg)
        await mix_make.finish()

    temp_dict = {}
    all_herb_as_type = ['主药', '药引', '辅药']
    for herb_as_type, matched_result in zip(all_herb_as_type, [matched_main, matched_ing, matched_sub]):
        if matched_result:
            herb_str = matched_result.group(2)
            herb_names = get_strs_from_str(herb_str)
            # 获取所有药材id
            main_herb_id = [herb_id_map.get(herb_name) for herb_name in herb_names]
            # 获取所有药材数量
            add_herb_num = [int(num) for num in get_num_from_str(herb_str)]
            if None in main_herb_id:
                msg = f'{herb_as_type}中含有未知的药材'
                await bot.send(event=event, message=msg)
                await mix_make.finish()
            if len(add_herb_num) != len(main_herb_id):
                msg = f'{herb_as_type}中有药材未指定数量'
                await bot.send(event=event, message=msg)
                await mix_make.finish()
            # 格式化
            main_herb = list(zip(main_herb_id, add_herb_num, herb_names))
            temp_dict[herb_as_type] = main_herb

    # 检查用户药材数量是否充足
    loss_msg = ''
    user_back = await sql_message.get_back_msg(user_id)
    user_back_dict = {item_info['goods_id']: item_info for item_info in user_back}
    decrease_dict = {}
    for herb_as_type in temp_dict.keys():
        herbs_input = temp_dict[herb_as_type]
        for herb_id, herb_num, herb_name in herbs_input:
            if herb_id in decrease_dict:
                decrease_dict[herb_id] += herb_num
            else:
                decrease_dict[herb_id] = herb_num
            if (real_num := user_back_dict.get(herb_id, {}).get('goods_num', 0)) < herb_num:
                loss_msg += f"\r道友欲添加的{herb_as_type}:{herb_name}不足(需要{herb_num},余下{real_num}个)"
            if herb_id in user_back_dict:
                user_back_dict[herb_id]['goods_num'] -= herb_num

    if loss_msg:
        await bot.send(event=event, message=loss_msg)
        await mix_make.finish()

    # 扣除药材
    await sql_message.decrease_user_item(user_id, decrease_dict, True)
    # 获取用户炼丹数据
    user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
    user_alchemy_furnace: AlchemyFurnace = await get_user_alchemy_furnace(user_id)
    msg_herb = user_alchemy_furnace.input_herbs(
        user_mix_elixir_info['user_fire_control'],
        user_mix_elixir_info['user_herb_knowledge'],
        user_mix_elixir_info['user_fire_more_power'],
        temp_dict)

    msg_make, mix_elixir_info = user_alchemy_furnace.make_elixir()
    msg = msg_herb + '\r' + msg_make
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
    # 丹火炼丹数量提升
    fire_num_up = user_mix_elixir_info['user_fire_more_num']

    # 总炼丹数量提升
    num = 1 + user_alchemy_furnace.make_elixir_improve + impart_mix_per + main_dan + fire_num_up
    await sql_message.send_back(user_id=user_id,
                                goods_id=mix_elixir_info['item_id'],
                                goods_name=mix_elixir_info['name'],
                                goods_type=mix_elixir_info['type'],
                                goods_num=num)
    msg += f"{num}颗"

    # 提升炼丹经验计算
    main_dan_exp = main_dan_data['dan_exp'] if main_dan_data else 0
    final_dan_exp = max(20, mix_elixir_info['rank'] - 50) + main_dan_exp * num

    user_skill_improve_data = {
        'user_fire_control': mix_elixir_info['give_fire_control_exp']
                             + user_mix_elixir_info['user_fire_control'],
        'user_herb_knowledge': mix_elixir_info['give_herb_knowledge_exp']
                               + user_mix_elixir_info['user_herb_knowledge'],
        'user_mix_elixir_exp': final_dan_exp
                               + user_mix_elixir_info['user_mix_elixir_exp'],
        'sum_mix_num': num
                       + user_mix_elixir_info['sum_mix_num']
    }
    await database.update(table='mix_elixir_info',
                          where={'user_id': user_id},
                          **user_skill_improve_data)
    msg += (f"\r控火经验增加：{mix_elixir_info['give_fire_control_exp']}"
            f"（当前{user_skill_improve_data['user_fire_control']}）"
            f"\r药理知识增加：{mix_elixir_info['give_herb_knowledge_exp']}"
            f"（当前{user_skill_improve_data['user_herb_knowledge']}）"
            f"\r炼丹经验增加：{final_dan_exp}"
            f"（当前{user_skill_improve_data['user_mix_elixir_exp']}）\r")
    msg = simple_md(msg, '再次使用此丹方', event.get_message().extract_plain_text(), '。')
    # 保存丹炉数据
    await user_alchemy_furnace.save_data(user_id)
    await bot.send(event=event, message=msg)
    await mix_make.finish()


@alchemy_furnace_fire_control.handle(parameterless=[Cooldown(stamina_cost=0)])
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


@alchemy_furnace_state.handle(parameterless=[Cooldown(stamina_cost=0)])
async def alchemy_furnace_state_(bot: Bot, event: GroupMessageEvent):
    """丹炉状态"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    is_type, _ = await check_user_type(user_id, 7)
    if not is_type:
        msg = "道友现在没在炼丹呢！！"
        await bot.send(event=event, message=msg)
        await alchemy_furnace_state.finish()

    # 获取用户炼丹数据
    user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
    user_alchemy_furnace: AlchemyFurnace = await get_user_alchemy_furnace(user_id)
    fire_name = user_mix_elixir_info['user_fire_name']
    user_fire_num = user_mix_elixir_info['user_fire_more_num']
    user_fire_power = user_mix_elixir_info['user_fire_more_power']
    sum_level = user_fire_num + user_fire_power
    fire_name = fire_name if fire_name else fire_name_by_level.get(sum_level)
    msg = user_alchemy_furnace.get_state_msg(fire_name)
    await bot.send(event=event, message=msg)
    await alchemy_furnace_state.finish()


@mix_stop.handle(parameterless=[Cooldown(stamina_cost=0)])
async def mix_stop_(bot: Bot, event: GroupMessageEvent):
    """结束炼丹"""
    user_type = 0  # 状态为空闲

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    is_type, msg = await check_user_type(user_id, 7)
    if is_type:
        await sql_message.in_closing(user_id, user_type)  # 退出修炼状态
        msg = "道友收起丹炉，停止了炼丹。"
        remove_mix_user(user_id)
    else:
        msg = "道友现在没在炼丹呢！！"
    await bot.send(event=event, message=msg)
    await mix_stop.finish()


@alchemy_furnace_add_herb.handle(parameterless=[Cooldown(stamina_cost=0)])
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
    as_main = r'([\s\S]*)主药([\s\S][^主药引辅]*)'
    as_ing = r'([\s\S]*)药引([\s\S][^主药引辅]*)'
    as_sub = r'([\s\S]*)辅药([\s\S][^主药引辅]*)'

    matched_main = re.search(as_main, args)
    matched_ing = re.search(as_ing, args)
    matched_sub = re.search(as_sub, args)

    if not matched_main and not matched_ing and not matched_sub:
        msg = '输入格式有误，输入格式为 添加药材主药xxxx药引xxxx辅药xxxx'
        await bot.send(event=event, message=msg)
        await alchemy_furnace_add_herb.finish()

    temp_dict = {}
    all_herb_as_type = ['主药', '药引', '辅药']
    for herb_as_type, matched_result in zip(all_herb_as_type, [matched_main, matched_ing, matched_sub]):
        if matched_result:
            herb_str = matched_result.group(2)
            herb_names = get_strs_from_str(herb_str)
            # 获取所有药材id
            main_herb_id = [herb_id_map.get(herb_name) for herb_name in herb_names]
            # 获取所有药材数量
            add_herb_num = [int(num) for num in get_num_from_str(herb_str)]
            if None in main_herb_id:
                msg = f'{herb_as_type}中含有未知的药材'
                await bot.send(event=event, message=msg)
                await alchemy_furnace_add_herb.finish()
            if len(add_herb_num) != len(main_herb_id):
                msg = f'{herb_as_type}中有药材未指定数量'
                await bot.send(event=event, message=msg)
                await alchemy_furnace_add_herb.finish()
            # 格式化
            main_herb = list(zip(main_herb_id, add_herb_num, herb_names))
            temp_dict[herb_as_type] = main_herb

    # 检查用户药材数量是否充足
    loss_msg = ''
    user_back = await sql_message.get_back_msg(user_id)
    user_back_dict = {item_info['goods_id']: item_info for item_info in user_back}
    decrease_dict = {}
    for herb_as_type in temp_dict.keys():
        herbs_input = temp_dict[herb_as_type]
        for herb_id, herb_num, herb_name in herbs_input:
            if herb_id in decrease_dict:
                decrease_dict[herb_id] += herb_num
            else:
                decrease_dict[herb_id] = herb_num
            if (real_num := user_back_dict.get(herb_id, {}).get('goods_num', 0)) < herb_num:
                loss_msg += f"\r道友欲添加的{herb_as_type}:{herb_name}不足(需要{herb_num},余下{real_num}个)"
            if herb_id in user_back_dict:
                user_back_dict[herb_id]['goods_num'] -= herb_num

    if loss_msg:
        await bot.send(event=event, message=loss_msg)
        await alchemy_furnace_add_herb.finish()

    # 扣除药材
    await sql_message.decrease_user_item(user_id, decrease_dict, True)
    print(temp_dict)

    # 获取用户炼丹数据
    user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
    user_alchemy_furnace: AlchemyFurnace = await get_user_alchemy_furnace(user_id)
    msg = user_alchemy_furnace.input_herbs(
        user_mix_elixir_info['user_fire_control'],
        user_mix_elixir_info['user_herb_knowledge'],
        user_mix_elixir_info['user_fire_more_power'],
        temp_dict)

    # 保存丹炉数据
    await user_alchemy_furnace.save_data(user_id)
    await bot.send(event=event, message=msg)
    await alchemy_furnace_add_herb.finish()


@yaocai_get_op.handle(parameterless=[Cooldown(stamina_cost=0)])
async def yaocai_get_op_(bot: Bot, event: GroupMessageEvent):
    """灵田收取"""

    _, user_info, _ = await check_user(event)
    start_time = time.time()

    user_id = user_info['user_id']
    yaocai_id_list = items.get_random_id_list_by_rank_and_item_type(convert_rank(user_info['level'])[0],
                                                                    ['药材'])
    num = 10000
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


@yaocai_get.handle(parameterless=[Cooldown(stamina_cost=0)])
async def yaocai_get_(bot: Bot, event: GroupMessageEvent):
    """灵田收取"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    if int(user_info['blessed_spot_flag']) == 0:
        msg = f"道友还没有洞天福地呢，请发送洞天福地购买吧~"
        await bot.send(event=event, message=msg)
        await yaocai_get.finish()
    mix_elixir_info = await get_user_mix_elixir_info(user_id)
    GETCONFIG = {
        "time_cost": 23,  # 单位小时
        "加速基数": 0.10
    }
    last_time = mix_elixir_info['farm_harvest_time']
    if last_time != 0:
        nowtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # str
        time_def = round(
            (datetime.strptime(nowtime, '%Y-%m-%d %H:%M:%S')
             - datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')).total_seconds() / 3600,
            2)
        if time_def >= round(
                GETCONFIG['time_cost'] * (1 - (GETCONFIG['加速基数'] * mix_elixir_info['farm_grow_speed'])), 2):
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
            num = mix_elixir_info['farm_num'] + impart_reap_per + reap_buff
            msg = '道友成功收获药材：\r'
            if not yaocai_id_list:
                await sql_message.send_back(user_info['user_id'], 3001, '恒心草', '药材', num)  # 没有合适的，保底
                msg += f"恒心草 {num} 个！\r"
            else:
                give_dict = {}
                for _ in range(num):
                    elixir_id = int(random.choice(yaocai_id_list))
                    try:
                        give_dict[elixir_id] += 1
                    except LookupError:
                        give_dict[elixir_id] = 1
                for k, v in give_dict.items():
                    goods_info = items.get_data_by_item_id(k)
                    msg += f"{goods_info['name']} {v} 个！\r"
                await sql_message.send_item(user_id, give_dict)
            update_mix_elixir_info = {'farm_harvest_time': nowtime}
            await database.update(
                table='mix_elixir_info',
                where={'user_id': user_id},
                **update_mix_elixir_info)
            await bot.send(event=event, message=msg)
            await yaocai_get.finish()
        else:
            next_get_time = round(GETCONFIG['time_cost']
                                  * (1 - (GETCONFIG['加速基数'] * mix_elixir_info['farm_grow_speed'])),
                                  2) - time_def
            msg = f"道友的灵田还不能收取，下次收取时间为：{round(next_get_time, 2)}小时之后"
            await bot.send(event=event, message=msg)
            await yaocai_get.finish()


@my_mix_elixir_info.handle(parameterless=[Cooldown()])
async def my_mix_elixir_info_(bot: Bot, event: GroupMessageEvent):
    """我的炼丹信息"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']

    # 获取用户炼丹数据
    user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
    user_fire_more_num = user_mix_elixir_info['user_fire_more_num']
    user_fire_more_power = user_mix_elixir_info['user_fire_more_power']
    sum_level = user_fire_more_num + user_fire_more_power
    fire_name = user_mix_elixir_info['user_fire_name']
    fire_name = fire_name if fire_name else fire_name_by_level.get(sum_level)
    msg = (f"☆----道友的炼丹信息----☆\r"
           f"丹火：{fire_name}\r"
           f"(塑形：lv.{user_fire_more_num}"
           f"|萃取：lv.{user_fire_more_power})\r"
           f"控火经验：{user_mix_elixir_info['user_fire_control']}\r"
           f"药理知识：{user_mix_elixir_info['user_herb_knowledge']}\r"
           f"炼丹经验：{user_mix_elixir_info['user_mix_elixir_exp']}\r")
    if user_mix_elixir_info['mix_elixir_data']:
        pass
    msg_md = main_md(msg, '暂无炼丹记录',
                     '升级丹火', '升级丹火',
                     '灵田结算', '灵田结算',
                     '洞天福地', '洞天福地查看',
                     '丹炉状态', '丹炉状态')
    await bot.send(event=event, message=msg_md)
    await my_mix_elixir_info.finish()


@elixir_help.handle(parameterless=[Cooldown()])
async def elixir_help_(bot: Bot, event: GroupMessageEvent):
    """炼丹帮助"""
    # 这里曾经是风控模块，但是已经不再需要了
    msg = __elixir_help__
    await bot.send(event=event, message=msg)
    await elixir_help.finish()


@mix_elixir_help.handle(parameterless=[Cooldown()])
async def mix_elixir_help_(bot: Bot, event: GroupMessageEvent):
    """炼丹配方帮助"""
    # 这里曾经是风控模块，但是已经不再需要了
    msg = __mix_elixir_help__
    await bot.send(event=event, message=msg)
    await mix_elixir_help.finish()


user_ldl_dict = {}
user_ldl_flag = {}


@elixir_back.handle(parameterless=[Cooldown()])
async def elixir_back_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """丹药背包
    ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
    "remake", "day_num", "all_num", "action_time", "state"]
    """

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    msg_list = await get_user_back_msg(user_id, ['炼丹炉', '丹药', '合成丹药'])

    args = args.extract_plain_text().strip()
    page = get_args_num(args, 1, default=1)  # 背包页数
    msg_list_per = get_paged_msg(msg_list=msg_list, page=page, per_page_item=20)
    await send_msg_handler(bot, event, '丹药背包', bot.self_id, msg_list_per)
    await elixir_back.finish()


@yaocai_back.handle(parameterless=[Cooldown()])
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
