from nonebot import require, logger, on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot
from nonebot.permission import SUPERUSER

from .tools import get_world_boss_damage_top_limit, send_world_boss_point_top_3, send_world_boss_point, \
    send_world_boss_point_all, all_world_id
from ..xiuxian_buff import two_exp_cd, reset_send_stone, reset_stone_exp_up
from ..xiuxian_database.database_connect import database
from ..xiuxian_impart_pk import impart_pk
from ..xiuxian_limit import limit_data
from ..xiuxian_sect import sect_config
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.xiuxian2_handle import sql_message

weekly_work = require("nonebot_plugin_apscheduler").scheduler
materials_update = require("nonebot_plugin_apscheduler").scheduler
reset_user_task = require("nonebot_plugin_apscheduler").scheduler
daily_reset = require("nonebot_plugin_apscheduler").scheduler

world_boss_point_hand_send = on_command('世界BOSS积分发放', priority=1, permission=SUPERUSER, block=True)


@world_boss_point_hand_send.handle(parameterless=[Cooldown()])
async def world_boss_point_hand_send_(bot: Bot, event: GroupMessageEvent):
    """挑战世界boss"""

    await send_world_boss_point_top_3(database)

    for world_id in all_world_id:
        top_10_list = await get_world_boss_damage_top_limit(database, 10, world_id)
        await send_world_boss_point(database, top_10_list, 20)

        top_100_list = await get_world_boss_damage_top_limit(database, 100, world_id)
        await send_world_boss_point(database, top_100_list, 20)

    await send_world_boss_point_all(database, 10)

    msg = f"已发放世界BOSS累计伤害奖励"
    await bot.send(event=event, message=msg)
    await world_boss_point_hand_send.finish()


# 每日0点重置用户宗门任务次数、宗门丹药领取次数
@reset_user_task.scheduled_job("cron", hour=0, minute=30)
async def reset_user_task_():
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


# 定时任务每1小时按照宗门贡献度增加资材
@materials_update.scheduled_job("cron", hour=sect_config["发放宗门资材"]["时间"])
async def materials_update_():
    all_sects = await sql_message.get_all_sects_id_scale()
    all_sects_id = [(sect_per['sect_id'],) for sect_per in all_sects]
    await sql_message.daily_update_sect_materials(all_sects_id)
    logger.opt(colors=True).info(f"<green>已更新所有宗门的资材</green>")


@weekly_work.scheduled_job("cron", day_of_week='mon', hour=4)
async def weekly_work_():
    await limit_data.redata_limit_by_key('state')
    logger.opt(colors=True).info(f"<green>已更新周常事件</green>")


@weekly_work.scheduled_job("cron", day_of_week='mon', hour=0)
async def weekly_world_boss_reset_():
    await database.sql_execute("update world_boss set fight_damage=0")
    logger.opt(colors=True).info(f"<green>已重置世界BOSS累计伤害</green>")


@weekly_work.scheduled_job("cron", day_of_week='sun', hour=9)
async def weekly_world_boss_point_give_():
    await send_world_boss_point_top_3(database)

    for world_id in all_world_id:
        top_10_list = await get_world_boss_damage_top_limit(database, 10, world_id)
        await send_world_boss_point(database, top_10_list, 20)

        top_100_list = await get_world_boss_damage_top_limit(database, 100, world_id)
        await send_world_boss_point(database, top_100_list, 20)

    await send_world_boss_point_all(database, 10)

    logger.opt(colors=True).info(f"<green>已发放世界BOSS累计伤害奖励</green>")


# 每日0点重置用虚神界次数
@daily_reset.scheduled_job("cron", hour=0, minute=0)
async def daily_reset_():
    await impart_pk.re_data()
    logger.opt(colors=True).info(f"<green>已重置虚神界行动次数</green>")

    await sql_message.sect_task_reset()
    logger.opt(colors=True).info(f"<green>宗门任务次数重置成功！</green>")

    await sql_message.sect_elixir_get_num_reset()
    logger.opt(colors=True).info(f"<green>宗门丹药领取次数重置成功！</green>")

    await sql_message.reset_work_num()
    logger.opt(colors=True).info(f"<green>用户悬赏令刷新次数重置成功</green>")

    await sql_message.day_num_reset()
    logger.opt(colors=True).info(f"<green>每日丹药使用次数重置成功！</green>")

    await sql_message.sign_remake()
    logger.opt(colors=True).info(f"<green>每日修仙签到重置成功！</green>")

    await two_exp_cd.re_data()
    logger.opt(colors=True).info(f"<green>双修次数已刷新！</green>")

    await reset_send_stone()
    logger.opt(colors=True).info(f"<green>收送灵石限制重置成功！</green>")

    await reset_stone_exp_up()
    logger.opt(colors=True).info(f"<green>灵石修炼限制重置成功！</green>")

    await sql_message.beg_remake()
    logger.opt(colors=True).info(f"<green>仙途奇缘重置成功！</green>")

    await database.sql_execute("update world_boss set fight_num=0")
    logger.opt(colors=True).info(f"<green>每日BOSS挑战次数重置成功！</green>")
