import random

from nonebot import on_command, require
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent,
    MessageSegment, Message
)
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .old_rift_info import old_rift_info
from .riftconfig import get_rift_config
from .riftmake import (
    Rift, get_rift_type, get_story_type, NONEMSG, get_battle_type,
    get_dxsj_info, get_boss_battle_info, get_treasure_info
)
from .. import DRIVER
from ..xiuxian_limit import limit_handle
from ..xiuxian_place import place
from ..xiuxian_utils.clean_utils import get_strs_from_str, simple_md, main_md, msg_handler, get_num_from_str
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import (
    check_user, check_user_type,
    CommandObjectID
)
from ..xiuxian_utils.xiuxian2_handle import sql_message

config = get_rift_config()
cache_help = {}
world_rift = {}  # dict
# 定时任务
set_rift = require("nonebot_plugin_apscheduler").scheduler

rift_help = on_command("秘境帮助", priority=6, permission=GROUP, block=True)
create_rift = on_command("生成秘境", priority=5, permission=SUPERUSER, block=True)
create_rift_with_args = on_command("创造秘境", priority=5, permission=SUPERUSER, block=True)
complete_rift = on_command("探索秘境", aliases={"结算秘境"}, priority=7, permission=GROUP, block=True)
rift_protect_handle = on_command("秘境战斗事件保底", priority=5, permission=GROUP, block=True)
rift_protect_msg = on_command("查看秘境战斗事件保底", priority=5, permission=GROUP, block=True)

# 秘境类改动，将原group分隔的群秘境形式更改为位置（依旧套用group），位置实现方式为位置与状态压成元组，原状态访问[0]数据，位置访问[1]数据
__rift_help__ = f"""
\r———秘境帮助———
1、探索秘境:
>消耗240点体力探索秘境获取随机奖励
2、秘境结算:
>结算秘境奖励
>获取秘境帮助信息
3、秘境战斗事件保底开启|关闭
>开启或关闭秘境战斗事件保底
4、查看秘境战斗事件保底
——————————————
tips：每天早八各位面将会生成一个随机等级的秘境供各位道友探索
""".strip()


@DRIVER.on_startup
async def read_rift_():
    global world_rift
    world_rift.update(old_rift_info.read_rift_info())
    logger.opt(colors=True).info(f"<green>历史rift数据读取成功</green>")


# 定时任务生成秘境，原群私有，改公有
@set_rift.scheduled_job("cron", hour=8, minute=0)
async def set_rift_(place_cls=place):
    global world_rift
    if place_cls.get_worlds():
        world_rift = {}
        for world_id in place_cls.get_worlds():
            if world_id == len(place_cls.get_worlds()) - 1:
                continue
            rift = Rift()
            rift.name = get_rift_type()
            place_all_id = [place_id for place_id in place_cls.get_world_place_list(world_id)]
            place_id = random.choice(place_all_id)
            rift.place = place_id
            rift.rank = max(config['rift'][rift.name]['rank'], 1 + int(world_id))
            rift.count = config['rift'][rift.name]['count']
            rift.time = config['rift'][rift.name]['time']
            world_rift[world_id] = rift
        old_rift_info.save_rift(world_rift)
        logger.opt(colors=True).info(f"<green>rift数据已保存</green>")


@create_rift_with_args.handle(parameterless=[Cooldown(at_sender=False)])
async def create_rift_with_args_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """
    生成秘境，格式为 生成秘境 等级 秘境名称 位置（不填则随机）
    """
    # 这里曾经是风控模块，但是已经不再需要了
    global world_rift  # 挖坑，不同位置的秘境

    args_str = args.extract_plain_text()
    nums = get_num_from_str(args_str)
    rift_name = get_strs_from_str(args_str)
    if not rift_name:
        msg = f"请输入秘境名称！！"
        await bot.send(event=event, message=msg)
        await create_rift_with_args.finish()
    rift_name = rift_name[0]
    if not nums:
        msg = f"请输入秘境等级！！"
        await bot.send(event=event, message=msg)
        await create_rift_with_args.finish()
    rift_rank = int(nums[0])

    if place.get_worlds():
        world_rift = {}
        for world_id in place.get_worlds():
            if world_id == len(place.get_worlds()) - 1:
                continue
            rift = Rift()
            rift.name = rift_name
            place_all_id = [place_id for place_id in place.get_world_place_list(world_id)]
            place_id = random.choice(place_all_id)
            rift.place = place_id
            rift.rank = rift_rank
            rift.count = 100
            rift.time = 100
            world_rift[world_id] = rift
            world_name = place.get_world_name(place_id)
            place_name = place.get_place_name(place_id)
            msg = (f"秘境：【{rift.name}】已在【{world_name}】的【{place_name}】开启！\r"
                   f"请诸位身在{world_name}的道友前往{place_name}(ID:{place_id})发送 探索秘境 来加入吧！")
            await bot.send(event=event, message=msg)
        old_rift_info.save_rift(world_rift)
        msg = f"rift数据已保存"
        await bot.send(event=event, message=msg)
    await create_rift_with_args.finish()


@rift_help.handle(parameterless=[Cooldown(at_sender=False)])
async def rift_help_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    """秘境帮助"""
    # 这里曾经是风控模块，但是已经不再需要了
    if session_id in cache_help:
        await bot.send(event=event, message=MessageSegment.image(cache_help[session_id]))
        await rift_help.finish()
    else:
        msg = __rift_help__
        await bot.send(event=event, message=msg)
        await rift_help.finish()


@create_rift.handle(parameterless=[Cooldown(at_sender=False)])
async def create_rift_(bot: Bot, event: GroupMessageEvent):
    """
    生成秘境，格式为 生成秘境 位置 秘境名称（可不填）//未完成
    :param bot:
    :param event:
    :return:
    """
    # 这里曾经是风控模块，但是已经不再需要了
    global world_rift  # 挖坑，不同位置的秘境
    if place.get_worlds():
        world_rift = {}
        for world_id in place.get_worlds():
            if world_id == len(place.get_worlds()) - 1:
                continue
            rift = Rift()
            rift.name = get_rift_type()
            place_all_id = [place_id for place_id in place.get_world_place_list(world_id)]
            place_id = random.choice(place_all_id)
            rift.place = place_id
            rift.rank = config['rift'][rift.name]['rank']
            rift.count = config['rift'][rift.name]['count']
            rift.time = config['rift'][rift.name]['time']
            world_rift[world_id] = rift
            world_name = place.get_world_name(place_id)
            place_name = place.get_place_name(place_id)
            msg = (f"秘境：【{rift.name}】已在【{world_name}】的【{place_name}】开启！\r"
                   f"请诸位身在{world_name}的道友前往{place_name}(ID:{place_id})发送 探索秘境 来加入吧！")
            await bot.send(event=event, message=msg)
        old_rift_info.save_rift(world_rift)
        msg = f"rift数据已保存"
        await bot.send(event=event, message=msg)
    await create_rift.finish()


@complete_rift.handle(parameterless=[Cooldown(stamina_cost=240, at_sender=False)])
async def complete_rift_(bot: Bot, event: GroupMessageEvent):
    """探索秘境"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    is_type, msg = await check_user_type(user_id, 0)  # 需要无状态的用户
    is_old_type, msg = await check_user_type(user_id, 3)  # 需要无状态的用户
    if not (is_type or is_old_type):
        await sql_message.update_user_stamina(user_id, 240, 1)
        await bot.send(event=event, message=msg)
        await complete_rift.finish()

    place_id = await place.get_now_place_id(user_id)
    world_id = place.get_world_id(place_id)
    world_name = place.get_world_name(place_id)
    try:
        world_rift[world_id]
    except KeyError:
        msg = f'道友所在位面【{world_name}】尚未有秘境出世，请道友耐心等待!'
        await sql_message.update_user_stamina(user_id, 240, 1)
        await bot.send(event=event, message=msg)
        await complete_rift.finish()

    if place_id != world_rift[world_id].place:
        far, start_place, to_place = place.get_distance(place_id, world_rift[world_id].place)
        await sql_message.update_user_stamina(user_id, 240, 1)
        msg = simple_md(f"\r道友所在位置没有秘境出世!!\r"
                        f"当前位面【{world_name}】的秘境【{world_rift[world_id].name}】在距你{far:.1f}万里的：【{to_place}】\r"
                        f"请", "前往", f"前往 {to_place}", "秘境所在位置探索！")
        await bot.send(event=event, message=msg)
        await complete_rift.finish()

    title = f"道友进入秘境：{world_rift[world_id].name}，探索需要花费体力240点！！，余剩体力{user_info['user_stamina']}/2400！"
    await sql_message.do_work(user_id, 0)
    rift_rank = world_rift[world_id].rank  # 秘境等级
    rift_protect = await limit_handle.get_user_rift_protect(user_id)
    rift_type = get_story_type()  # 无事、宝物、战斗
    if rift_protect:
        if rift_type != "战斗":
            if rift_protect == 1:
                rift_type = "战斗"
            else:
                await limit_handle.update_user_limit(user_id, 8, 1, 1)
    if rift_type == "无事":
        msg = random.choice(NONEMSG)
        item_info = items.get_data_by_item_id(660001)
        await sql_message.send_back(user_id, 660001, item_info["name"], item_info['type'], 1, 1)
    elif rift_type == "战斗":
        result, msg = await get_boss_battle_info(user_info, rift_rank)
        if rift_protect:
            await limit_handle.update_user_limit(user_id, 8, 9)
        msg = msg + msg_handler(result)
    elif rift_type == "宝物":
        msg = await get_treasure_info(user_info, rift_rank)
    elif rift_type == "掉血事件":
        protect_item = await sql_message.get_item_by_good_id_and_user_id(user_id, 660001)
        protect_item = protect_item if protect_item else {}
        if protect_item.get("goods_num", 0) > 0:
            await sql_message.update_back_j(user_id, 660001, 1)
            msg = "道友踏入秘境一番探索，正要进入一处险境寻宝，怀中一物却轰然碎裂，一道念头自心中升起：不可进入！出秘境后方才得知，方才欲探之地有不少修士折损了修为。"
        else:
            msg = await get_dxsj_info("掉血事件", user_info)
    await limit_handle.update_user_log_data(user_id, msg)
    msg = main_md(title, msg,
                  "秘境帮助", "秘境帮助",
                  "余剩体力", "体力",
                  "查看日常", "日常中心",
                  "继续探索", "探索秘境")
    await bot.send(event=event, message=msg)
    await complete_rift.finish()


@rift_protect_handle.handle(parameterless=[Cooldown(cd_time=2400, at_sender=False)])
async def rift_protect_handle_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """秘境保底"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']

    args_str = args.extract_plain_text()
    arg_strs = get_strs_from_str(args_str)
    handle_type = arg_strs[0] if arg_strs else 0

    rift_protect = await limit_handle.get_user_rift_protect(user_id)
    msg = "请输入正确的指令！！开启|关闭！！"
    if handle_type == "开启":
        if rift_protect:
            msg = "道友已开启秘境战斗事件保底，请勿重复开启！！！"
        else:
            msg = "成功开启秘境战斗事件保底！！！可以使用【查看秘境战斗事件保底】来查看距离保底探索次数！！"
            await limit_handle.update_user_limit(user_id, 8, 10)
    if handle_type == "关闭":
        if rift_protect:
            if rift_protect > 10:
                msg = f"当前无法关闭秘境保底！！！请在距离秘境保底10次以内时关闭！！！当前距离保底余剩{rift_protect}次"
            else:
                msg = "成功关闭秘境战斗事件保底！！！"
                await limit_handle.update_user_limit(user_id, 8, rift_protect, 1)
        else:
            msg = "道友未开启秘境战斗事件保底！！！"
    await bot.send(event=event, message=msg)
    await rift_protect_handle.finish()


@rift_protect_msg.handle(parameterless=[Cooldown(cd_time=10, at_sender=False)])
async def rift_protect_msg_(bot: Bot, event: GroupMessageEvent):
    """秘境保底"""

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']

    rift_protect = await limit_handle.get_user_rift_protect(user_id)
    if rift_protect:
        msg = f"当前距离保底余剩{rift_protect}次"
    else:
        msg = "道友未开启秘境战斗事件保底！！！"
    await bot.send(event=event, message=msg)
    await rift_protect_msg.finish()
