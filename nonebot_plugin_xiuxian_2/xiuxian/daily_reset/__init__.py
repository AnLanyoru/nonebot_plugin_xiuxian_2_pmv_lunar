from nonebot import require, logger

from ..xiuxian_buff import two_exp_cd, reset_send_stone, reset_stone_exp_up
from ..xiuxian_impart_pk import impart_pk
from ..xiuxian_limit import limit_data
from ..xiuxian_sect import sect_config
from ..xiuxian_utils.xiuxian2_handle import sql_message

weekly_work = require("nonebot_plugin_apscheduler").scheduler
materials_update = require("nonebot_plugin_apscheduler").scheduler
reset_user_task = require("nonebot_plugin_apscheduler").scheduler
daily_reset = require("nonebot_plugin_apscheduler").scheduler


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
