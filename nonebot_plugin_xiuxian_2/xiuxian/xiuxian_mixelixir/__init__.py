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
from nonebot.params import EventPlainText, CommandArg, RawCommand
from nonebot.permission import SUPERUSER

from .mix_elixir_config import MIXELIXIRCONFIG
from .mixelixirutil import get_mix_elixir_msg, tiaohe, check_mix, make_dict
from ..xiuxian_back.back_util import get_user_elixir_back_msg, get_user_yaocai_back_msg, get_user_yaocai_back_msg_easy
from ..xiuxian_config import convert_rank
from ..xiuxian_utils.clean_utils import get_strs_from_str, get_args_num, get_paged_msg
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import (
    check_user, send_msg_handler,
    CommandObjectID
)
from ..xiuxian_utils.xiuxian2_handle import (
    sql_message, get_player_info, save_player_info,
    UserBuffDate, xiuxian_impart
)

cache_help = {}

mix_elixir = on_fullmatch("炼丹", priority=17, permission=GROUP, block=True)
mix_make = on_command("配方", priority=5, permission=GROUP, block=True)
elixir_help = on_fullmatch("炼丹帮助", priority=7, permission=GROUP, block=True)
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
指令：
1、炼丹:会检测背包内的药材,自动生成配方【一次最多匹配25种药材】
2、配方:发送配方领取丹药【配方主药.....】
3、炼丹帮助:获取本帮助信息
4、丹药背包:获取背包内丹药以及炼丹炉信息
5、药材背包:获取背包内药材信息
6、炼丹配方帮助:获取炼丹配方帮助
7、灵田收取、灵田结算:收取洞天福地里灵田的药材
8、我的炼丹信息:查询自己的炼丹信息
9、升级收取等级:每一个等级会增加灵田收取的数量
10、升级丹药控火:每一个等级会增加炼丹的产出数量
"""

__mix_elixir_help__ = f"""
炼丹配方信息
1、炼丹需要主药、药引、辅药
2、主药和药引控制炼丹时的冷热调和,冷热失和则炼不出丹药
3、草药的类型控制产出丹药的类型
"""


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
        await sql_message.send_back(user_info['user_id'], 3001, '恒心草', '药材', num)  # 没有合适的，保底
        msg += f"恒心草 {num} 个！\r"
    else:
        give_dict = {}
        while num := num - 1:
            item_id = random.choice(yaocai_id_list)
            try:
                give_dict[item_id] += 1
            except LookupError:
                give_dict[item_id] = 1
        for k, v in give_dict.items():
            goods_info = items.get_data_by_item_id(k)
            msg += f"{goods_info['name']} {v} 个！\r"
            await sql_message.send_back(user_info['user_id'], k, goods_info['name'], '药材', v)
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
                    id = random.choice(yaocai_id_list)
                    try:
                        give_dict[id] += 1
                        i += 1
                    except LookupError:
                        give_dict[id] = 1
                        i += 1
                for k, v in give_dict.items():
                    goods_info = items.get_data_by_item_id(k)
                    msg += f"{goods_info['name']} {v} 个！\r"
                    await sql_message.send_back(user_info['user_id'], k, goods_info['name'], '药材', v)
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
    l_msg = [f"☆------道友的炼丹信息------☆"]
    msg = f"药材收取等级：{mix_elixir_info['收取等级']}\r"
    msg += f"丹药控火等级：{mix_elixir_info['丹药控火']}\r"
    msg += f"丹药耐药性等级：{mix_elixir_info['丹药耐药性']}\r"
    msg += f"炼丹经验：{mix_elixir_info['炼丹经验']}\r"
    l_msg.append(msg)
    if mix_elixir_info['炼丹记录'] != {}:
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


@mix_elixir.handle(parameterless=[Cooldown(cd_time=30, at_sender=False)])
async def mix_elixir_(bot: Bot, event: GroupMessageEvent):
    global user_ldl_dict, user_ldl_flag

    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    user_back = await sql_message.get_back_msg(user_id)
    yaocai_dict = {}
    user_ldl_flag[user_id] = False  # 初始化炼丹炉标志
    for back in user_back:
        if back['goods_type'] == "药材":
            yaocai_dict[back['goods_id']] = items.get_data_by_item_id(back['goods_id'])
            yaocai_dict[back['goods_id']]['num'] = back['goods_num']
        elif back['goods_type'] == "炼丹炉":
            if user_id not in user_ldl_dict:
                user_ldl_dict[user_id] = {}
            user_ldl_dict[user_id][back['goods_id']] = back['goods_name']
            user_ldl_flag[user_id] = True

    if user_back is None:
        msg = "道友的背包空空如也，无法炼丹"
        await bot.send(event=event, message=msg)
        await mix_elixir.finish()

    if yaocai_dict == {}:
        msg = "道友的背包内没有药材，无法炼丹！"
        await bot.send(event=event, message=msg)
        await mix_elixir.finish()

    if not user_ldl_flag[user_id]:
        msg = "道友背包内没有炼丹炉，无法炼丹！"
        await bot.send(event=event, message=msg)
        await mix_elixir.finish()

    msg = "正在生成丹方，请稍候..."
    await bot.send(event=event, message=msg)

    yaocai_dict = await make_dict(yaocai_dict)
    finall_mix_elixir_msg = await get_mix_elixir_msg(yaocai_dict)
    if finall_mix_elixir_msg == {}:
        msg = "系统未检测到丹方，道友背包内的药材不满足！"
        await bot.send(event=event, message=msg)
        await mix_elixir.finish()
    else:
        ldl_name = sorted(user_ldl_dict[user_id].items(), key=lambda x: x[0], reverse=False)[0][1]
        l_msg = []
        for k, v in finall_mix_elixir_msg.items():
            goods_info = items.get_data_by_item_id(v['id'])
            msg = f"名字：{goods_info['name']}\r"
            msg += f"效果：{goods_info['desc']}\r"
            msg += f"配方：{v['配方']['配方简写']}丹炉{ldl_name}\r"
            msg += f"☆------药材清单------☆\r"
            msg += f"主药：{v['配方']['主药']},{v['配方']['主药_level']}，数量：{v['配方']['主药_num']}\r"
            msg += f"药引：{v['配方']['药引']},{v['配方']['药引_level']}，数量：{v['配方']['药引_num']}\r"
            if v['配方']['辅药_num'] != 0:
                msg += f"辅药：{v['配方']['辅药']},{v['配方']['辅药_level']}，数量：{v['配方']['辅药_num']}\r"
            l_msg.append(msg)
        if len(l_msg) > 51:
            l_msg = l_msg[:50]
        await send_msg_handler(bot, event, '配方', bot.self_id, l_msg)
        await mix_elixir.finish()


# 配方
@mix_make.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def mix_elixir_(bot: Bot, event: GroupMessageEvent, mode: str = EventPlainText()):
    """配方"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_id = event.user_id
    pattern = r"主药([\u4e00-\u9fa5]+)(\d+)药引([\u4e00-\u9fa5]+)(\d+)辅药([\u4e00-\u9fa5]+)(\d+)丹炉([\u4e00-\u9fa5]+)+"
    matched = re.search(pattern, mode)
    if matched is None:
        msg = f"请输入正确的配方！"
        await bot.send(event=event, message=msg)
        await mix_make.finish()
    else:
        zhuyao_name = matched.groups()[0]
        zhuyao_num = int(matched.groups()[1])  # 数量一定会有
        check, zhuyao_goods_id = await check_yaocai_name_in_back(user_id, zhuyao_name, zhuyao_num)
        if not check:
            msg = f"请检查药材：{zhuyao_name} 是否在背包中，或者数量是否足够！"
            await bot.send(event=event, message=msg)
            await mix_make.finish()
        yaoyin_name = matched.groups()[2]
        yaoyin_num = int(matched.groups()[3])  # 数量一定会有
        check, yaoyin_goods_id = await check_yaocai_name_in_back(user_id, yaoyin_name, yaoyin_num)
        if not check:
            msg = f"请检查药材：{yaoyin_name} 是否在背包中，或者数量是否足够！"
            await bot.send(event=event, message=msg)
            await mix_make.finish()
        fuyao_name = matched.groups()[4]
        fuyao_num = int(matched.groups()[5])
        check, fuyao_goods_id = await check_yaocai_name_in_back(user_id, fuyao_name, fuyao_num)
        if not check:
            msg = f"请检查药材：{fuyao_name} 是否在背包中，或者数量是否足够！"
            await bot.send(event=event, message=msg)
            await mix_make.finish()
        if zhuyao_name == fuyao_name:
            check, fuyao_goods_id = await check_yaocai_name_in_back(user_id, fuyao_name, fuyao_num + zhuyao_num)
            if not check:
                msg = f"请检查药材：{zhuyao_name} 是否在背包中，或者数量是否足够！"
                await bot.send(event=event, message=msg)
                await mix_make.finish()
        if yaoyin_name == fuyao_name:
            check, fuyao_goods_id = await check_yaocai_name_in_back(user_id, fuyao_name, fuyao_num + yaoyin_num)
            if not check:
                msg = f"请检查药材：{yaoyin_name} 是否在背包中，或者数量是否足够！"
                await bot.send(event=event, message=msg)
                await mix_make.finish()

        ldl_name = matched.groups()[6]
        check, ldl_info = await check_ldl_name_in_back(user_id, ldl_name)
        if not check:
            msg = f"请检查炼丹炉：{ldl_name} 是否在背包中！"
            await bot.send(event=event, message=msg)
            await mix_make.finish()
        # 检测通过
        zhuyao_info = items.get_data_by_item_id(zhuyao_goods_id)
        yaoyin_info = items.get_data_by_item_id(yaoyin_goods_id)
        if await tiaohe(zhuyao_info, zhuyao_num, yaoyin_info, yaoyin_num):  # 调和失败
            msg = f"冷热调和失败！小心炸炉哦~"
            await bot.send(event=event, message=msg)
            await mix_make.finish()
        else:
            elixir_config = {
                str(zhuyao_info['主药']['type']): zhuyao_info['主药']['power'] * zhuyao_num
            }
            fuyao_info = items.get_data_by_item_id(fuyao_goods_id)
            elixir_config[str(fuyao_info['辅药']['type'])] = fuyao_info['辅药']['power'] * fuyao_num
            is_mix, id = await check_mix(elixir_config)
            if is_mix:
                mix_elixir_info = get_player_info(user_id, 'mix_elixir_info')
                goods_info = items.get_data_by_item_id(id)
                # 加入传承
                impart_data = await xiuxian_impart.get_user_info_with_id(user_id)
                impart_mix_per = impart_data['impart_mix_per'] if impart_data is not None else 0
                # 功法炼丹数加成
                main_dan_data = await UserBuffDate(user_id).get_user_main_buff_data()

                if main_dan_data is not None:  # 功法炼丹数量加成
                    main_dan = main_dan_data['dan_buff']
                else:
                    main_dan = 0
                # 功法炼丹经验加成
                main_dan_exp = await UserBuffDate(user_id).get_user_main_buff_data()

                if main_dan_exp is not None:  # 功法炼丹经验加成
                    main_exp = main_dan_exp['dan_exp']
                else:
                    main_exp = 0

                num = 1 + ldl_info['buff'] + mix_elixir_info['丹药控火'] + impart_mix_per + main_dan  # 炼丹数量提升
                msg = f"恭喜道友成功炼成丹药：{goods_info['name']}{num}枚"
                # 背包sql
                await sql_message.send_back(user_id, id, goods_info['name'], "丹药", num)  # 将炼制的丹药加入背包
                await sql_message.update_back_j(user_id, zhuyao_goods_id, zhuyao_num)  # 将消耗的药材从背包中减去
                await sql_message.update_back_j(user_id, fuyao_goods_id, fuyao_num)
                await sql_message.update_back_j(user_id, yaoyin_goods_id, yaoyin_num)
                try:
                    var = mix_elixir_info['炼丹记录'][id]
                    now_num = mix_elixir_info['炼丹记录'][id]['num']  # now_num 已经炼制的丹药数量
                    if now_num >= goods_info['mix_all']:
                        msg += f"该丹药道友已炼制{now_num}次，无法获得炼丹经验了~"
                    elif now_num + num >= goods_info['mix_all']:
                        exp_num = goods_info['mix_all'] - now_num
                        mix_elixir_info['炼丹经验'] += (goods_info['mix_exp'] + main_exp) * exp_num
                        msg += f"获得炼丹经验{goods_info['mix_exp'] * exp_num}点"
                    else:
                        mix_elixir_info['炼丹经验'] += (goods_info['mix_exp'] + main_exp) * num
                        msg += f"获得炼丹经验{(goods_info['mix_exp'] + main_exp) * num}点"
                    mix_elixir_info['炼丹记录'][id]['num'] += num
                except:
                    mix_elixir_info['炼丹记录'][id] = {}
                    mix_elixir_info['炼丹记录'][id]['name'] = goods_info['name']
                    mix_elixir_info['炼丹记录'][id]['num'] = num
                    mix_elixir_info['炼丹经验'] += (goods_info['mix_exp'] + main_exp) * num
                    msg += f"获得炼丹经验{(goods_info['mix_exp'] + main_exp) * num}点"
                save_player_info(user_id, mix_elixir_info, 'mix_elixir_info')
                await bot.send(event=event, message=msg)
                await mix_make.finish()
            else:
                msg = f"没有炼成丹药哦~就不扣你药材啦"
                await bot.send(event=event, message=msg)
                await mix_make.finish()


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
