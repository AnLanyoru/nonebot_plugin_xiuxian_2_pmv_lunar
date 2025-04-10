import math
from datetime import datetime

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent
)
from nonebot.params import CommandArg

from ..database_utils.move_database import save_move_data, read_move_data
from ..xiuxian_config import convert_rank
from ..xiuxian_place import place
from ..xiuxian_utils.clean_utils import get_num_from_str, get_strs_from_str, simple_md
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import (
    check_user, check_user_type
)
from ..xiuxian_utils.xiuxian2_handle import sql_message

MAP_BUTTON = "102368631_1740931292"


go_to = on_command("移动", aliases={"前往", "去"}, permission=GROUP, priority=10, block=True)
get_map = on_command("地图", aliases={"我的位置", "位置"}, permission=GROUP, priority=10, block=True)
complete_move = on_command("行动结算", aliases={"到达"}, permission=GROUP, priority=10, block=True)
stop_move = on_command("停止移动", permission=GROUP, priority=10, block=True)
near_player = on_command("附近玩家", aliases={"附近"}, permission=GROUP, priority=10, block=True)


@go_to.handle(parameterless=[Cooldown()])
async def go_to_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """
    移动位置
    """

    user_info = await check_user(event)

    user_id = user_info['user_id']

    is_type, msg = await check_user_type(user_id, 0)  # 需要空闲的用户

    if not is_type:
        await bot.send(event=event, message=msg)
        await complete_move.finish()

    msg_text = args.extract_plain_text()
    start_id = await place.get_now_place_id(user_id)
    num = get_num_from_str(msg_text)
    name = get_strs_from_str(msg_text)
    place_id = None
    if name:
        place_id = place.get_place_id(name[0])
    if num:
        place_id = int(num[0])
    if place_id is None:
        msg = "请输入正确的地点或地点id！！！"
        await bot.send(event=event, message=msg)
        await go_to.finish()

    far, name_1, name_2 = place.get_distance(start_id, place_id)
    if far == "unachievable":
        msg = f"无法从【{name_1}】移动至【{name_2}】！！！目的地跨位面或不可到达"

    elif far == 0:
        msg = f"道友已在【{name_1}】！！"

    else:
        need_time = far / (convert_rank(user_info["level"])[0] + 60) * 60  # * 10
        move_data = {
            "start_id": start_id,
            "to_id": place_id,
            "need_time": need_time
        }
        await save_move_data(user_id, move_data)
        await sql_message.do_work(user_id, -1, need_time)
        need_time = math.ceil(need_time)
        msg = f"道友开始从【{name_1}】移动至【{name_2}】, 距离约：{far:.1f}万里, 预计耗时{need_time}分钟！"

    await bot.send(event=event, message=msg)
    await go_to.finish()


@stop_move.handle(parameterless=[Cooldown(cd_time=30)])
async def stop_move_(bot: Bot, event: GroupMessageEvent):
    """停止移动"""

    user_info = await check_user(event)

    user_id = user_info['user_id']

    is_type, msg = await check_user_type(user_id, int(-1))  # 需要在移动中的用户
    if is_type:
        msg = "\r道友飞速赶回了出发点！！"
        await sql_message.do_work(user_id, 0)
    else:
        pass
    await bot.send(event=event, message=msg)
    await stop_move.finish()


@complete_move.handle(parameterless=[Cooldown()])
async def complete_move_(bot: Bot, event: GroupMessageEvent):
    """移动结算"""

    user_info = await check_user(event)

    user_id = user_info['user_id']

    is_type, msg = await check_user_type(user_id, int(-1))  # 需要在移动中的用户
    if not is_type:
        await bot.send(event=event, message=msg)
        await complete_move.finish()
    else:
        user_cd_message = await sql_message.get_user_cd(user_id)
        work_time = datetime.strptime(
            user_cd_message['create_time'], "%Y-%m-%d %H:%M:%S.%f"
        )
        pass_time = (datetime.now() - work_time).seconds // 60  # 时长计算
        move_info = await read_move_data(user_id)
        need_time = move_info["need_time"]
        place_name = place.get_place_name(move_info["to_id"])
        if pass_time < need_time:
            last_time = math.ceil(need_time - pass_time)
            msg = f"向【{place_name}】的移动，预计{last_time}分钟后可结束"
            await bot.send(event=event, message=msg)
            await complete_move.finish()
        else:  # 移动结算逻辑
            await sql_message.do_work(user_id, 0)
            place_id = move_info["to_id"]
            await place.set_now_place_id(user_id, place_id)
            msg = f"道友雷厉风行，成功到达【{place_name}】！"
            await bot.send(event=event, message=msg)
            await complete_move.finish()


@get_map.handle(parameterless=[Cooldown()])
async def get_map_(bot: Bot, event: GroupMessageEvent):
    """
    获取地图
    """

    user_info = await check_user(event)

    user_id = user_info['user_id']
    place_id = await place.get_now_place_id(user_id)
    world_name = place.get_world_name(place_id)
    world_id = place.get_world_id(place_id)
    msg = f"\r————{world_name}地图————\r"
    place_dict = place.get_place_dict()
    for get_place_id, places in place_dict.items():
        place_world_id = places[1][2]
        if place_world_id == world_id:
            if place_id == get_place_id:
                msg += f"地区ID:{get_place_id}【{places[0]}】位置:{places[1][:2]}<道友在这\r"

            else:
                msg += f"地区ID:{get_place_id}【{places[0]}】位置:{places[1][:2]}\r"
        else:
            pass
    msg += "\r发送【"
    msg = simple_md(msg, "前往", "前往", "】+【目的地ID】来进行移动哦",
                    MAP_BUTTON)
    await bot.send(event=event, message=msg)
    await get_map.finish()


@near_player.handle(parameterless=[Cooldown()])
async def near_player_(bot: Bot, event: GroupMessageEvent):
    """
    获取附近玩家： 10名
    """

    user_info = await check_user(event)

    user_id = user_info['user_id']
    place_id = await place.get_now_place_id(user_id)
    place_name = place.get_place_name(place_id)
    msg = f"\r附近的道友："
    nearby_players = await sql_message.get_nearby_player(place_id, user_info["exp"])
    for player in nearby_players:
        msg += f"\r{player['user_name']} {player['level']}"
    msg = simple_md(f"当前道友在ID：{place_id} ",
                    f"{place_name}", f"前往 {place_name}",
                    msg,
                    MAP_BUTTON)
    await bot.send(event=event, message=msg)
    await near_player.finish()
