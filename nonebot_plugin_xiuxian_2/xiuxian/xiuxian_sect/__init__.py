import json
import random
import re
import time

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    MessageSegment,
)
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .sectconfig import sect_config
from ..types import SectPosition
from ..xiuxian_config import XiuConfig, convert_rank
from ..xiuxian_data.data.功法概率设置_data import skill_rate_set
from ..xiuxian_data.data.境界_data import level_data
from ..xiuxian_data.data.宗门玩法配置_data import sect_config_data
from ..xiuxian_limit.limit_database import limit_handle
from ..xiuxian_utils.clean_utils import get_num_from_str, get_strs_from_str, simple_md, three_md, main_md, msg_handler
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown, UserCmdLock
from ..xiuxian_utils.other_set import OtherSet
from ..xiuxian_utils.random_names import get_random_sect_name
from ..xiuxian_utils.utils import (
    check_user, number_to,
    get_msg_pic, send_msg_handler,
    get_id_from_str
)
from ..xiuxian_utils.xiuxian2_handle import (
    sql_message,
    get_main_info_msg, UserBuffDate, get_sec_msg
)

config = sect_config
SECT_BUTTON = "102368631_1739819758"
LEVLECOST = config["LEVLECOST"]
cache_help = {}
userstask = {}

buffrankkey = {
    "后天品级": 1,
    "先天品级": 2,
    "神丹品级": 3,
    "虚劫品级": 4,
    "生死品级": 5,
    "神海品级": 6,
    "神劫品级": 7,
    "神极品级": 8,
    "神变品级": 10,
    "界主品级": 100,
    "天尊品级": 1000,
}

upatkpractice = on_command("升级攻击修炼", priority=5, permission=GROUP, block=True)
my_sect = on_command("我的宗门", aliases={"宗门信息"}, priority=5, permission=GROUP, block=True)
create_sect = on_command("创建宗门", priority=5, permission=GROUP, block=True)
join_sect = on_command("加入宗门", priority=5, permission=GROUP, block=True)
sect_position_update = on_command("宗门职位变更", priority=5, permission=GROUP, block=True)
sect_donate = on_command("宗门捐献", priority=5, permission=GROUP, block=True)
sect_out = on_command("退出宗门", priority=5, permission=GROUP, block=True)
sect_kick_out = on_command("踢出宗门", priority=5, permission=GROUP, block=True)
sect_owner_change = on_command("宗主传位", priority=5, permission=GROUP, block=True)
sect_list = on_command("宗门列表", priority=5, permission=GROUP, block=True)
sect_task = on_command("宗门任务接取", aliases={"我的宗门任务"}, priority=7, permission=GROUP, block=True)
sect_task_complete = on_command("宗门任务完成", priority=7, permission=GROUP, block=True)
sect_task_refresh = on_command("宗门任务刷新", priority=7, permission=GROUP, block=True)
sect_mainbuff_get = on_command("宗门功法搜寻", aliases={"搜寻宗门功法", "宗门搜寻功法"}, priority=6, permission=GROUP,
                               block=True)
sect_mainbuff_learn = on_command("学习宗门功法", priority=5, permission=GROUP, block=True)
sect_secbuff_get = on_command("宗门神通搜寻", aliases={"搜寻宗门神通", "宗门搜寻神通"}, priority=6, permission=GROUP,
                              block=True)
sect_secbuff_learn = on_command("学习宗门神通", priority=5, permission=GROUP, block=True)
sect_buff_info = on_command("宗门功法查看", aliases={"查看宗门功法"}, priority=9, permission=GROUP, block=True)
sect_users = on_command("宗门成员查看", aliases={"查看宗门成员"}, priority=8, permission=GROUP, block=True)
sect_users_donate_check = on_command("宗门周贡检查", aliases={"检查宗门周贡"}, priority=8, permission=GROUP, block=True)
sect_elixir_room_make = on_command("宗门丹房建设", aliases={"建设宗门丹房"}, priority=5, permission=GROUP, block=True)
sect_elixir_get = on_command("宗门丹药领取", aliases={"领取宗门丹药领取"}, priority=5, permission=GROUP, block=True)
sect_close = on_command("关闭宗门加入", aliases={"开启宗门加入"}, priority=5, permission=GROUP, block=True)
sect_rename = on_command("宗门改名", priority=5, permission=GROUP, block=True)
gm_sect_rename = on_command("超管宗门改名", priority=12, permission=SUPERUSER, block=True)
gm_root_rename = on_command("超管灵根改名", priority=12, permission=SUPERUSER, block=True)
gm_sect_materials = on_command("发放宗门资材", priority=12, permission=SUPERUSER, block=True)


@gm_root_rename.handle(parameterless=[Cooldown(stamina_cost=0)])
async def gm_root_rename_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    arg_str = args.extract_plain_text()
    strs = get_strs_from_str(arg_str)
    num = get_num_from_str(arg_str)
    sect_id = int(num[0]) if num else None
    update_sect_name = strs[0] if strs else None
    if not update_sect_name:
        msg = '请输入要更改的灵根名称'
        await bot.send(event, msg)
        await gm_root_rename.finish()
    if not sect_id:
        msg = '请输入要更改的玩家ID'
        await bot.send(event, msg)
        await gm_root_rename.finish()
    await sql_message.gm_update_root_name(sect_id, update_sect_name)
    msg = f'ID为:{sect_id}的道友, 灵根名称已更改为：{update_sect_name}'
    await bot.send(event, msg)
    await gm_root_rename.finish()


@gm_sect_materials.handle(parameterless=[Cooldown(stamina_cost=0)])
async def gm_sect_materials_(bot: Bot, event: GroupMessageEvent):
    msg = f"开始发放宗门资材"
    await bot.send(event, msg)
    start_time = time.time()
    all_sects = await sql_message.get_all_sects_id_scale()
    all_sects_id = [(sect_per['sect_id'],) for sect_per in all_sects]
    await sql_message.daily_update_sect_materials(all_sects_id)
    end_time = time.time()
    use_time = (end_time - start_time) * 1000
    msg = f"已更新所有宗门的资材, 耗时: {use_time} ms"
    await bot.send(event, msg)
    await gm_sect_materials.finish()


@gm_sect_rename.handle(parameterless=[Cooldown(stamina_cost=0)])
async def gm_sect_rename_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    arg_str = args.extract_plain_text()
    strs = get_strs_from_str(arg_str)
    num = get_num_from_str(arg_str)
    sect_id = int(num[0]) if num else None
    update_sect_name = strs[0] if strs else None
    if not update_sect_name:
        msg = '请输入要更改的宗门名称'
        await bot.send(event, msg)
        await gm_sect_rename.finish()
    if not sect_id:
        msg = '请输入要更改的宗门ID'
        await bot.send(event, msg)
        await gm_sect_rename.finish()
    await sql_message.update_sect_name(sect_id, update_sect_name)
    msg = f'ID为:{sect_id}的宗门, 名称已更改为：{update_sect_name}'
    await bot.send(event, msg)
    await gm_sect_rename.finish()


@sect_elixir_room_make.handle(parameterless=[Cooldown(stamina_cost=0)])
async def sect_elixir_room_make_(bot: Bot, event: GroupMessageEvent):
    """宗门丹房建设"""

    user_info = await check_user(event)

    sect_id = user_info['sect_id']
    if sect_id:
        sect_position = user_info['sect_position']
        owner_idx = [k for k, v in sect_config_data.items() if v.get("title", "") == "宗主"]
        owner_position = int(owner_idx[0]) if len(owner_idx) == 1 else 0
        if sect_position == owner_position:
            elixir_room_config = config['宗门丹房参数']
            elixir_room_level_up_config = elixir_room_config['elixir_room_level']
            sect_info = await sql_message.get_sect_info(sect_id)
            elixir_room_level = sect_info['elixir_room_level']  # 宗门丹房等级
            if int(elixir_room_level) == len(elixir_room_level_up_config):
                msg = f"宗门丹房等级已经达到最高等级，无法继续建设了！"
                await bot.send(event=event, message=msg)
                await sect_elixir_room_make.finish()
            to_up_level = int(elixir_room_level) + 1
            elixir_room_level_up_sect_scale_cost = elixir_room_level_up_config[str(to_up_level)]['level_up_cost'][
                '建设度']
            elixir_room_level_up_use_stone_cost = elixir_room_level_up_config[str(to_up_level)]['level_up_cost'][
                'stone']
            if elixir_room_level_up_use_stone_cost > int(sect_info['sect_used_stone']):
                msg = f"宗门可用灵石不满足升级条件，当前升级需要消耗宗门灵石：{elixir_room_level_up_use_stone_cost}枚！"
                await bot.send(event=event, message=msg)
                await sect_elixir_room_make.finish()
            elif elixir_room_level_up_sect_scale_cost > int(sect_info['sect_scale']):
                msg = f"宗门建设度不满足升级条件，当前升级需要消耗宗门建设度：{elixir_room_level_up_sect_scale_cost}点！"
                await bot.send(event=event, message=msg)
                await sect_elixir_room_make.finish()
            else:
                msg = f"宗门消耗：{elixir_room_level_up_sect_scale_cost}建设度，{elixir_room_level_up_use_stone_cost}宗门灵石\r"
                msg += f"成功升级宗门丹房，当前丹房为：{elixir_room_level_up_config[str(to_up_level)]['name']}!"
                await sql_message.update_sect_scale_and_used_stone(sect_id,
                                                                   sect_info[
                                                                       'sect_used_stone'] - elixir_room_level_up_use_stone_cost,
                                                                   sect_info[
                                                                       'sect_scale'] - elixir_room_level_up_sect_scale_cost)
                await sql_message.update_sect_elixir_room_level(sect_id, to_up_level)
                await bot.send(event=event, message=msg)
                await sect_elixir_room_make.finish()
        else:
            msg = f"道友不是宗主，无法使用该命令！"
            await bot.send(event=event, message=msg)
            await sect_elixir_room_make.finish()
    else:
        msg = f"道友尚未加入宗门！"
        await bot.send(event=event, message=msg)
        await sect_elixir_room_make.finish()


@sect_elixir_get.handle(parameterless=[Cooldown()])
async def sect_elixir_get_(bot: Bot, event: GroupMessageEvent):
    """宗门丹药领取"""

    user_info = await check_user(event)

    sect_id = user_info['sect_id']
    user_name = user_info['user_name']
    user_id = user_info['user_id']
    await sql_message.update_last_check_info_time(user_id)  # 更新查看修仙信息时间
    if not sect_id:
        msg = f"道友尚未加入宗门！"
        await bot.send(event=event, message=msg)
        await sect_elixir_get.finish()
    sect_position = user_info['sect_position']
    elixir_room_config = config['宗门丹房参数']
    if sect_position == 4:
        msg = f"""道友所在宗门的职位为：{sect_config_data[f"{sect_position}"]['title']}，不满足领取要求!"""
        await bot.send(event=event, message=msg)
        await sect_elixir_get.finish()
    sect_info = await sql_message.get_sect_info(sect_id)
    if int(sect_info['elixir_room_level']) == 0:
        msg = f"道友的宗门目前还未建设丹房！"
        await bot.send(event=event, message=msg)
        await sect_elixir_get.finish()
    if int(user_info['sect_contribution']) < elixir_room_config['领取贡献度要求']:
        msg = f"道友的宗门贡献度不满足领取条件，当前宗门贡献度要求：{elixir_room_config['领取贡献度要求']}点！"
        await bot.send(event=event, message=msg)
        await sect_elixir_get.finish()
    elixir_room_level_up_config = elixir_room_config['elixir_room_level']
    elixir_room_cost = elixir_room_level_up_config[str(sect_info['elixir_room_level'])]['level_up_cost'][
        '建设度']
    if sect_info['sect_materials'] < elixir_room_cost:
        msg = f"当前宗门资材无法维护丹房，请等待{config['发放宗门资材']['时间']}点发放宗门资材后尝试领取！"
        await bot.send(event=event, message=msg)
        await sect_elixir_get.finish()
    if int(user_info['sect_elixir_get']) == 1:
        msg = f"道友已经领取过了，不要贪心哦~"
        await bot.send(event=event, message=msg)
        await sect_elixir_get.finish()
    if int(sect_info['elixir_room_level']) == 1:
        msg = f"道友成功领取到丹药:渡厄丹！"
        await sql_message.send_back(user_info['user_id'], 1999, "渡厄丹", "丹药", 1, 1)  # 1级丹房送1个渡厄丹
        await sql_message.update_user_sect_elixir_get_num(user_info['user_id'])
        await bot.send(event=event, message=msg)
        await sect_elixir_get.finish()
    sect_now_room_config = elixir_room_level_up_config[str(sect_info['elixir_room_level'])]
    give_num = sect_now_room_config['give_level']['give_num'] - 1
    rank_up = sect_now_room_config['give_level']['rank_up']
    give_dict = {}
    give_elixir_id_list = items.get_random_id_list_by_rank_and_item_type(
        final_rank=convert_rank(user_info['level'])[0] + rank_up, item_type=['丹药'])
    if not give_elixir_id_list:  # 没有合适的ID，全部给渡厄丹
        msg = f"道友成功领取到丹药：渡厄丹 2 枚！"
        await sql_message.send_back(user_info['user_id'], 1999, "渡厄丹", "丹药", 2, 1)  # 送1个渡厄丹
        await sql_message.update_user_sect_elixir_get_num(user_info['user_id'])
        await bot.send(event=event, message=msg)
        await sect_elixir_get.finish()
    i = 1
    while i <= give_num:
        elixir_id = int(random.choice(give_elixir_id_list))
        if elixir_id == 1999:  # 不给渡厄丹
            continue
        else:
            try:
                give_dict[elixir_id] += 1
                i += 1
            except:
                give_dict[elixir_id] = 1
                i += 1
    msg = f"渡厄丹 1 枚!\r"
    await sql_message.send_back(user_info['user_id'], 1999, "渡厄丹", "丹药", 1, 1)  # 送1个渡厄丹
    for k, v in give_dict.items():
        goods_info = items.get_data_by_item_id(k)
        msg += f"{goods_info['name']} {v} 枚!\r"
    msg = simple_md(f"{user_name}道友成功",
                    "领取", "宗门丹药领取",
                    "到丹药:\r" + msg)
    await sql_message.send_item(user_id, give_dict, 1)
    await sql_message.update_user_sect_elixir_get_num(user_info['user_id'])
    await bot.send(event=event, message=msg)
    await sect_elixir_get.finish()


@sect_buff_info.handle(parameterless=[Cooldown()])
async def sect_buff_info_(bot: Bot, event: GroupMessageEvent):
    """宗门功法查看"""

    user_info = await check_user(event)

    sect_id = user_info['sect_id']
    if sect_id:
        sect_info = await sql_message.get_sect_info(sect_id)
        if sect_info['mainbuff'] == 0 and sect_info['secbuff'] == 0:
            msg = f"本宗尚未获得任何功法、神通，请宗主发送宗门功法、神通搜寻来获得！"
            await bot.send(event=event, message=msg)
            await sect_buff_info.finish()
        msg = ""
        if sect_info['mainbuff'] != 0:
            mainbufflist = await get_sect_mainbuff_id_list(sect_id)
            main_msg = f"\r☆------宗门功法------☆\r"
            msg += main_msg
            for main in mainbufflist:
                if main:
                    mainbuff, mainbuffmsg = get_main_info_msg(str(main))
                    mainmsg = f"{mainbuff['level']}:{mainbuffmsg}\r"
                    msg += mainmsg
        if sect_info['secbuff'] != 0:
            secbufflist = await get_sect_secbuff_id_list(sect_id)
            sec_msg = f"☆------宗门神通------☆\r"
            msg += sec_msg
            for sec in secbufflist:
                secbuff = items.get_data_by_item_id(sec)
                secbuffmsg = get_sec_msg(secbuff)
                secmsg = f"{secbuff['level']}:{secbuff['name']} {secbuffmsg}\r"
                msg += secmsg
        msg = main_md("道友的宗门功法", msg,
                      "宗门神通学习", "宗门神通学习",
                      "宗门任务", "宗门任务接取",
                      "宗门信息", "我的宗门",
                      "宗门功法学习", "宗门功法学习",
                      )
        await bot.send(event=event, message=msg)
        await sect_buff_info.finish()
    else:
        msg = f"道友尚未加入宗门！"
        await bot.send(event=event, message=msg)
        await sect_buff_info.finish()


@sect_mainbuff_learn.handle(parameterless=[Cooldown(cd_time=10, stamina_cost=0)])
async def sect_mainbuff_learn_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """学习宗门功法"""

    user_info = await check_user(event)

    msg = args.extract_plain_text()
    msg = get_strs_from_str(msg)
    if msg:
        msg = msg[0]
        pass
    else:
        msg = "输入功法名称错误！！！"
    sect_id = user_info['sect_id']
    if sect_id:
        sect_position = user_info['sect_position']
        if sect_position > SectPosition.own_disciple.value:
            msg = f"""道友所在宗门的职位为：{sect_config_data[f"{sect_position}"]["title"]}，不满足学习要求!"""
            await bot.send(event=event, message=msg)
            await sect_mainbuff_learn.finish()
        else:
            sect_info = await sql_message.get_sect_info(sect_id)
            if sect_info['mainbuff'] == 0:
                msg = f"本宗尚未获得宗门功法，请宗主发送宗门功法搜寻来获得宗门功法！"
                await bot.send(event=event, message=msg)
                await sect_mainbuff_learn.finish()

            sectmainbuffidlist = await get_sect_mainbuff_id_list(sect_id)

            if msg not in get_mainname_list(sectmainbuffidlist):
                msg = f"本宗还没有该功法，请发送本宗有的功法进行学习！"
                await bot.send(event=event, message=msg)
                await sect_mainbuff_learn.finish()

            userbuffinfo = await UserBuffDate(user_info['user_id']).buff_info
            mainbuffid = get_mainnameid(msg, sectmainbuffidlist)
            if str(userbuffinfo['main_buff']) == str(mainbuffid):
                msg = f"道友请勿重复学习！"
                await bot.send(event=event, message=msg)
                await sect_mainbuff_learn.finish()

            mainbuffconfig = config['宗门主功法参数']
            mainbuff = items.get_data_by_item_id(mainbuffid)
            mainbufftype = mainbuff['level']
            mainbuffgear = buffrankkey[mainbufftype]
            # 获取逻辑
            materialscost = mainbuffgear * mainbuffconfig['学习资材消耗']
            if sect_info['sect_materials'] >= materialscost:
                await sql_message.update_sect_materials(sect_id, materialscost, 2)
                await sql_message.updata_user_main_buff(user_info['user_id'], mainbuffid)
                mainbuff, mainbuffmsg = get_main_info_msg(str(mainbuffid))
                msg = f"本次学习消耗{materialscost}宗门资材，成功学习到本宗{mainbufftype}功法：{mainbuff['name']}\r{mainbuffmsg}"
                await bot.send(event=event, message=msg)
                await sect_mainbuff_learn.finish()
            else:
                msg = f"本次学习需要消耗{materialscost}宗门资材，不满足条件！"
                await bot.send(event=event, message=msg)
                await sect_mainbuff_learn.finish()
    else:
        msg = f"道友尚未加入宗门！"
        await bot.send(event=event, message=msg)
        await sect_mainbuff_learn.finish()


@sect_mainbuff_get.handle(parameterless=[Cooldown(stamina_cost=0)])
async def sect_mainbuff_get_(bot: Bot, event: GroupMessageEvent):
    """搜寻宗门功法"""

    user_info = await check_user(event)

    sect_id = user_info['sect_id']

    # 判断是否加入宗门
    if not sect_id:
        msg = f"道友尚未加入宗门！"
        await bot.send(event=event, message=msg)
        await sect_mainbuff_get.finish()

    sect_position = user_info['sect_position']
    owner_idx = [k for k, v in sect_config_data.items() if v.get("title", "") == "宗主"]
    owner_position = int(owner_idx[0]) if len(owner_idx) == 1 else 0
    # 判断是否为宗主
    if sect_position != owner_position:
        msg = f"道友不是宗主，无法使用该命令！"
        await bot.send(event=event, message=msg)
        await sect_mainbuff_get.finish()
    mainbuffconfig = config['宗门主功法参数']
    sect_info = await sql_message.get_sect_info(sect_id)
    mainbuffgear, mainbufftype = get_sectbufftxt(sect_info['sect_scale'], mainbuffconfig)
    stonecost = mainbuffgear * mainbuffconfig['获取消耗的灵石']
    materialscost = mainbuffgear * mainbuffconfig['获取消耗的资材']
    total_stone_cost = stonecost
    total_materials_cost = materialscost

    if sect_info['sect_used_stone'] < total_stone_cost or sect_info['sect_materials'] < total_materials_cost:
        msg = f"需要消耗{total_stone_cost}宗门灵石，{total_materials_cost}宗门资材，不满足条件！"
        await bot.send(event=event, message=msg)
        await sect_mainbuff_get.finish()
    success_count = 0
    fail_count = 0
    repeat_count = 0
    mainbuffidlist = await get_sect_mainbuff_id_list(sect_id)
    results = []

    for i in range(10):
        if random.randint(0, 100) <= mainbuffconfig['获取到功法的概率']:
            main_buff_id = int(random.choice(skill_rate_set[mainbufftype]['gf_list']))
            if main_buff_id in mainbuffidlist:
                mainbuff, mainbuffmsg = get_main_info_msg(main_buff_id)
                repeat_count += 1
                results.append(f"第{i + 1}次获取到重复功法：{mainbuff['name']}")
            else:
                mainbuffidlist.append(main_buff_id)
                mainbuff, mainbuffmsg = get_main_info_msg(main_buff_id)
                success_count += 1
                results.append(f"第{i + 1}次获取到{mainbufftype}功法：{mainbuff['name']}\r")
        else:
            fail_count += 1

    await sql_message.update_sect_materials(sect_id, total_materials_cost, 2)
    await sql_message.update_sect_scale_and_used_stone(sect_id,
                                                       sect_info['sect_used_stone'] - total_stone_cost,
                                                       sect_info['sect_scale'])
    sql = set_sect_list(mainbuffidlist)
    await sql_message.update_sect_mainbuff(sect_id, sql)

    msg = f"共消耗{total_stone_cost}宗门灵石，{total_materials_cost}宗门资材。\r"
    msg += f"失败{fail_count}次，获取重复功法{repeat_count}次"
    if success_count > 0:
        msg += f"，搜寻到新功法{success_count}次。\r"
    else:
        msg += f"，未搜寻到新功法！\r"
    msg += f"\r".join(results)

    await bot.send(event=event, message=msg)
    await sect_mainbuff_get.finish()


@sect_secbuff_get.handle(parameterless=[Cooldown(stamina_cost=0)])
async def sect_secbuff_get_(bot: Bot, event: GroupMessageEvent):
    """搜寻宗门神通"""

    user_info = await check_user(event)

    sect_id = user_info['sect_id']
    if sect_id:
        sect_position = user_info['sect_position']
        owner_idx = [k for k, v in sect_config_data.items() if v.get("title", "") == "宗主"]
        owner_position = int(owner_idx[0]) if len(owner_idx) == 1 else 0
        if sect_position == owner_position:
            secbuffconfig = config['宗门神通参数']
            sect_info = await sql_message.get_sect_info(sect_id)
            secbuffgear, secbufftype = get_sectbufftxt(sect_info['sect_scale'], secbuffconfig)
            stonecost = secbuffgear * secbuffconfig['获取消耗的灵石']
            materialscost = secbuffgear * secbuffconfig['获取消耗的资材']
            total_stone_cost = stonecost
            total_materials_cost = materialscost

            if sect_info['sect_used_stone'] >= total_stone_cost and sect_info['sect_materials'] >= total_materials_cost:
                success_count = 0
                fail_count = 0
                repeat_count = 0
                secbuffidlist = await get_sect_secbuff_id_list(sect_id)
                results = []

                for i in range(10):
                    if random.randint(0, 100) <= secbuffconfig['获取到神通的概率']:
                        sec_buff_id = int(random.choice(skill_rate_set[secbufftype]['st_list']))
                        if sec_buff_id in secbuffidlist:
                            secbuff = items.get_data_by_item_id(sec_buff_id)
                            repeat_count += 1
                            results.append(f"第{i + 1}次获取到重复神通：{secbuff['name']}")
                        else:
                            secbuffidlist.append(sec_buff_id)
                            secbuff = items.get_data_by_item_id(sec_buff_id)
                            success_count += 1
                            results.append(f"第{i + 1}次获取到{secbufftype}神通：{secbuff['name']}\r")
                    else:
                        fail_count += 1

                await sql_message.update_sect_materials(sect_id, total_materials_cost, 2)
                await sql_message.update_sect_scale_and_used_stone(sect_id,
                                                                   sect_info['sect_used_stone'] - total_stone_cost,
                                                                   sect_info['sect_scale'])
                sql = set_sect_list(secbuffidlist)
                await sql_message.update_sect_secbuff(sect_id, sql)

                msg = f"共消耗{total_stone_cost}宗门灵石，{total_materials_cost}宗门资材。\r"
                msg += f"失败{fail_count}次，获取重复神通{repeat_count}次"
                if success_count > 0:
                    msg += f"，搜寻到新神通{success_count}次。\r"
                else:
                    msg += f"，未搜寻到新神通！\r"
                msg += f"\r".join(results)

                await bot.send(event=event, message=msg)
                await sect_secbuff_get.finish()
            else:
                msg = f"需要消耗{total_stone_cost}宗门灵石，{total_materials_cost}宗门资材，不满足条件！"
                await bot.send(event=event, message=msg)
                await sect_secbuff_get.finish()
        else:
            msg = f"道友不是宗主，无法使用该命令！"
            await bot.send(event=event, message=msg)
            await sect_secbuff_get.finish()
    else:
        msg = f"道友尚未加入宗门！"
        await bot.send(event=event, message=msg)
        await sect_secbuff_get.finish()


@sect_secbuff_learn.handle(parameterless=[Cooldown(cd_time=10, stamina_cost=0)])
async def sect_secbuff_learn_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """学习宗门神通"""

    user_info = await check_user(event)

    msg = args.extract_plain_text()
    msg = get_strs_from_str(msg)
    if msg:
        msg = msg[0]
        pass
    else:
        msg = "输入神通名称错误！！！"
    sect_id = user_info['sect_id']
    if sect_id:
        sect_position = user_info['sect_position']
        if sect_position > SectPosition.own_disciple.value:
            msg = f"""道友所在宗门的职位为：{sect_config_data[f"{sect_position}"]['title']}，不满足学习要求!"""
            await bot.send(event=event, message=msg)
            await sect_secbuff_learn.finish()
        else:
            sect_info = await sql_message.get_sect_info(sect_id)
            if sect_info['secbuff'] == 0:
                msg = f"本宗尚未获得宗门神通，请宗主发送宗门神通搜寻来获得宗门神通！"
                await bot.send(event=event, message=msg)
                await sect_secbuff_learn.finish()

            sectsecbuffidlist = await get_sect_secbuff_id_list(sect_id)

            if msg not in get_secname_list(sectsecbuffidlist):
                msg = f"本宗还没有该神通，请发送本宗有的神通进行学习！"

                await bot.send(event=event, message=msg)
                await sect_secbuff_learn.finish()

            userbuffinfo = await UserBuffDate(user_info['user_id']).buff_info
            secbuffid = get_secnameid(msg, sectsecbuffidlist)
            if str(userbuffinfo['sec_buff']) == str(secbuffid):
                msg = f"道友请勿重复学习！"
                await bot.send(event=event, message=msg)
                await sect_secbuff_learn.finish()

            secbuffconfig = config['宗门神通参数']

            secbuff = items.get_data_by_item_id(secbuffid)
            secbufftype = secbuff['level']
            secbuffgear = buffrankkey[secbufftype]
            # 获取逻辑
            materialscost = secbuffgear * secbuffconfig['学习资材消耗']
            if sect_info['sect_materials'] >= materialscost:
                await sql_message.update_sect_materials(sect_id, materialscost, 2)
                await sql_message.updata_user_sec_buff(user_info['user_id'], secbuffid)
                secmsg = get_sec_msg(secbuff)
                msg = f"本次学习消耗{materialscost}宗门资材，成功学习到本宗{secbufftype}神通：{secbuff['name']}\r{secbuff['name']}：{secmsg}"
                await bot.send(event=event, message=msg)
                await sect_secbuff_learn.finish()
            else:
                msg = f"本次学习需要消耗{materialscost}宗门资材，不满足条件！"
                await bot.send(event=event, message=msg)
                await sect_secbuff_learn.finish()
    else:
        msg = f"道友尚未加入宗门！"
        await bot.send(event=event, message=msg)
        await sect_secbuff_learn.finish()


@upatkpractice.handle(parameterless=[Cooldown()])
async def upatkpractice_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """升级攻击修炼"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    sect_id = user_info['sect_id']
    config_max_level = max(int(key) for key in LEVLECOST.keys())
    raw_args = get_num_from_str(args.extract_plain_text())
    if raw_args:
        raw_args = raw_args[0]
    else:
        raw_args = 1
    try:
        level_up_count = int(raw_args)
        level_up_count = min(max(1, level_up_count), config_max_level)
    except ValueError:
        level_up_count = 1
    if sect_id:
        sect_materials = int((await sql_message.get_sect_info(sect_id))['sect_materials'])  # 当前资材
        useratkpractice = int(user_info['atkpractice'])  # 当前等级
        if useratkpractice == 50:
            msg = f"道友的攻击修炼等级已达到最高等级!"
            await bot.send(event=event, message=msg)
            await upatkpractice.finish()

        sect_level = (await get_sect_level(sect_id))[0] if (await get_sect_level(sect_id))[
                                                               0] <= 50 else 50  # 获取当前宗门修炼等级上限，500w建设度1级,上限25级

        sect_position = user_info['sect_position']
        # 确保用户不会尝试升级超过宗门等级的上限
        level_up_count = min(level_up_count, sect_level - useratkpractice)
        if sect_position > SectPosition.own_disciple.value:
            msg = f"""道友所在宗门的职位为：{sect_config_data[f"{sect_position}"]["title"]}，不满足使用资材的条件!"""
            await bot.send(event=event, message=msg)
            await upatkpractice.finish()

        if useratkpractice >= sect_level:
            msg = f"道友的攻击修炼等级已达到当前宗门修炼等级的最高等级：{sect_level}，请捐献灵石提升贡献度吧！"
            await bot.send(event=event, message=msg)
            await upatkpractice.finish()

        total_stone_cost = sum(LEVLECOST[str(useratkpractice + i)] for i in range(level_up_count))
        total_materials_cost = int(total_stone_cost * 10)

        if int(user_info['stone']) < total_stone_cost:
            msg = f"道友的灵石不够，升级到攻击修炼等级 {useratkpractice + level_up_count} 还需 {total_stone_cost - int(user_info['stone'])} 灵石!"
            await bot.send(event=event, message=msg)
            await upatkpractice.finish()

        if sect_materials < total_materials_cost:
            msg = f"道友的所处的宗门资材不足，还需 {total_materials_cost - sect_materials} 资材来升级到攻击修炼等级 {useratkpractice + level_up_count}!"
            await bot.send(event=event, message=msg)
            await upatkpractice.finish()

        await sql_message.update_ls(user_id, total_stone_cost, 2)
        await sql_message.update_sect_materials(sect_id, total_materials_cost, 2)
        await sql_message.update_user_atkpractice(user_id, useratkpractice + level_up_count)
        msg = f"升级成功，道友当前攻击修炼等级：{useratkpractice + level_up_count}，消耗灵石：{total_stone_cost}枚，消耗宗门资材{total_materials_cost}!"
        await bot.send(event=event, message=msg)
        await upatkpractice.finish()
    else:
        msg = f"修炼逆天而行消耗巨大，请加入宗门再进行修炼！"
        await bot.send(event=event, message=msg)
        await upatkpractice.finish()


@sect_task_refresh.handle(parameterless=[Cooldown()])
async def sect_task_refresh_(bot: Bot, event: GroupMessageEvent):
    """刷新宗门任务"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_cmd_lock = UserCmdLock(user_id)
    with user_cmd_lock:
        sect_id = user_info['sect_id']
        if sect_id:
            if isUserTask(user_id):
                create_user_sect_task(user_id)
                msg = f"已刷新，道友当前接取的任务：{userstask[user_id]['任务名称']}\r{userstask[user_id]['任务内容']['desc']}\r请尽快"
                msg = three_md(msg, "完成", "宗门任务完成", "若对宗门任务不满意，可", "刷新", "宗门任务刷新", "！\r查看",
                               "宗门状态", "我的宗门", "。")
                await bot.send(event=event, message=msg)
                await sect_task_refresh.finish()
            else:
                msg = simple_md(f"道友目前还没有宗门任务，请发送指令",
                                "宗门任务接取", "宗门任务接取",
                                "来获取吧")
                await bot.send(event=event, message=msg)
                await sect_task_refresh.finish()

        else:
            msg = simple_md(f"道友还未",
                            "加入", "加入",
                            "一方宗门。")
            await bot.send(event=event, message=msg)
            await sect_task_refresh.finish()


@sect_list.handle(parameterless=[Cooldown()])
async def sect_list_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """宗门列表：当前为返回转发内容"""
    # 这里曾经是风控模块，但是已经不再需要了
    sect_lists_with_members = await sql_message.get_all_sects_with_member_count()

    msg_list = []
    for sect in sect_lists_with_members:
        sect_id, sect_name, sect_scale, user_name, member_count = sect.values()
        msg_list.append(
            f"编号{sect_id}：{sect_name}\r宗主：{user_name}\r宗门建设度：{number_to(sect_scale)}\r成员数：{member_count}")
    if msg_list:
        page = get_num_from_str(args.extract_plain_text())

        items_all = len(msg_list)
        page_all = ((items_all // 12) + 1) if (items_all % 12 != 0) else (items_all // 12)  # 总页数
        if page:
            page = page[0]
            pass
        else:
            page = 1
        page = int(page)
        if page_all < page:
            msg = "没有那么多宗门！！！"
            await bot.send(event=event, message=msg)
            await sect_list.finish()

        item_num = page * 12 - 12
        item_num_end = item_num + 12
        msg_list = msg_list[item_num:item_num_end]
        page_info = f"第{page}/{page_all}页\r——tips——\r可以发送 宗门列表 页数 来查看更多宗门哦"
        msg_list.append(page_info)
        pass
    else:
        msg = "宗门列表当前空空如也！！！"
        await bot.send(event=event, message=msg)
        await sect_list.finish()

    await send_msg_handler(bot, event, '宗门列表', bot.self_id, msg_list)
    await sect_list.finish()


@sect_users.handle(parameterless=[Cooldown()])
async def sect_users_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """查看所在宗门成员信息"""
    # 这里曾经是风控模块，但是已经不再需要了
    msg_list = []
    args = args.extract_plain_text()
    page = get_num_from_str(args)

    user_info = await check_user(event)

    if user_info:
        sect_id = user_info['sect_id']
        if sect_id:
            sect_info = await sql_message.get_sect_info(sect_id)
            userlist = await sql_message.get_all_users_by_sect_id(sect_id)

            page_all = ((len(userlist) // 12) + 1) if (len(userlist) % 12 != 0) else (len(userlist) // 12)  # 总页数

            if page:
                page = page[0]
                pass
            else:
                page = 1
            page = int(page)
            if page_all < page:
                msg = "道友的宗门没有那么多人！！！"
                await bot.send(event=event, message=msg)
                await sect_users.finish()
            user_num = page * 12 - 12
            user_num_end = user_num + 12
            title = f"☆【{sect_info['sect_name']}】的成员信息☆\r"
            userlist = userlist[user_num:user_num_end]
            i = user_num + 1
            for user in userlist:
                week_donate = await limit_handle.get_user_donate_log_data(user['user_id'])
                msg = f"""编号{i}:{user['user_name']},{user['level']}\r宗门职位：{sect_config_data[f"{user['sect_position']}"]['title']}\r宗门贡献度：{number_to(user['sect_contribution'])}|{user['sect_contribution']}\r本周宗门贡献度：{number_to(week_donate)}|{week_donate}\r"""

                msg_list.append(msg)
                i += 1
            msg = f"\r第{page}/{page_all}页"
            msg_list.append(msg)
            text = msg_handler(msg_list)
            msg = main_md(title, text,
                          "查看日常", "日常",
                          "周贡检查", "宗门周贡检查",
                          "移除成员", "踢出宗门",
                          "下一页", f"宗门成员查看 {page + 1}",
                          )
        else:
            msg = simple_md(f"道友还未",
                            "加入", "加入",
                            "一方宗门。")
    else:
        msg = simple_md(f"未曾踏入修仙世界，输入",
                        "踏入仙途", "踏入仙途",
                        "加入我们，看破这世间虚妄!")
    await bot.send(event=event, message=msg)
    await sect_users.finish()


@sect_users_donate_check.handle(parameterless=[Cooldown(cd_time=30)])
async def sect_users_donate_check_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """宗门划水成员审判"""
    # 这里曾经是风控模块，但是已经不再需要了
    msg_list = []
    args = args.extract_plain_text()
    nums = get_num_from_str(args)

    user_info = await check_user(event)

    sect_id = user_info['sect_id']
    if sect_id:
        sect_position = user_info['sect_position']
        if sect_position > SectPosition.elder.value:
            msg = f"""道友所在宗门的职位为：{sect_config_data[f"{sect_position}"]["title"]}，无权审判宗门成员!"""
            await bot.send(event=event, message=msg)
            await sect_users_donate_check.finish()
        sect_info = await sql_message.get_sect_info(sect_id)
        userlist = await sql_message.get_all_users_by_sect_id(sect_id)
        goal_donate = int(nums[0]) if nums else 10000000
        userlist = [user for user in userlist if
                    await limit_handle.get_user_donate_log_data(user['user_id']) < goal_donate]
        page_all = ((len(userlist) // 12) + 1) if (len(userlist) % 12 != 0) else (len(userlist) // 12)  # 总页数
        page = int(nums[1]) if len(nums) > 1 else 1
        if page_all < page:
            msg = "道友的宗门没有那么多摸鱼的成员！！！"
            await bot.send(event=event, message=msg)
            await sect_users_donate_check.finish()
        # 构造表头
        title = f"☆【{sect_info['sect_name']}】本周贡献低于{number_to(goal_donate)}的成员信息☆\r"
        # 页数构造
        user_num = page * 12 - 12
        user_num_end = user_num + 12
        userlist = userlist[user_num:user_num_end]
        i = user_num + 1
        unpassable_user = []
        for user in userlist:
            week_donate = await limit_handle.get_user_donate_log_data(user['user_id'])
            msg = (f"编号{i}:{user['user_name']},{user['level']}\r"
                   f"宗门职位：{sect_config_data[str(user['sect_position'])]['title']}\r"
                   f"宗门贡献度：{number_to(user['sect_contribution'])}|{user['sect_contribution']}\r"
                   f"本周宗门贡献度：{number_to(week_donate)}|{week_donate}\r")
            unpassable_user.append(user)
            msg_list.append(msg)
            i += 1
        msg = f"\r第{page}/{page_all}页\r"
        msg_list.append(msg)
        text = msg_handler(msg_list)
        msg = main_md(title, text,
                      "查看日常", "日常",
                      "全部成员", "宗门成员查看",
                      "移除成员", "踢出宗门",
                      "下一页", f"宗门周贡检查 {goal_donate} {page + 1}",
                      )
    else:
        msg = simple_md(f"道友还未",
                        "加入", "加入",
                        "一方宗门。")
    await bot.send(event=event, message=msg)
    await sect_users_donate_check.finish()


@sect_task.handle(parameterless=[Cooldown()])
async def sect_task_(bot: Bot, event: GroupMessageEvent):
    """获取宗门任务"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_cmd_lock = UserCmdLock(user_id)
    with user_cmd_lock:
        sect_id = user_info['sect_id']
        if sect_id:
            user_now_num = int(user_info['sect_task'])
            if user_now_num >= config["每日宗门任务次上限"]:
                msg = f"道友已完成{user_now_num}次，今日无法再获取宗门任务了！"
                await bot.send(event=event, message=msg)
                await sect_task.finish()

            if isUserTask(user_id):  # 已有任务
                msg = f"道友当前已接取了任务：{userstask[user_id]['任务名称']}\r{userstask[user_id]['任务内容']['desc']}\r请先"
                msg = three_md(msg, "完成", "宗门任务完成", "若宗门任务不满意，可", "刷新", "宗门任务刷新", "！\r查看",
                               "宗门状态", "我的宗门", "。")
                await bot.send(event=event, message=msg)
                await sect_task.finish()

            create_user_sect_task(user_id)
            msg = f"{userstask[user_id]['任务内容']['desc']}\r请尽快"
            msg = three_md(msg, "完成", "宗门任务完成", "若宗门任务不满意，可", "刷新", "宗门任务刷新", "！\r查看",
                           "宗门状态", "我的宗门", "。")
            await bot.send(event=event, message=msg)
            await sect_task.finish()
        else:
            msg = simple_md(f"道友还未",
                            "加入", "加入",
                            "一方宗门。")
            await bot.send(event=event, message=msg)
            await sect_task.finish()


@sect_task_complete.handle(parameterless=[Cooldown()])
async def sect_task_complete_(bot: Bot, event: GroupMessageEvent):
    """完成宗门任务"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_cmd_lock = UserCmdLock(user_id)
    with user_cmd_lock:
        sect_id = user_info['sect_id']
        if sect_id:
            if not isUserTask(user_id):
                msg = f"道友当前没有接取宗门任务，道友浪费了一次出门机会哦！"
                await bot.send(event=event, message=msg)
                await sect_task_complete.finish()

            if userstask[user_id]['任务内容']['type'] == 1:  # type=1：需要扣气血，type=2：需要扣灵石
                costhp = int((user_info['exp'] / 2) * userstask[user_id]['任务内容']['cost'])
                if user_info['hp'] < user_info['exp'] / 10 or costhp >= user_info['hp']:
                    msg = (
                        f"道友兴高采烈的出门做任务，结果状态欠佳，没过两招就力不从心，坚持不住了，"
                        f"道友只好原路返回，浪费了一次出门机会，看你这么可怜，就不扣你任务次数了！"
                    )
                    await bot.send(event=event, message=msg)
                    await sect_task_complete.finish()

                get_exp = int(user_info['exp'] * userstask[user_id]['任务内容']['give'])

                if user_info['sect_position'] is None:
                    max_exp_limit = 4
                else:
                    max_exp_limit = user_info['sect_position']
                max_exp = sect_config_data[str(max_exp_limit)]["max_exp"]
                if get_exp >= max_exp:
                    get_exp = max_exp
                max_exp_next = int((int(await OtherSet().set_closing_type(
                    user_info['level'])) * XiuConfig().closing_exp_upper_limit))  # 获取下个境界需要的修为 * 1.5为闭关上限
                if int(get_exp + user_info['exp']) > max_exp_next:
                    get_exp = 1
                sect_stone = int(userstask[user_id]['任务内容']['sect'])
                await sql_message.update_user_hp_mp(user_id, user_info['hp'] - costhp, user_info['mp'])
                await sql_message.update_exp(user_id, get_exp)
                await sql_message.donate_update(user_info['sect_id'], sect_stone)
                await sql_message.update_sect_materials(sect_id, sect_stone * 10, 1)
                await sql_message.update_user_sect_task(user_id, 1)
                await sql_message.update_user_sect_contribution(user_id,
                                                                user_info['sect_contribution'] + int(sect_stone))
                msg = (f"道友大战一番，气血减少：{number_to(costhp)}|{costhp}\r"
                       f"获得修为：{number_to(get_exp)}|{get_exp}\r"
                       f"所在宗门建设度增加：{number_to(sect_stone)}\r"
                       f"资材增加：{number_to(sect_stone * 10)}\r"
                       f"宗门贡献度增加：{number_to(sect_stone)}|{int(sect_stone)}\r")
                userstask[user_id] = {}
                await limit_handle.update_user_donate_log_data(user_id, msg)
                msg = simple_md(msg, "接取宗门任务", "宗门任务接取", "！")
                await bot.send(event=event, message=msg)
                await sect_task_complete.finish()

            elif userstask[user_id]['任务内容']['type'] == 2:  # type=1：需要扣气血，type=2：需要扣灵石
                costls = userstask[user_id]['任务内容']['cost']

                if costls > int(user_info['stone']):
                    msg = (
                        f"道友兴高采烈的出门做任务，结果发现灵石带少了，当前任务所需灵石：{costls},"
                        f"道友只好原路返回，浪费了一次出门机会，看你这么可怜，就不扣你任务次数了！")
                    await bot.send(event=event, message=msg)
                    await sect_task_complete.finish()

                get_exp = int(user_info['exp'] * userstask[user_id]['任务内容']['give'])

                if user_info['sect_position'] is None:
                    max_exp_limit = 4
                else:
                    max_exp_limit = user_info['sect_position']
                max_exp = sect_config_data[str(max_exp_limit)]["max_exp"]
                if get_exp >= max_exp:
                    get_exp = max_exp
                max_exp_next = int((int(await OtherSet().set_closing_type(
                    user_info['level'])) * XiuConfig().closing_exp_upper_limit))  # 获取下个境界需要的修为 * 1.5为闭关上限
                if int(get_exp + user_info['exp']) > max_exp_next:
                    get_exp = 1
                sect_stone = int(userstask[user_id]['任务内容']['sect'])
                await sql_message.update_ls(user_id, costls, 2)
                await sql_message.update_exp(user_id, get_exp)
                await sql_message.donate_update(user_info['sect_id'], sect_stone)
                await sql_message.update_sect_materials(sect_id, sect_stone * 10, 1)
                await sql_message.update_user_sect_task(user_id, 1)
                await sql_message.update_user_sect_contribution(user_id,
                                                                user_info['sect_contribution'] + int(sect_stone))
                msg = (f"道友为了完成任务购买宝物消耗灵石：{costls}枚\r"
                       f"获得修为：{number_to(get_exp)}|{get_exp}\r"
                       f"所在宗门建设度增加：{sect_stone}\r"
                       f"资材增加：{sect_stone * 10}\r"
                       f"宗门贡献度增加：{int(sect_stone)}\r")
                userstask[user_id] = {}
                await limit_handle.update_user_donate_log_data(user_id, msg)
                msg = simple_md(msg, "接取宗门任务", "宗门任务接取", "！")
                await bot.send(event=event, message=msg)
                await sect_task_complete.finish()
        else:
            msg = simple_md(f"道友还未",
                            "加入", "加入",
                            "一方宗门。")
            await bot.send(event=event, message=msg)
            await sect_task_complete.finish()


@sect_owner_change.handle(parameterless=[Cooldown()])
async def sect_owner_change_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """宗主传位"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    if not user_info['sect_id']:
        msg = simple_md(f"道友还未",
                        "加入", "加入",
                        "一方宗门。")
        await bot.send(event=event, message=msg)
        await sect_owner_change.finish()
    position_this = [k for k, v in sect_config_data.items() if v.get("title", "") == "宗主"]
    owner_position = int(position_this[0]) if len(position_this) == 1 else 0
    if user_info['sect_position'] != owner_position:
        msg = f"只有宗主才能进行传位。"
        await bot.send(event=event, message=msg)
        await sect_owner_change.finish()
    give_qq = await sql_message.get_user_id(args)  # 使用道号获取用户id，代替原at
    if give_qq:
        if give_qq == user_id:
            msg = f"您已是本宗宗主！"
            await bot.send(event=event, message=msg)
            await sect_owner_change.finish()
        else:
            give_user = await sql_message.get_user_info_with_id(give_qq)
            if give_user['sect_id'] == user_info['sect_id']:
                await sql_message.update_usr_sect(give_user['user_id'], give_user['sect_id'], owner_position)
                await sql_message.update_usr_sect(user_info['user_id'], user_info['sect_id'], owner_position + 1)
                sect_info = await sql_message.get_sect_info_by_id(give_user['sect_id'])
                await sql_message.update_sect_owner(give_user['user_id'], sect_info['sect_id'])
                msg = f"传老宗主{user_info['user_name']}法旨，即日起由{give_user['user_name']}继任{sect_info['sect_name']}宗主"
                await bot.send(event=event, message=msg)
                await sect_owner_change.finish()
            else:
                msg = f"{give_user['user_name']}不在你管理的宗门内，请检查。"
                await bot.send(event=event, message=msg)
                await sect_owner_change.finish()
    else:
        msg = f"请按照规范进行操作,ex:宗主传位 道号,将XXX道友(需在自己管理下的宗门)升为宗主，自己则变为宗主下一等职位。"
        await bot.send(event=event, message=msg)
        await sect_owner_change.finish()


@sect_rename.handle(parameterless=[Cooldown(cd_time=XiuConfig().sect_rename_cd * 86400)])
async def sect_rename_(bot: Bot, event: GroupMessageEvent):
    """宗门改名"""

    user_info = await check_user(event)

    if not user_info['sect_id']:
        msg = simple_md(f"道友还未",
                        "加入", "加入",
                        "一方宗门。")
        await bot.send(event=event, message=msg)
        await sect_rename.finish()
    position_this = [k for k, v in sect_config_data.items() if v.get("title", "") == "宗主"]
    owner_position = int(position_this[0]) if len(position_this) == 1 else 0
    if user_info['sect_position'] != owner_position:
        msg = f"只有宗主才能进行改名！"
        await bot.send(event=event, message=msg)
        await sect_rename.finish()
    else:
        sect_id = user_info['sect_id']
        sect_info = await sql_message.get_sect_info(sect_id)
        if sect_info['sect_used_stone'] < XiuConfig().sect_rename_cost:
            msg = f"道友宗门灵石储备不足，还需{number_to(XiuConfig().sect_rename_cost - sect_info['sect_used_stone'])}灵石!"
            await bot.send(event=event, message=msg)
            await sect_rename.finish()
        update_sect_name = get_random_sect_name(1)[0]
        await sql_message.update_sect_name(sect_id, update_sect_name)
        await sql_message.update_sect_used_stone(sect_id, XiuConfig().sect_rename_cost, 2)
        msg = (f"传宗门——{sect_info['sect_name']}\r"
               f"宗主{user_info['user_name']}法旨:\r"
               f"宗门改名为{update_sect_name}！\r"
               f"星斗更迭，法器灵通，神光熠熠。\r"
               f"愿同门共沐神光，共护宗门千世荣光！\r"
               f"青天无云，道韵长存，灵气飘然。\r"
               f"愿同门同心同德，共铸宗门万世辉煌！")
        await bot.send(event=event, message=msg)
        await sect_rename.finish()


@create_sect.handle(parameterless=[Cooldown()])
async def create_sect_(bot: Bot, event: GroupMessageEvent):
    """创建宗门，对灵石、修为等级有要求，且需要当前状态无宗门"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    # 首先判断是否满足创建宗门的三大条件
    level = user_info['level']
    list_level_all = list(level_data.keys())
    if list_level_all.index(level) < list_level_all.index(XiuConfig().sect_min_level):
        msg = f"创建宗门要求:创建者境界最低要求为{XiuConfig().sect_min_level}"

    elif user_info['stone'] < XiuConfig().sect_create_cost:
        msg = f"创建宗门要求:需要创建者拥有灵石{XiuConfig().sect_create_cost}枚"
    elif user_info['sect_id']:
        msg = f"道友已经加入了宗门ID为{user_info['sect_id']}的宗门，无法再创建宗门。"
    else:
        # 获取宗门名称
        sect_name = get_random_sect_name(1)[0]
        await sql_message.create_sect(user_id, sect_name)
        new_sect = await sql_message.get_sect_info_by_qq(user_id)
        owner_idx = [k for k, v in sect_config_data.items() if v.get("title", "") == "宗主"]
        owner_position = int(owner_idx[0]) if len(owner_idx) == 1 else 0
        await sql_message.update_usr_sect(user_id, new_sect['sect_id'], owner_position)
        await sql_message.update_ls(user_id, XiuConfig().sect_create_cost, 2)
        msg = f"恭喜{user_info['user_name']}道友创建宗门——{sect_name}，宗门编号为{new_sect['sect_id']}。为道友贺！为仙道贺！"
    await bot.send(event=event, message=msg)
    await create_sect.finish()


@sect_kick_out.handle(parameterless=[Cooldown()])
async def sect_kick_out_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """踢出宗门"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_cmd_lock = UserCmdLock(user_id)
    with user_cmd_lock:
        if not user_info['sect_id']:
            msg = simple_md(f"道友还未",
                            "加入", "加入",
                            "一方宗门。")
            await bot.send(event=event, message=msg)
            await sect_kick_out.finish()
        give_qq = await sql_message.get_user_id(args.extract_plain_text())  # 使用道号获取用户id，代替原at
        if await sql_message.get_user_info_with_id(give_qq) is None:
            msg = f"修仙界没有此人,请输入正确道号!"
            await bot.send(event=event, message=msg)
            await sect_kick_out.finish()
        if give_qq:
            if give_qq == user_id:
                msg = f"无法对自己的进行踢出操作，试试退出宗门？"
                await bot.send(event=event, message=msg)
                await sect_kick_out.finish()
            else:
                give_user = await sql_message.get_user_info_with_id(give_qq)
                if give_user['sect_id'] == user_info['sect_id']:
                    if user_info['sect_position'] <= SectPosition.elder.value:
                        if give_user['sect_position'] <= user_info['sect_position']:
                            msg = f"""{give_user['user_name']}的宗门职务为{sect_config_data[f"{give_user['sect_position']}"]['title']}，不在你之下，无权操作。"""
                            await bot.send(event=event, message=msg)
                            await sect_kick_out.finish()
                        else:
                            sect_info = await sql_message.get_sect_info_by_id(give_user['sect_id'])
                            await sql_message.update_usr_sect(give_user['user_id'], None, None)
                            await sql_message.update_user_sect_contribution(give_user['user_id'], 0)
                            msg = f"""传{sect_config_data[f"{user_info['sect_position']}"]['title']}{user_info['user_name']}法旨，即日起{give_user['user_name']}被{sect_info['sect_name']}除名"""
                            await bot.send(event=event, message=msg)
                            await sect_kick_out.finish()
                    else:
                        msg = f"""你的宗门职务为{sect_config_data[f"{user_info['sect_position']}"]['title']}，只有长老及以上可执行踢出操作。"""
                        await bot.send(event=event, message=msg)
                        await sect_kick_out.finish()
                else:
                    msg = simple_md(f"{give_user['user_name']}不在你",
                                    "管理的宗门", "我的宗门",
                                    "内，请检查。",
                                    )
                    await bot.send(event=event, message=msg)
                    await sect_kick_out.finish()
        else:
            msg = simple_md(f"请按照规范进行操作,例如:",
                            "踢出宗门", "踢出宗门",
                            " 云依,将云依道友(需在自己管理下的宗门）踢出宗门",
                            )
            await bot.send(event=event, message=msg)
            await sect_kick_out.finish()


@sect_out.handle(parameterless=[Cooldown()])
async def sect_out_(bot: Bot, event: GroupMessageEvent):
    """退出宗门"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_name = user_info['user_name']
    if not user_info['sect_id']:
        msg = simple_md(f"道友还未",
                        "加入", "加入",
                        "一方宗门。")
        await bot.send(event=event, message=msg)
        await sect_out.finish()
    position_this = [k for k, v in sect_config_data.items() if v.get("title", "") == "宗主"]
    owner_position = int(position_this[0]) if len(position_this) == 1 else 0
    sect_out_id = user_info['sect_id']
    if user_info['sect_position'] != owner_position:
        await sql_message.update_usr_sect(user_id, None, None)
        sect_info = await sql_message.get_sect_info_by_id(int(sect_out_id))
        await sql_message.update_user_sect_contribution(user_id, 0)
        msg = simple_md(f"{user_name}道友已",
                        f"退出{sect_info['sect_name']}", "退出宗门",
                        "，今后就是自由散修，是福是祸，犹未可知。",
                        )
        await bot.send(event=event, message=msg)
        await sect_out.finish()
    else:
        msg = simple_md(
            f"宗主无法直接退出宗门，如确有需要，请完成",
            "宗主传位", "宗主传位",
            "后另行尝试。",
            )
        await bot.send(event=event, message=msg)
        await sect_out.finish()


@sect_close.handle(parameterless=[Cooldown()])
async def sect_close_(bot: Bot, event: GroupMessageEvent):
    """关闭宗门"""

    user_info = await check_user(event)
    if not user_info['sect_id']:
        msg = f"道友还未加入一方宗门。"
        await bot.send(event=event, message=msg)
        await sect_close.finish()
    position_this = [k for k, v in sect_config_data.items() if v.get("title", "") == "宗主"]
    owner_position = int(position_this[0]) if len(position_this) == 1 else 0
    sect_id = user_info['sect_id']
    if user_info['sect_position'] != owner_position:
        msg = f"道友无权管理宗门人员流动事宜。"
        await bot.send(event=event, message=msg)
        await sect_close.finish()
    else:
        sect_info = await sql_message.get_sect_info_by_id(int(sect_id))
        sect_state = sect_info['is_open']
        if sect_state:
            await sql_message.set_sect_join_mode(sect_id, False)
            msg = f"宗门关闭加入成功"
        else:
            await sql_message.set_sect_join_mode(sect_id, True)
            msg = f"宗门开放加入成功"
        await bot.send(event=event, message=msg)
        await sect_close.finish()


@sect_donate.handle(parameterless=[Cooldown()])
async def sect_donate_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """宗门捐献"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    if not user_info['sect_id']:
        msg = f"道友还未加入一方宗门。"
        await bot.send(event=event, message=msg)
        await sect_donate.finish()
    msg = args.extract_plain_text().strip()
    donate_num = re.findall(r"\d+", msg)  # 捐献灵石数
    if len(donate_num) > 0:
        if int(donate_num[0]) > user_info['stone']:
            msg = f"道友的灵石数量小于欲捐献数量{int(donate_num[0])}，请检查"
            await bot.send(event=event, message=msg)
            await sect_donate.finish()
        else:
            await sql_message.update_ls(user_id, int(donate_num[0]), 2)
            await sql_message.donate_update(user_info['sect_id'], int(donate_num[0]))
            await sql_message.update_user_sect_contribution(user_id,
                                                            user_info['sect_contribution'] + int(donate_num[0]))
            msg = f"道友捐献灵石{int(donate_num[0])}枚，宗门建设度增加：{int(donate_num[0])}，宗门贡献度增加：{int(donate_num[0])}点，蒸蒸日上！"
            await limit_handle.update_user_donate_log_data(user_id, msg)
            await bot.send(event=event, message=msg)
            await sect_donate.finish()
    else:
        msg = f"捐献的灵石数量解析异常"
        await bot.send(event=event, message=msg)
        await sect_donate.finish()


@sect_position_update.handle(parameterless=[Cooldown()])
async def sect_position_update_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """宗门职位变更"""

    user_info = await check_user(event)

    user_id = user_info['user_id']

    if user_info['sect_position'] > SectPosition.elder.value:
        msg = f"""你的宗门职位为{sect_config_data[f"{user_info['sect_position']}"]['title']}，无权进行职位管理！"""
        await bot.send(event=event, message=msg)
        await sect_position_update.finish()
    msg = args.extract_plain_text()
    position_num = re.findall(r"\d+", msg)

    give_qq = await get_id_from_str(msg)  # 使用道号获取用户id，代替原at
    if give_qq:
        if give_qq == user_id:
            msg = f"无法对自己的职位进行管理。"
            await bot.send(event=event, message=msg)
            await sect_position_update.finish()
        else:
            if len(position_num) > 0 and position_num[0] in list(sect_config_data.keys()):
                give_user = await sql_message.get_user_info_with_id(give_qq)
                if give_user['sect_id'] == user_info['sect_id'] and give_user['sect_position'] > user_info[
                    'sect_position']:
                    if int(position_num[0]) > user_info['sect_position']:
                        await sql_message.update_usr_sect(give_user['user_id'], give_user['sect_id'],
                                                          int(position_num[0]))
                        msg = f"""传{sect_config_data[f"{user_info['sect_position']}"]['title']}{user_info['user_name']}法旨:即日起{give_user['user_name']}为本宗{sect_config_data[f"{int(position_num[0])}"]['title']}"""
                        if XiuConfig().img:
                            pic = await get_msg_pic(f"@{event.sender.nickname}\r" + msg)
                            await bot.send(event=event, message=MessageSegment.image(pic))
                        else:
                            await bot.send(event=event, message=msg)
                        await sect_position_update.finish()
                    else:
                        msg = f"道友试图变更的职位品阶必须在你品阶之下"
                        if XiuConfig().img:
                            pic = await get_msg_pic(f"@{event.sender.nickname}\r" + msg)
                            await bot.send(event=event, message=MessageSegment.image(pic))
                        else:
                            await bot.send(event=event, message=msg)
                        await sect_position_update.finish()
                else:
                    msg = f"请确保变更目标道友与你在同一宗门，且职位品阶在你之下。"
                    await bot.send(event=event, message=msg)
                    await sect_position_update.finish()
            else:
                msg = f"职位品阶数字解析异常，请输入宗门职位变更帮助，查看支持的数字解析配置"
                await bot.send(event=event, message=msg)
                await sect_position_update.finish()
    else:
        msg = f"""请按照规范进行操作,ex:宗门职位变更2XXX,将XXX道友(需在自己管理下的宗门)的变更为{sect_config_data.get('2', {'title': '没有找到2品阶'})['title']}"""
        await bot.send(event=event, message=msg)
        await sect_position_update.finish()


@join_sect.handle(parameterless=[Cooldown()])
async def join_sect_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """加入宗门,后跟宗门ID,要求加入者当前状态无宗门,入门默认为外门弟子"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    if not user_info['sect_id']:
        sect_no = get_num_from_str(args.extract_plain_text())
        if sect_no:
            sect_no = int(sect_no[0])
        else:
            sect_no = None
        sects_all = await sql_message.get_all_sect_id()
        if sect_no:
            if sect_no not in sects_all:
                msg = f"申请加入的宗门编号似乎有误，未在宗门名录上发现!"
            else:
                new_sect = await sql_message.get_sect_info_by_id(sect_no)
                userlist = await sql_message.get_all_users_by_sect_id(sect_no)
                max_sect_num = new_sect['elixir_room_level'] * 16 + 52
                sect_num = len(userlist)
                if not new_sect['is_open']:
                    msg = f"目标宗门未开放加入！！"
                    await bot.send(event=event, message=msg)
                    await join_sect.finish()
                if sect_num < max_sect_num:
                    owner_idx = [k for k, v in sect_config_data.items() if v.get("title", "") == "外门弟子"]
                    owner_position = int(owner_idx[0]) if len(owner_idx) == 1 else 4
                    await sql_message.update_usr_sect(user_id, sect_no, owner_position)
                    msg = f"欢迎{user_info['user_name']}师弟入我{new_sect['sect_name']}，共参天道。\r宗门当前人数：{sect_num + 1}/{max_sect_num}"
                else:
                    msg = f"道友欲加入的宗门太过火爆啦，换个宗门吧！！\r{new_sect['sect_name']}当前人数：{sect_num}/{max_sect_num}"
        else:
            msg = f"申请加入的宗门编号解析异常，应全为数字!"
    else:
        msg = f"守山弟子：我观道友气运中已有宗门气运加持，又何必与我为难。"
    await bot.send(event=event, message=msg)
    await join_sect.finish()


# edited:zyp981204
@my_sect.handle(parameterless=[Cooldown()])
async def my_sect_(bot: Bot, event: GroupMessageEvent):
    """我的宗门"""

    user_info = await check_user(event)

    elixir_room_level_up_config = config['宗门丹房参数']['elixir_room_level']
    sect_id = user_info['sect_id']
    sect_position = user_info['sect_position']
    user_name = user_info['user_name']
    sect_info = await sql_message.get_sect_info(sect_id)
    owner_idx = [k for k, v in sect_config_data.items() if v.get("title", "") == "宗主"]
    week_donate = await limit_handle.get_user_donate_log_data(user_info['user_id'])
    owner_position = int(owner_idx[0]) if len(owner_idx) == 1 else 0
    if sect_id:
        sql_res = await sql_message.scale_top()
        top_idx_list = [_['sect_id'] for _ in sql_res]
        if not sect_info['elixir_room_level']:
            elixir_room_name = "暂无"
        else:
            elixir_room_name = elixir_room_level_up_config[str(sect_info['elixir_room_level'])]['name']
        msg = f"""
{user_name}所在宗门
宗门名讳：{sect_info['sect_name']}
宗门编号：{sect_id}
宗   主：{(await sql_message.get_user_info_with_id(sect_info['sect_owner']))['user_name']}
道友职位：{sect_config_data[f"{sect_position}"]['title']}
宗门建设度：{number_to(sect_info['sect_scale'])}
洞天福地：{sect_info['sect_fairyland'] if sect_info['sect_fairyland'] else "暂无"}
宗门位面排名：{top_idx_list.index(sect_id) + 1}
宗门拥有资材：{number_to(sect_info['sect_materials'])}
宗门贡献度：{number_to(user_info['sect_contribution'])}(本周:{number_to(week_donate)})
宗门丹房：{elixir_room_name}
"""
        if sect_position == owner_position:
            msg += f"\r宗门储备：{sect_info['sect_used_stone']}灵石"
    else:
        msg = f"一介散修，莫要再问。"

    await bot.send(event=event, message=msg)
    await my_sect.finish()


def create_user_sect_task(user_id):
    tasklist = config["宗门任务"]
    # 反正我做了
    task_pro = ["仗义疏财", "九转仙丹", "查抄窝点", "狩猎邪修", "红尘寻宝", "狩猎邪修", "红尘寻宝", "狩猎邪修",
                "红尘寻宝",
                "狩猎邪修", "红尘寻宝", "狩猎邪修", "红尘寻宝", "狩猎邪修", "红尘寻宝", "狩猎邪修", "红尘寻宝",
                "狩猎邪修",
                "红尘寻宝", "狩猎邪修", "红尘寻宝", "狩猎邪修", "红尘寻宝"]
    random_task = random.choice(task_pro)
    key = random_task  # random.choices(list(tasklist))[0]
    userstask[user_id]['任务名称'] = key
    userstask[user_id]['任务内容'] = tasklist[key]


def isUserTask(user_id):
    """判断用户是否已有任务 True:有任务"""
    Flag = False
    try:
        userstask[user_id]
    except:
        userstask[user_id] = {}

    if userstask[user_id] != {}:
        Flag = True

    return Flag


async def get_sect_mainbuff_id_list(sect_id):
    """获取宗门功法id列表"""
    sect_info = await sql_message.get_sect_info(sect_id)
    main_buff_data = sect_info['mainbuff']
    if not main_buff_data or main_buff_data == '0':
        return []
    mainbufflist = json.loads(main_buff_data)
    return mainbufflist


async def get_sect_secbuff_id_list(sect_id):
    """获取宗门神通id列表"""
    sect_info = await sql_message.get_sect_info(sect_id)
    sec_buff_buff_data = sect_info['secbuff']
    if not sec_buff_buff_data or sec_buff_buff_data == '0':
        return []
    secbufflist = json.loads(sec_buff_buff_data)
    return secbufflist


def set_sect_list(bufflist):
    """传入ID列表,返回[ID列表]"""
    return json.dumps(bufflist)


def get_mainname_list(bufflist):
    """根据传入的功法列表，返回功法名字列表"""
    namelist = []
    for buff in bufflist:
        mainbuff = items.get_data_by_item_id(buff)
        namelist.append(mainbuff['name'])
    return namelist


def get_secname_list(bufflist):
    """根据传入的神通列表，返回神通名字列表"""
    namelist = []
    for buff in bufflist:
        secbuff = items.get_data_by_item_id(buff)
        namelist.append(secbuff['name'])
    return namelist


def get_mainnameid(buffname, bufflist):
    """根据传入的功法名字,获取到功法的id"""
    tempdict = {}
    buffid = 0
    for buff in bufflist:
        mainbuff = items.get_data_by_item_id(buff)
        tempdict[mainbuff['name']] = buff
    for k, v in tempdict.items():
        if buffname == k:
            buffid = v
    return buffid


def get_secnameid(buffname, bufflist):
    tempdict = {}
    buffid = 0
    for buff in bufflist:
        secbuff = items.get_data_by_item_id(buff)
        tempdict[secbuff['name']] = buff
    for k, v in tempdict.items():
        if buffname == k:
            buffid = v
    return buffid


def get_sectbufftxt(sect_scale, config_):
    """
    获取宗门当前获取功法的品阶 档位 + 3
    参数:sect_scale=宗门建设度
    config=宗门主功法参数
    """
    bufftxt = {1: '后天品级', 2: '后天品级', 3: '先天品级', 4: '先天品级', 5: '神丹品级', 6: '神丹品级', 7: '虚劫品级',
               8: '虚劫品级', 9: '生死品级', 10: '神海品级', 11: '神劫品级', 12: '神极品级', 13: '神变品级',
               14: '界主品级', 15: '天尊品级'}
    buffgear = divmod(sect_scale, config_['建设度'])[0]
    if buffgear >= 10:
        if buffgear >= 10000:
            buffgear = 15
        elif buffgear >= 1000:
            buffgear = 14
        elif buffgear >= 800:
            buffgear = 13
        elif buffgear >= 600:
            buffgear = 12
        elif buffgear >= 400:
            buffgear = 11
        else:
            buffgear = 10
    elif buffgear <= 1:
        buffgear = 1
    else:
        pass
    return buffgear, bufftxt[buffgear]


async def get_sect_level(sect_id):
    sect = await sql_message.get_sect_info(sect_id)
    return divmod(sect['sect_scale'], config["等级建设度"])
