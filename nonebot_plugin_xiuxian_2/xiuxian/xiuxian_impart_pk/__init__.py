import random

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent
)

from .impart_pk import impart_pk
from .impart_pk_uitls import impart_pk_check
from .. import NICKNAME
from ..xiuxian_impart import impart_check
from ..xiuxian_utils.clean_utils import main_md
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import check_user, check_user_type
from ..xiuxian_utils.xiuxian2_handle import sql_message, xiuxian_impart

impart_pk_now_all = on_command("虚神界对决", priority=3, permission=GROUP, block=True)
impart_pk_now = on_command("确认虚神界对决", priority=3, permission=GROUP, block=True)
impart_pray = on_command("确认虚神界祈愿", priority=3, permission=GROUP, block=True)
impart_shop = on_command("虚神界兑换", priority=3, permission=GROUP, block=True)
impart_pk_exp = on_command("虚神界闭关", aliases={"进入虚神界修炼"}, priority=3, permission=GROUP, block=True)


@impart_shop.handle(parameterless=[Cooldown(stamina_cost=0)])
async def impart_shop_(bot: Bot, event: GroupMessageEvent):
    """虚神界兑换"""
    msg = "敬请期待"
    await bot.send(event=event, message=msg)
    await impart_shop.finish()


@impart_pk_now_all.handle(parameterless=[Cooldown(stamina_cost=0)])
async def impart_pk_now_all_(bot: Bot, event: GroupMessageEvent):
    """虚神界活动"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    pk_num = await impart_pk.get_impart_pk_num(user_id)
    if pk_num:
        msg = f"道友今日已经完成虚神界行动了，明天再来吧！"
        await bot.send(event=event, message=msg)
        await impart_pk_now_all.finish()
    msg = main_md("请选择你在虚神界中的行动",
                  f"虚神界对决：与{NICKNAME}对决，根据表现获得思恋结晶奖励\r"
                  f"虚神界祈愿：在虚神界中进行祈愿，获取祈愿结晶*1",
                  "虚神界对决", "确认虚神界对决",
                  "虚神界祈愿", "确认虚神界祈愿",
                  "传承祈愿", "传承祈愿",
                  "传承抽卡", "传承抽卡"
                  )
    await bot.send(event=event, message=msg)
    await impart_pk_now_all.finish()


@impart_pray.handle(parameterless=[Cooldown(stamina_cost=0)])
async def impart_pray_(bot: Bot, event: GroupMessageEvent):
    """虚神界祈愿"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    pk_num = await impart_pk.get_impart_pk_num(user_id)
    if pk_num:
        msg = f"道友今日已经在虚神界行动过了，明天再来吧！"
        await bot.send(event=event, message=msg)
        await impart_pray.finish()
    await impart_check(user_id)
    await impart_pk.update_impart_pk_num(user_id)
    await xiuxian_impart.update_pray_stone_num(1, user_id, 1)
    tag = random.choice(["福签，运势亨通", "平签，多喜乐，常安宁", "喜签，喜事不断"])
    combined_msg = f"\r进入虚神界进行祈愿，求得一{tag}，获得祈愿结晶一颗"
    await bot.send(event=event, message=combined_msg)
    await impart_pray.finish()


@impart_pk_now.handle(parameterless=[Cooldown(stamina_cost=0)])
async def impart_pk_now_(bot: Bot, event: GroupMessageEvent):
    """虚神界对决"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    pk_num = await impart_pk.get_impart_pk_num(user_id)
    if pk_num:
        msg = f"道友今日已经在虚神界行动过了，明天再来吧！"
        await bot.send(event=event, message=msg)
        await impart_pk_now.finish()
    await impart_check(user_id)
    await impart_pk.update_impart_pk_num(user_id)
    stones = 8
    await xiuxian_impart.update_stone_num(stones, user_id, 1)
    combined_msg = f"\r进入虚神界与{NICKNAME}对决，将{NICKNAME}击败，获得思恋结晶{stones}颗"
    await bot.send(event=event, message=combined_msg)
    await impart_pk_now.finish()


@impart_pk_exp.handle(parameterless=[Cooldown()])
async def impart_pk_exp_(bot: Bot, event: GroupMessageEvent):
    """虚神界闭关"""

    user_type = 5  # 状态0为无事件

    user_info = await check_user(event)

    user_id = user_info['user_id']
    is_type, msg = await check_user_type(user_id, 0)
    if is_type:  # 符合
        impart_data_draw = await impart_pk_check(user_id)  # 虚神界余剩闭关时间
        if int(impart_data_draw['exp_day']) > 0:
            await sql_message.do_work(user_id, user_type)
            msg = f"进入虚神界，开始闭关，余剩虚神界内加速修炼时间：{int(impart_data_draw['exp_day'])}分钟，如需出关，发送【出关】！"
            await bot.send(event=event, message=msg)
            await impart_pk_exp.finish()
        else:
            msg = "道友虚神界内修炼余剩时长不足"
            await bot.send(event=event, message=msg)
            await impart_pk_exp.finish()
    else:
        await bot.send(event=event, message=msg)
        await impart_pk_exp.finish()
