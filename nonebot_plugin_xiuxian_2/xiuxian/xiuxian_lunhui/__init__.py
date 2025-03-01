import random

from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent)
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from ..xiuxian_buff import two_exp_cd
from ..xiuxian_config import XiuConfig
from ..xiuxian_data.data.境界_data import level_data
from ..xiuxian_impart_pk import impart_pk
from ..xiuxian_sect import sect_config
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import (
    check_user, number_to, check_user_type
)
from ..xiuxian_utils.xiuxian2_handle import sql_message

__warring_help__ = """

———轮回帮助———
散尽修为，轮回重修，将万世的道果凝聚为极致天赋
修为、攻击修炼将被清空！！
进入轮回：
>获得轮回灵根
感悟源宇之秘：
>获得源宇道根
感悟道之本源：
>获得道之本源，仅有感悟道之本源者可突破彼岸境！！
———特殊功能———
自废修为：
>字面意思，仅炼体境可用
""".strip()

from ..xiuxian_work.work_database import save_work_info

cache_help_fk = {}

warring_help = on_command("轮回重修帮助", aliases={"轮回重修", "轮回"}, priority=12, permission=GROUP, block=True)
lunhui = on_command('进入轮回', priority=15, permission=GROUP, block=True)
twolun = on_command('感悟源宇之秘', priority=15, permission=GROUP, block=True)
threelun = on_command('感悟道之本源', priority=15, permission=GROUP, block=True)
resetting = on_command('自废修为', priority=15, permission=GROUP, block=True)
gettest = on_command('修炼资源领取', priority=15, permission=GROUP, block=True)
timeback = on_command('回到过去', priority=15, permission=SUPERUSER, block=True)
time_set_now = on_command('逆转时空', priority=15, permission=SUPERUSER, block=True)


@warring_help.handle(parameterless=[Cooldown()])
async def warring_help_(bot: Bot, event: GroupMessageEvent):
    """轮回重修帮助"""

    msg = __warring_help__
    await bot.send(event=event, message=msg)
    await warring_help.finish()


@lunhui.handle(parameterless=[Cooldown()])
async def lunhui_(bot: Bot, event: GroupMessageEvent):
    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_msg = await sql_message.get_user_info_with_id(user_id)
    user_name = user_msg['user_name']
    user_root = user_msg['root_type']
    list_level_all = list(level_data.keys())
    level = user_info['level']

    if user_root == '轮回灵根':
        msg = "道友已是轮回之身！"
        await bot.send(event=event, message=msg)
        await lunhui.finish()

    if user_root == '源宇道根':
        msg = "道友已然感悟源宇之秘！"
        await bot.send(event=event, message=msg)
        await lunhui.finish()
    if user_root == '道之本源':
        msg = "道友已然触及道之本源！"
        await bot.send(event=event, message=msg)
        await lunhui.finish()
    is_type, msg = await check_user_type(user_id, 0)
    if is_type:
        pass
    else:
        await bot.send(event=event, message=msg)
        await lunhui.finish()

    if list_level_all.index(level) >= list_level_all.index(XiuConfig().lunhui_min_level):
        exp = user_msg['exp']
        now_exp = exp - 100
        await sql_message.updata_level(user_id, '求道者')  # 重置用户境界
        await sql_message.update_levelrate(user_id, 0)  # 重置突破成功率
        await sql_message.update_j_exp(user_id, now_exp)  # 重置用户修为
        await sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        await sql_message.update_user_atkpractice(user_id, 0)  # 重置用户攻修等级
        await save_work_info(user_id, {})
        await sql_message.update_root(user_id, 6)  # 更换轮回灵根
        msg = f"数世轮回磨不灭，重回绝颠谁能敌，恭喜大能{user_name}轮回成功！"
        await bot.send(event=event, message=msg)
        await lunhui.finish()
    else:
        msg = f"道友境界未达要求，进入轮回的最低境界为{XiuConfig().lunhui_min_level}"
        await bot.send(event=event, message=msg)
        await lunhui.finish()


@twolun.handle(parameterless=[Cooldown()])
async def twolun_(bot: Bot, event: GroupMessageEvent):
    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_msg = await sql_message.get_user_info_with_id(user_id)
    user_name = user_msg['user_name']
    user_root = user_msg['root_type']
    list_level_all = list(level_data.keys())
    level = user_info['level']

    if user_root == '源宇道根':
        msg = "道友已然感悟源宇之秘！！"
        await bot.send(event=event, message=msg)
        await twolun.finish()
    if user_root == '道之本源':
        msg = "道友已然触及道之本源！"
        await bot.send(event=event, message=msg)
        await twolun.finish()

    if user_root != '轮回灵根':
        msg = "道友还未轮回过，请先进入轮回！"
        await bot.send(event=event, message=msg)
        await twolun.finish()
    is_type, msg = await check_user_type(user_id, 0)
    if is_type:
        pass
    else:
        await bot.send(event=event, message=msg)
        await twolun.finish()

    if list_level_all.index(level) >= list_level_all.index(XiuConfig().twolun_min_level) and user_root == '轮回灵根':
        exp = user_msg['exp']
        now_exp = exp - 100
        await sql_message.updata_level(user_id, '求道者')  # 重置用户境界
        await sql_message.update_levelrate(user_id, 0)  # 重置突破成功率
        await sql_message.update_j_exp(user_id, now_exp)  # 重置用户修为
        await sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        await sql_message.update_user_atkpractice(user_id, 0)  # 重置用户攻修等级
        await save_work_info(user_id, {})
        await sql_message.update_root(user_id, 7)  # 更换轮回灵根
        msg = f"求道散尽半仙躯，堪能窥得源宇秘，恭喜大能{user_name}成功感悟源宇之秘！"
        await bot.send(event=event, message=msg)
        await twolun.finish()
    else:
        msg = f"道友境界未达要求，感悟源宇之秘的最低境界为{XiuConfig().twolun_min_level}！"
        await bot.send(event=event, message=msg)
        await twolun.finish()


@threelun.handle(parameterless=[Cooldown()])
async def threelun_(bot: Bot, event: GroupMessageEvent):
    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_msg = await sql_message.get_user_info_with_id(user_id)
    user_name = user_msg['user_name']
    user_root = user_msg['root_type']
    list_level_all = list(level_data.keys())
    level = user_info['level']

    if user_root == '道之本源':
        msg = "道友已然触及道之本源！"
        await bot.send(event=event, message=msg)
        await threelun.finish()

    if user_root != '源宇道根':
        msg = "道友根基未牢，请先感悟源宇之秘！"
        await bot.send(event=event, message=msg)
        await threelun.finish()
    is_type, msg = await check_user_type(user_id, 0)
    if is_type:
        pass
    else:
        await bot.send(event=event, message=msg)
        await threelun.finish()

    if list_level_all.index(level) >= list_level_all.index(
            XiuConfig().threelun_min_level) and user_root == '源宇道根':
        exp = user_msg['exp']
        now_exp = exp - 100
        await sql_message.updata_level(user_id, '求道者')  # 重置用户境界
        await sql_message.update_levelrate(user_id, 0)  # 重置突破成功率
        await sql_message.update_j_exp(user_id, now_exp)  # 重置用户修为
        await sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        await sql_message.update_user_atkpractice(user_id, 0)  # 重置用户攻修等级
        await save_work_info(user_id, {})
        await sql_message.update_root(user_id, 8)  # 更换灵根
        msg = f"帝蕴浸灭求一道，触及本源登顶峰，恭喜大能{user_name}成功感悟道之本源！"
        await bot.send(event=event, message=msg)
        await threelun.finish()
    else:
        msg = f"道友境界未达要求，感悟道之本源的最低境界为{XiuConfig().threelun_min_level}！"
        await bot.send(event=event, message=msg)
        await threelun.finish()


@resetting.handle(parameterless=[Cooldown()])
async def resetting_(bot: Bot, event: GroupMessageEvent):
    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_msg = await sql_message.get_user_info_with_id(user_id)
    user_name = user_msg['user_name']

    if user_msg['level'][:-2] == '炼体境':
        exp = user_msg['exp']
        now_exp = exp - 100
        await sql_message.updata_level(user_id, '求道者')  # 重置用户境界
        await sql_message.update_levelrate(user_id, 0)  # 重置突破成功率
        await sql_message.update_j_exp(user_id, now_exp)  # 重置用户修为
        await sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        msg = f"{user_name}现在是一介凡人了！！"
        await bot.send(event=event, message=msg)
        await resetting.finish()
    else:
        msg = f"道友境界未达要求，仅有练体境可自废修为！"
        await bot.send(event=event, message=msg)
        await resetting.finish()


@gettest.handle(parameterless=[Cooldown()])
async def gettest_(bot: Bot, event: GroupMessageEvent, state: T_State):
    # 这里曾经是风控模块，但是已经不再需要了

    await bot.send(event=event, message="正在申请测试用灵石，请在10秒内输入后台获取的代码")
    key = ""
    key_pre = "qwert-yuioppppp-asdffghjk-llzxcvb-nm12345-67890"
    for e in range(20):
        key += random.choice(key_pre)
    print(key)
    state["key"] = key


@gettest.receive()
async def gettest_(bot: Bot, event: GroupMessageEvent, state: T_State):
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    input_key = event.get_plaintext().strip()

    if input_key == state["key"]:
        user_id = user_info['user_id']
        user_msg = await sql_message.get_user_info_with_id(user_id)
        user_name = user_msg['user_name']
        await sql_message.update_ls(user_id, int(100000000000000), 1)
        msg = f"{user_name}获取灵石成功，共获取100000000000000 | {number_to(100000000000000)}枚灵石，别嫌少肯定够用了"
        await bot.send(event=event, message=msg)
        await gettest.finish()
    else:
        msg = "密钥错误！！请不要随意调用调试接口！！！"
        await bot.send(event=event, message=msg)
        await gettest.finish()


@time_set_now.handle(parameterless=[Cooldown()])
async def time_set_now_(bot: Bot, event: GroupMessageEvent):

    await sql_message.sign_remake()
    await sql_message.day_num_reset()
    await two_exp_cd.re_data()
    await sql_message.beg_remake()
    await impart_pk.re_data()
    await sql_message.sect_task_reset()
    await sql_message.sect_elixir_get_num_reset()
    await sql_message.reset_work_num()
    all_sects = await sql_message.get_all_sects_id_scale()
    for s in all_sects:
        sect_info = await sql_message.get_sect_info(s['sect_id'])
        if sect_info['elixir_room_level']:
            elixir_room_cost = \
                sect_config['宗门丹房参数']['elixir_room_level'][str(sect_info['elixir_room_level'])]['level_up_cost'][
                    '建设度']
            if sect_info['sect_materials'] < elixir_room_cost:
                logger.opt(colors=True).info(f"<red>宗门：{sect_info['sect_name']}的资材无法维持丹房</red>")
                continue
            else:
                await sql_message.update_sect_materials(sect_id=sect_info['sect_id'], sect_materials=elixir_room_cost,
                                                        key=2)
    logger.opt(colors=True).info(f"<green>已重置所有宗门任务次数、宗门丹药领取次数，已扣除丹房维护费</green>")
    msg = f"逆转时空，让一切重置次数！！！"
    await bot.send(event=event, message=msg)
    await time_set_now.finish()
