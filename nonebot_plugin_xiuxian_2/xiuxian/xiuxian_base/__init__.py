import random
import re
from datetime import datetime

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    MessageSegment
)
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from ..xiuxian_buff import check_limit
from ..xiuxian_config import XiuConfig
from ..xiuxian_data.data.灵根_data import root_data
from ..xiuxian_data.data.突破概率_data import break_rate
from ..xiuxian_limit.limit_database import limit_handle
from ..xiuxian_place import place
from ..xiuxian_sect import sect_config
from ..xiuxian_utils.clean_utils import get_num_from_str, get_strs_from_str, main_md, number_to_pro, simple_md
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.other_set import OtherSet
from ..xiuxian_utils.utils import (
    check_user,
    get_msg_pic, number_to,
    send_msg_handler, get_id_from_str, linggen_get, check_user_type
)
from ..xiuxian_utils.xiuxian2_handle import (
    sql_message, UserBuffDate, xiuxian_impart, leave_harm_time
)

# 定时任务
cache_help = {}
cache_level_help = {}

run_xiuxian = on_command("踏入仙途", aliases={"/踏入仙途", "我要修仙"}, priority=8, permission=GROUP, block=True)
restart = on_command("重入仙途", permission=GROUP, priority=7, block=True)
sign_in = on_command("修仙签到", aliases={"/签到"}, priority=13, permission=GROUP, block=True)
rank = on_command("排行榜", aliases={"修仙排行榜", "灵石排行榜", "战力排行榜", "境界排行榜", "宗门排行榜"},
                  priority=7, permission=GROUP, block=True)
rename = on_command("改头换面", aliases={"修仙改名", "改名", "改头", "换面"}, priority=5, permission=GROUP,
                    block=True)
level_up = on_command("突破", aliases={"tp"}, priority=6, permission=GROUP, block=True)
level_up_dr = on_command("渡厄突破", priority=7, permission=GROUP, block=True)
level_up_dr_fast = on_command("快速渡厄突破", priority=7, permission=GROUP, block=True)
level_up_zj = on_command("直接突破", aliases={"破", "/突破"}, priority=2, permission=GROUP, block=True)
level_up_zj_all = on_command("快速突破", aliases={"连续突破", "一键突破"}, priority=2, permission=GROUP, block=True)
give_stone = on_command("送灵石", priority=5, permission=GROUP, block=True)
steal_stone = on_command("借灵石", priority=4, permission=GROUP, block=True)
gm_command = on_command("生成灵石", permission=SUPERUSER, priority=10, block=True)
gm_command_miss = on_command("思恋结晶", permission=SUPERUSER, priority=10, block=True)
gm_command_pray = on_command("祈愿结晶", permission=SUPERUSER, priority=10, block=True)
gmm_command = on_command("灵根更换", permission=SUPERUSER, priority=10, block=True)
cz = on_command('创造', permission=SUPERUSER, priority=15, block=True)
cz_ts = on_command('调试创造', permission=SUPERUSER, priority=15, block=True)
rob_stone = on_command("抢灵石_____", priority=5, permission=GROUP, block=True)
user_leveluprate = on_command('我的突破概率', aliases={'突破概率'}, priority=5, permission=GROUP, block=True)
user_stamina = on_command('我的体力', aliases={'体力'}, priority=5, permission=GROUP, block=True)
xiuxian_update_data = on_command('更新记录', priority=15, permission=GROUP, block=True)
level_help = on_command('列表', aliases={"灵根列表", "品阶列表", "境界列表"}, priority=15, permission=GROUP, block=True)

__xiuxian_update_data__ = f"""
#更新2024.11.28
事实证明我不喜欢写更新记录
markdown有了可喜可贺
""".strip()

__level_help_root__ = f"""\r

--灵根帮助--
轮回
异界——极道——混沌
九彩——七彩——混元
天——异——真——伪
""".strip()
__level_help_level__ = f"""\r

--境界列表--
无极仙尊六境—混沌仙帝六境
无上仙君六境—罗天上仙六境
混元大罗六境—九天玄仙六境
大罗金仙六境—太乙金仙六境
金仙六境—玄仙六境—真仙六境
登仙九劫—羽化三境—虚劫三境
合道三境—逆虚三境—炼神三境
悟道三境—天人四境—踏虚三境
通玄九重—归元九重—聚元九重
凝气九重—引气三境—感气三境
炼体九重—求道启程—我要修仙
""".strip()
__level_help_skill__ = f"""\r

--功法品阶--
永恒——起源——至圣——圣人
神级——天尊——界主——神变
神极——神劫——神海——生死
虚劫——神丹——先天——后天
--法器品阶--
天命——造化
王道——神器——圣器——仙器
灵器——玄器——宝器——符器
--奇物品阶--
太极——太素
太始——太初——太易——太阳
太阴——紫薇——离火——灵胚
灵纹——血淬——精练——凡铁
""".strip()


@xiuxian_update_data.handle(parameterless=[Cooldown()])
async def mix_elixir_help_(bot: Bot, event: GroupMessageEvent):
    """更新记录"""
    # 这里曾经是风控模块，但是已经不再需要了
    msg = __xiuxian_update_data__
    await bot.send(event=event, message=msg)
    await xiuxian_update_data.finish()


@run_xiuxian.handle(parameterless=[Cooldown(check_user=False)])
async def run_xiuxian_(bot: Bot, event: GroupMessageEvent):
    """加入修仙"""
    user_id = int(event.get_user_id())
    user_name = await sql_message.random_name()  # 获取随机名称
    root, root_type = linggen_get()  # 获取灵根，灵根类型
    rate = await sql_message.get_root_rate(root_type)  # 灵根倍率
    power = 100 * float(rate)  # 战力=境界的power字段 * 灵根的rate字段
    create_time = str(datetime.now())  # 创建账号时间
    is_new_user, msg = await sql_message.create_user(
        user_id, root, root_type, int(power), create_time, user_name
    )
    if is_new_user:
        user_msg = await check_user(event)
        if user_msg['hp'] is None or user_msg['hp'] == 0 or user_msg['hp'] == 0:
            await sql_message.update_user_hp(user_id)
        text = "耳边响起一个神秘人的声音：不要忘记仙途奇缘！!\r不知道怎么玩的话可以发送 修仙帮助 喔！！"

        msg = main_md(msg, text, '仙途奇缘', f'仙途奇缘', '修仙帮助', '修仙帮助', '修仙新手教程', '新手教程',
                      '开始修炼', '修炼')
        await bot.send(event=event, message=msg)
    else:
        await bot.send(event=event, message=msg)


@sign_in.handle(parameterless=[Cooldown()])
async def sign_in_(bot: Bot, event: GroupMessageEvent):
    """修仙签到"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    user_id = user_info['user_id']
    result = await sql_message.get_sign(user_id)
    msg = result
    await bot.send(event=event, message=msg)
    await sign_in.finish()


@level_help.handle(parameterless=[Cooldown()])
async def level_help_(bot: Bot, event: GroupMessageEvent):
    """境界帮助"""
    # 这里曾经是风控模块，但是已经不再需要了
    message = str(event.message)
    rank_msg = r'[\u4e00-\u9fa5]+'
    message = re.findall(rank_msg, message)
    if message:
        message = message[0]
    if message in ["境界列表", "境界帮助"]:
        msg = __level_help_level__
        await bot.send(event=event, message=msg)
        await level_help.finish()
    elif message in ["灵根列表", "灵根帮助"]:
        msg = __level_help_root__
        await bot.send(event=event, message=msg)
        await level_help.finish()
    elif message in ["品阶列表", "品阶帮助"]:
        msg = __level_help_skill__
        await bot.send(event=event, message=msg)
        await level_help.finish()


@restart.handle(parameterless=[Cooldown()])
async def restart_(bot: Bot, event: GroupMessageEvent, state: T_State):
    """刷新灵根信息"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)

    if user_info['stone'] < XiuConfig().remake:
        msg = "你的灵石还不够呢，快去赚点灵石吧！"
        await bot.send(event=event, message=msg)
        await restart.finish()

    linggen_options = []
    for _ in range(10):
        name, root_type = linggen_get()
        linggen_options.append((name, root_type))

    linggen_list_msg = "\r".join(
        [f"{i + 1}. {name} ({root_type})" for i, (name, root_type) in enumerate(linggen_options)])
    choice_msg_pass = f"请从以下灵根中选择一个:\r{linggen_list_msg}\r请输入对应的数字选择 (1-10):"

    state["linggen_options"] = linggen_options
    state["linggen_msg"] = choice_msg_pass
    try:
        state["msg_pass"]
    except:
        state["msg_pass"] = 0
    if user_info["root_type"] not in ["异世界之力", "极道灵根", "轮回灵根", "源宇道根", "道之本源"] or \
            state["msg_pass"] == 3:
        await bot.send(event=event, message=choice_msg_pass)
        state["msg_pass"] = 2
    else:
        msg = f"道友的灵根为{user_info['root']}，乃是{user_info['root_type']}\r若思虑周全了欲更换灵根，请回复我【确认更换灵根】"
        await bot.send(event=event, message=msg)
        state["msg_pass"] = 1


@restart.receive()
async def handle_user_choice(bot: Bot, event: GroupMessageEvent, state: T_State):
    user_choice = event.get_plaintext().strip()
    user_id = int(event.get_user_id())  # 从状态中获取用户ID
    linggen_options = state["linggen_options"]
    choice_msg_pass = state["linggen_msg"]
    selected_name, selected_root_type = max(linggen_options,
                                            key=lambda x: root_data[x[1]]["type_speeds"])
    if state["msg_pass"] == 2:
        if user_choice.isdigit():  # 判断数字
            user_choice = get_num_from_str(user_choice)[0]
            user_choice = int(user_choice)
            if 1 <= user_choice <= 10:
                selected_name, selected_root_type = linggen_options[user_choice - 1]
                msg = f"你选择了 {selected_name} 呢！\r"
            else:
                msg = "输入有误，帮你自动选择最佳灵根了嗷！\r"
        else:
            msg = "输入有误，帮你自动选择最佳灵根了嗷！\r"

        msg += await sql_message.ramaker(selected_name, selected_root_type, user_id)
        await bot.send(event=event, message=msg)
        await restart.finish()
    else:
        if user_choice == "确认更换灵根":
            await bot.send(event=event, message=choice_msg_pass)
            state["msg_pass"] = 2
            await restart.reject()


@rank.handle(parameterless=[Cooldown()])
async def rank_(bot: Bot, event: GroupMessageEvent):
    """排行榜"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    user_place = user_info['place_id']
    world_name = place.get_world_name(user_place)
    world_id = place.get_world_id(user_place)
    messages = str(event.message)
    rank_msg = r'[\u4e00-\u9fa5]+'
    message = re.findall(rank_msg, messages)
    num = get_num_from_str(messages)
    if num:
        page = int(num[0])
    else:
        page = 1
    if message:
        message = message[0]
    first_msg = ""
    scened_msg = ""
    if message in ["排行榜", "修仙排行榜", "境界排行榜", "修为排行榜"]:
        lt_rank = await sql_message.realm_top(world_id)
        scened_msg = "修为"
    elif message == "灵石排行榜":
        lt_rank = await sql_message.stone_top(world_id)
        scened_msg = "灵石"
    elif message == "战力排行榜":
        lt_rank = await sql_message.power_top(world_id)
        scened_msg = "战力"
    elif message in "宗门排行榜":
        lt_rank = await sql_message.scale_elixir_top()
        first_msg = "ID:"
        scened_msg = "\r    丹房"
        elixir_room_level_up_config = sect_config['宗门丹房参数']['elixir_room_level']
        for sect_info, index in zip(lt_rank, range(60)):
            if int(sect_info['elixir_room_level']) == 0:
                lt_rank[index]['elixir_room_level'] = "暂无" + f"  建设度:{sect_info['sect_scale']}"
            else:
                lt_rank[index]['elixir_room_level'] = (elixir_room_level_up_config[
                                                           str(sect_info['elixir_room_level'])]['name']
                                                       + f" 建设度:{sect_info['sect_scale']}")
    else:
        lt_rank = {}
    long_rank = len(lt_rank)
    page_all = (long_rank // 20) + 1 if long_rank % 20 != 0 else long_rank // 20  # 总页数
    if page_all < page != 1:
        msg = f"{message}没有那么广阔！！！"
        await bot.send(event=event, message=msg)
        await rank.finish()
    if long_rank != 0:
        # 获取页数物品数量
        item_num = page * 20 - 20
        item_num_end = item_num + 20
        lt_rank = lt_rank[item_num:item_num_end]
        top_msg = f"✨{world_name}{message}TOP{item_num_end}✨"
        msg = ''
        num = item_num
        for i in lt_rank:
            i = list(i.values())
            num += 1
            msg += f"第{num}位 {first_msg}{i[0]} {i[1]} {scened_msg}:{number_to_pro(i[2])}\r"
        msg += f"第 {page}/{page_all} 页"
        msg = main_md(top_msg, msg, '下一页', f'{message}{page + 1}', '灵石排行榜', '灵石排行榜', '宗门排行榜',
                      '宗门排行榜', '修仙帮助', '修仙帮助')
    else:
        msg = f"该排行榜空空如也！"
    await bot.send(event=event, message=msg)
    await rank.finish()


@rename.handle(parameterless=[Cooldown()])
async def remaname_(bot: Bot, event: GroupMessageEvent):
    """修改道号"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    user_id = user_info['user_id']
    user_name = await sql_message.random_name()
    msg = f"道友前往一处偏僻之地，施展乾坤换面诀\r霎时之间面容变换，并且修改道号为：{user_name}"
    await sql_message.update_user_name(user_id, user_name)
    await bot.send(event=event, message=msg)
    await rename.finish()


@level_up.handle(parameterless=[Cooldown(stamina_cost=0)])
async def level_up_(bot: Bot, event: GroupMessageEvent):
    """突破"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    user_id = user_info['user_id']
    if user_info['hp'] is None:
        # 判断用户气血是否为空
        await sql_message.update_user_hp(user_id)
    user_msg = await sql_message.get_user_info_with_id(user_id)  # 用户信息
    user_level_up_rate = int(user_msg['level_up_rate'])  # 用户失败次数加成
    level_name = user_msg['level']  # 用户境界
    level_rate = break_rate.get(level_name, 1)  # 对应境界突破的概率
    user_backs = await sql_message.get_item_by_good_id_and_user_id(user_id, 1999)  # list(back)
    main_rate_buff = await UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升，别忘了还有渡厄突破
    number = main_rate_buff['number'] if main_rate_buff is not None else 0
    now_break_rate = level_rate + user_level_up_rate + number
    is_pass = False
    if user_backs:
        if int(user_backs['goods_num']) > 0:  # 检测到有对应丹药
            is_pass = True
    if not is_pass:
        msg = (f"由于检测到背包没有【渡厄丹】，突破已经准备就绪\r"
               f"请发送，【直接突破】来突破！请注意，本次突破失败将会损失部分修为！\r"
               f"本次突破概率为：{now_break_rate}% ")
        msg = main_md("提示", msg,
                      '确认直接突破', '直接突破',
                      '领取宗门丹药', '宗门丹药领取',
                      '继续修炼', '修炼',
                      '修仙帮助', '修仙帮助')
        await bot.send(event=event, message=msg)
        await level_up.finish()
    elixir_name = user_backs['goods_name']
    elixir_desc = items.get_data_by_item_id(1999)['desc']
    msg = (f"由于检测到背包有丹药：{elixir_name}，效果：{elixir_desc}，突破已经准备就绪\r"
           f"请发送 ，【渡厄突破】 或 【直接突破】来选择是否使用丹药突破！\r"
           f"本次突破概率为：{now_break_rate}% ")
    msg = main_md("提示", msg,
                  '渡厄突破', '渡厄突破',
                  '直接突破', '直接突破',
                  '继续修炼', '修炼',
                  '修仙帮助', '修仙帮助')
    await bot.send(event=event, message=msg)
    await level_up.finish()


@level_up_zj.handle(parameterless=[Cooldown(stamina_cost=0)])
async def level_up_zj_(bot: Bot, event: GroupMessageEvent):
    """直接突破"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    user_id = user_info['user_id']
    is_type, msg = await check_user_type(user_id, 0)
    if not is_type:
        await bot.send(event=event, message=msg)
        await level_up_zj.finish()
    if user_info['hp'] is None:
        # 判断用户气血是否为空
        await sql_message.update_user_hp(user_id)
    user_info = await sql_message.get_user_info_with_id(user_id)  # 用户信息
    level_name = user_info['level']  # 用户境界
    exp = user_info['exp']  # 用户修为
    level_rate = break_rate.get(level_name, 1)  # 对应境界突破的概率
    leveluprate = int(user_info['level_up_rate'])  # 用户失败次数加成
    main_rate_buff = await UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升，别忘了还有渡厄突破
    main_exp_buff = await UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破扣修为减少
    exp_buff = main_exp_buff['exp_buff'] if main_exp_buff is not None else 0
    number = main_rate_buff['number'] if main_rate_buff is not None else 0
    le = await OtherSet().get_type(exp, level_rate + leveluprate + number, level_name, user_info)
    if le == "失败":
        # 失败惩罚，随机扣减修为
        percentage = random.randint(
            XiuConfig().level_punishment_floor, XiuConfig().level_punishment_limit
        )
        now_exp = int(int(exp) * ((percentage / 100) * (1 - exp_buff)))  # 功法突破扣修为减少
        await sql_message.update_j_exp(user_id, now_exp)  # 更新用户修为

        user_info = await sql_message.get_user_info_with_id(user_id)
        hp_down = int((now_exp / 2))
        nowhp = max(user_info['hp'] - hp_down, 1)
        nowmp = max(user_info['mp'] - now_exp, 1)
        await sql_message.update_user_hp_mp(user_id, nowhp, nowmp)  # 修为掉了，血量、真元也要掉
        update_rate = 1 if int(level_rate * XiuConfig().level_up_probability) <= 1 else int(
            level_rate * XiuConfig().level_up_probability)  # 失败增加突破几率
        await sql_message.update_levelrate(user_id, leveluprate + update_rate)
        msg = f"道友突破失败,境界受损,修为减少{number_to(now_exp)}|{now_exp}，气血流失{hp_down}，下次突破成功率增加{update_rate}%，道友不要放弃！"
        await bot.send(event=event, message=msg)
        await level_up_zj.finish()

    elif type(le) is list:
        # 突破成功
        await sql_message.updata_level(user_id, le[0])  # 更新境界
        await sql_message.update_power2(user_id)  # 更新战力
        await sql_message.update_levelrate(user_id, 0)
        await sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        msg = f"恭喜道友突破{le[0]}成功！"
        await bot.send(event=event, message=msg)
        await level_up_zj.finish()
    else:
        # 最高境界
        msg = le
        await bot.send(event=event, message=msg)
        await level_up_zj.finish()


@level_up_zj_all.handle(parameterless=[Cooldown(stamina_cost=0)])
async def level_up_zj_all_(bot: Bot, event: GroupMessageEvent):
    """快速突破"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    run = 0
    user_id = user_info['user_id']
    is_type, msg = await check_user_type(user_id, 0)
    if not is_type:
        await bot.send(event=event, message=msg)
        await level_up_zj_all.finish()
    lost_exp = 0
    if user_info['hp'] is None:
        # 判断用户气血是否为空
        await sql_message.update_user_hp(user_id)
    user_info = await sql_message.get_user_info_with_id(user_id)  # 用户信息
    level_name = user_info['level']  # 用户境界
    exp = user_info['exp']  # 用户修为
    level_rate = break_rate.get(level_name, 1)  # 对应境界突破的概率
    leveluprate = int(user_info['level_up_rate'])  # 用户失败次数加成
    main_rate_buff = await UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升，别忘了还有渡厄突破
    number = main_rate_buff['number'] if main_rate_buff is not None else 0
    msg = "开始进行快速突破\r"
    while "道友" not in (await OtherSet().get_type(exp, level_rate + leveluprate + number, level_name, user_info)):
        run = 1
        if user_info['hp'] is None:
            # 判断用户气血是否为空
            await sql_message.update_user_hp(user_id)
        user_info = await sql_message.get_user_info_with_id(user_id)  # 用户信息
        level_name = user_info['level']  # 用户境界
        exp = user_info['exp']  # 用户修为
        level_rate = break_rate.get(level_name, 1)  # 对应境界突破的概率
        leveluprate = int(user_info['level_up_rate'])  # 用户失败次数加成
        main_rate_buff = await UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升，别忘了还有渡厄突破
        main_exp_buff = await UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破扣修为减少
        exp_buff = main_exp_buff['exp_buff'] if main_exp_buff is not None else 0
        number = main_rate_buff['number'] if main_rate_buff is not None else 0
        le = await OtherSet().get_type(exp, level_rate + leveluprate + number, level_name, user_info)
        if le == "失败":
            # 失败惩罚，随机扣减修为
            percentage = random.randint(
                XiuConfig().level_punishment_floor, XiuConfig().level_punishment_limit
            )
            now_exp = int(int(exp) * ((percentage / 100) * (1 - exp_buff)))  # 功法突破扣修为减少
            await sql_message.update_j_exp(user_id, now_exp)  # 更新用户修为

            user_info = await sql_message.get_user_info_with_id(user_id)
            hp_down = int((now_exp / 2))
            nowhp = max(user_info['hp'] - hp_down, 1)
            nowmp = max(user_info['mp'] - now_exp, 1)
            await sql_message.update_user_hp_mp(user_id, nowhp, nowmp)  # 修为掉了，血量、真元也要掉
            update_rate = 1 if int(level_rate * XiuConfig().level_up_probability) <= 1 else int(
                level_rate * XiuConfig().level_up_probability)  # 失败增加突破几率
            await sql_message.update_levelrate(user_id, leveluprate + update_rate)
            msg += f"道友突破失败,境界受损,修为减少{number_to(now_exp)}|{now_exp}，气血流失{hp_down}，下次突破成功率增加{update_rate}%，道友不要放弃！\r"
            lost_exp += now_exp
        elif type(le) is list:
            # 突破成功
            await sql_message.updata_level(user_id, le[0])  # 更新境界
            await sql_message.update_power2(user_id)  # 更新战力
            await sql_message.update_levelrate(user_id, 0)
            await sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
            msg += f"恭喜道友突破{le[0]}成功！\r"

        else:
            # 最高境界
            msg += le + "\r"
    final_level = (await sql_message.get_user_info_with_id(user_id))["level"]
    if run == 1:
        msg += f"快速突破结束本次快速突破损失{number_to(lost_exp)}|{lost_exp}点修为\r成功突破至{final_level}"
    else:
        msg += await OtherSet().get_type(exp, level_rate + leveluprate + number, level_name, user_info)
    await bot.send(event=event, message=msg)
    await level_up_zj_all.finish()


@level_up_dr.handle(parameterless=[Cooldown(stamina_cost=0)])
async def level_up_dr_(bot: Bot, event: GroupMessageEvent):
    """渡厄 突破"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    user_id = user_info['user_id']
    is_type, msg = await check_user_type(user_id, 0)
    if not is_type:
        await bot.send(event=event, message=msg)
        await level_up_dr.finish()
    if user_info['hp'] is None:
        # 判断用户气血是否为空
        await sql_message.update_user_hp(user_id)
    user_info = await sql_message.get_user_info_with_id(user_id)  # 用户信息
    elixir_name = "渡厄丹"
    level_name = user_info['level']  # 用户境界
    exp = user_info['exp']  # 用户修为
    level_rate = break_rate.get(level_name, 1)  # 对应境界突破的概率
    user_level_up_rate = int(user_info['level_up_rate'])  # 用户失败次数加成
    main_rate_buff = await UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升
    number = main_rate_buff['number'] if main_rate_buff is not None else 0
    le = await OtherSet().get_type(exp, level_rate + user_level_up_rate + number, level_name, user_info)
    user_backs = await sql_message.get_item_by_good_id_and_user_id(user_id=user_id, goods_id=1999)
    pause_flag = False
    if user_backs:
        if int(user_backs['goods_num']) > 0:  # 检测到有对应丹药
            pause_flag = True

    if not pause_flag:
        msg = f"道友突破需要使用{elixir_name}，但您的背包中没有该丹药！"
        await bot.send(event=event, message=msg)
        await level_up_dr.finish()

    if le == "失败":
        # 突破失败
        if pause_flag:
            await sql_message.update_back_j(user_id, 1999, use_key=1)
            update_rate = 1 if int(level_rate * XiuConfig().level_up_probability) <= 1 else int(
                level_rate * XiuConfig().level_up_probability)  # 失败增加突破几率
            await sql_message.update_levelrate(user_id, user_level_up_rate + update_rate)
            msg = f"道友突破失败，但是使用了丹药{elixir_name}，本次突破失败不扣除修为下次突破成功率增加{update_rate}%，道友不要放弃！"
        else:
            # 失败惩罚，随机扣减修为
            percentage = random.randint(
                XiuConfig().level_punishment_floor, XiuConfig().level_punishment_limit
            )
            main_exp_buff = await UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破扣修为减少
            exp_buff = main_exp_buff['exp_buff'] if main_exp_buff is not None else 0
            now_exp = int(int(exp) * ((percentage / 100) * (1 - exp_buff)))
            await sql_message.update_j_exp(user_id, now_exp)  # 更新用户修为
            user_info = await sql_message.get_user_info_with_id(user_id)

            nowhp = max(user_info['hp'] - int((now_exp / 2)), 1)
            nowmp = max(user_info['mp'] - now_exp, 1)
            await sql_message.update_user_hp_mp(user_id, nowhp, nowmp)  # 修为掉了，血量、真元也要掉
            update_rate = 1 if int(level_rate * XiuConfig().level_up_probability) <= 1 else int(
                level_rate * XiuConfig().level_up_probability)  # 失败增加突破几率
            await sql_message.update_levelrate(user_id, user_level_up_rate + update_rate)
            msg = f"没有检测到{elixir_name}，道友突破失败,境界受损,修为减少{now_exp}，下次突破成功率增加{update_rate}%，道友不要放弃！"
        await bot.send(event=event, message=msg)
        await level_up_dr.finish()

    elif type(le) is list:
        # 突破成功
        await sql_message.updata_level(user_id, le[0])  # 更新境界
        await sql_message.update_power2(user_id)  # 更新战力
        await sql_message.update_levelrate(user_id, 0)
        await sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        msg = f"恭喜道友突破{le[0]}成功"
        await bot.send(event=event, message=msg)
        await level_up_dr.finish()
    else:
        # 最高境界
        msg = le
        await bot.send(event=event, message=msg)
        await level_up_dr.finish()


@level_up_dr_fast.handle(parameterless=[Cooldown(stamina_cost=0)])
async def level_up_dr_fast_(bot: Bot, event: GroupMessageEvent):
    """渡厄 突破"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    user_id = user_info['user_id']
    is_type, msg = await check_user_type(user_id, 0)
    if not is_type:
        await bot.send(event=event, message=msg)
        await level_up_dr_fast.finish()
    elixir_name = "渡厄丹"
    user_backs = await sql_message.get_item_by_good_id_and_user_id(user_id=user_id, goods_id=1999)
    elixir_num = int(user_backs['goods_num'])
    pause_flag = False
    if user_backs:
        if elixir_num > 0:  # 检测到有对应丹药
            pause_flag = True

    if not pause_flag:
        msg = f"道友突破需要使用{elixir_name}，但您的背包中没有该丹药！"
        await bot.send(event=event, message=msg)
        await level_up_dr_fast.finish()

    level_name = user_info['level']  # 用户境界
    exp = user_info['exp']  # 用户修为

    level_rate = break_rate.get(level_name, 1)  # 对应境界突破的概率
    user_level_up_rate = int(user_info['level_up_rate'])  # 用户失败次数加成
    main_rate_buff = await UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升
    number = main_rate_buff['number'] if main_rate_buff is not None else 0
    now_break_rate = level_rate + user_level_up_rate + number

    break_count = 0  # 突破次数计数器
    level_up_rate_increase = int(level_rate * XiuConfig().level_up_probability)
    update_rate = 1 if level_up_rate_increase <= 1 else level_up_rate_increase  # 失败增加突破几率
    break_end_msg = ''
    for _ in range(100):
        print(now_break_rate)
        if elixir_num < 1:
            break_end_msg = f"道友背包内{elixir_name}已耗尽！本次突破提升{break_count * update_rate}突破概率"
            await sql_message.update_levelrate(user_id, now_break_rate - level_rate - number)
            break
        le = await OtherSet().get_type(exp, now_break_rate, level_name, user_info)
        if "道友" in le:
            break_end_msg = le
            break
        now_break_rate += update_rate
        break_count += 1
        elixir_num -= 1
        if isinstance(le, list):
            await sql_message.updata_level(user_id, le[0])  # 更新境界
            await sql_message.update_power2(user_id)  # 更新战力
            await sql_message.update_levelrate(user_id, 0)
            await sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
            break_end_msg = f"恭喜道友突破{le[0]}成功"
            break

    await sql_message.update_back_j(user_id, 1999, num=break_count, use_key=1)
    msg = f"突破结束\r共进行{break_count}次突破，{break_end_msg}\r"
    msg = simple_md(msg, '继续突破', '快速渡厄突破', '。')
    await bot.send(event=event, message=msg)
    await level_up_dr_fast.finish()


@user_leveluprate.handle(parameterless=[Cooldown()])
async def user_leveluprate_(bot: Bot, event: GroupMessageEvent):
    """我的突破概率"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    user_id = user_info['user_id']
    leveluprate = int(user_info['level_up_rate'])  # 用户失败次数加成
    level_name = user_info['level']  # 用户境界
    level_rate = break_rate.get(level_name, 1)  #
    main_rate_buff = await UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升
    number = main_rate_buff['number'] if main_rate_buff is not None else 0
    msg = f"道友下一次突破成功概率为{level_rate + leveluprate + number}%"
    await bot.send(event=event, message=msg)
    await user_leveluprate.finish()


@user_stamina.handle(parameterless=[Cooldown()])
async def user_stamina_(bot: Bot, event: GroupMessageEvent):
    """我的体力信息"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    msg = f"当前体力：{user_info['user_stamina']}"
    await bot.send(event=event, message=msg)
    await user_stamina.finish()


@give_stone.handle(parameterless=[Cooldown()])
async def give_stone_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """送灵石"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    user_id = user_info['user_id']
    user_name = user_info['user_name']
    user_stone_num = user_info['stone']
    msg = args.extract_plain_text()
    stone_num = get_num_from_str(msg)
    give_qq = await get_id_from_str(msg)  # 使用道号获取用户id，代替原at
    if stone_num:
        give_stone_num = stone_num[0]
    else:
        stone_num = None
        give_stone_num = 0
    if stone_num:
        if int(give_stone_num) > int(user_stone_num):
            msg = f"道友的灵石不够，请重新输入！"
            await bot.send(event=event, message=msg)
            await give_stone.finish()
    else:
        msg = f"请输入正确的灵石数量！！！"
        await bot.send(event=event, message=msg)
        await give_stone.finish()
    if give_qq:
        if str(give_qq) == str(user_id):
            msg = f"请不要送灵石给自己！"
            await bot.send(event=event, message=msg)
            await give_stone.finish()
        else:
            give_user = await sql_message.get_user_info_with_id(give_qq)
            if give_user:
                if await place.is_the_same_world(give_qq, user_id) is False:
                    msg = f"\r{give_user['user_name']}道友与你不在同一位面，无法赠送！！！跨位面赠送灵石费用及其昂贵！！！"
                    await bot.send(event=event, message=msg)
                    await give_stone.finish()
                if await place.is_the_same_place(give_qq, user_id):
                    num = int(give_stone_num)
                    send_msg, msg, is_pass = await check_limit.send_stone_check(user_id, give_qq, num)
                    if is_pass:
                        await sql_message.update_ls(user_id, give_stone_num, 2)  # 减少用户灵石
                        await sql_message.update_ls(give_qq, num, 1)  # 增加用户灵石
                        msg = f"\r{user_name}道友与好友在同一位置，当面赠送：\r" + send_msg + msg
                        await limit_handle.update_user_log_data(user_id, send_msg)
                        await limit_handle.update_user_log_data(give_qq, send_msg)
                    await bot.send(event=event, message=msg)
                    await give_stone.finish()

                give_stone_num2 = int(give_stone_num) * 0.1
                num = int(give_stone_num) - int(give_stone_num2)
                send_msg, msg, is_pass = await check_limit.send_stone_check(user_id, give_qq, num)
                if is_pass:
                    await sql_message.update_ls(user_id, give_stone_num, 2)  # 减少用户灵石
                    await sql_message.update_ls(give_qq, num, 1)  # 增加用户灵石
                    msg = (f"\r{user_name}道友与好友不在一地，通过远程邮寄赠送：\r" + send_msg + msg +
                           f"\r收取远程邮寄手续费{(number_to(give_stone_num2))}|{int(give_stone_num2)}枚！")
                    await limit_handle.update_user_log_data(user_id, send_msg)
                    await limit_handle.update_user_log_data(give_qq, send_msg)
                await bot.send(event=event, message=msg)
                await give_stone.finish()
            else:
                msg = f"对方未踏入修仙界，不可赠送！"
                await bot.send(event=event, message=msg)
                await give_stone.finish()
    else:
        msg = f"未获到对方信息，请输入正确的道号！"
        await bot.send(event=event, message=msg)
        await give_stone.finish()


# 偷灵石
@steal_stone.handle(parameterless=[Cooldown(stamina_cost=2400)])
async def steal_stone_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 这里曾经是风控模块，但是已经不再需要了
    user_info = await check_user(event)
    args = args.extract_plain_text()
    user_id = user_info['user_id']
    steal_user = None
    steal_user_stone = None
    user_stone_num = user_info['stone']
    coststone_num = XiuConfig().tou
    if int(coststone_num) > int(user_stone_num):
        msg = f"道友的偷窃准备(灵石)不足，请打工之后再切格瓦拉！"
        await sql_message.update_user_stamina(user_id, 1000, 1)
        await bot.send(event=event, message=msg)
        await steal_stone.finish()
    steal_qq = await get_id_from_str(args)  # 使用道号获取用户id，代替原at
    if steal_qq:
        if steal_qq == user_id:
            msg = f"请不要偷自己刷成就！"
            await sql_message.update_user_stamina(user_id, 1000, 1)
            await bot.send(event=event, message=msg)
            await steal_stone.finish()
        else:
            steal_user = await sql_message.get_user_info_with_id(steal_qq)
            if steal_user:
                steal_user_stone = steal_user['stone']
    if steal_user:
        steal_success = random.randint(0, 100)
        result = OtherSet().get_power_rate(user_info['power'], steal_user['power'])
        if isinstance(result, int):
            if int(steal_success) > result:
                await sql_message.update_ls(user_id, coststone_num, 2)  # 减少手续费
                await sql_message.update_ls(steal_qq, coststone_num, 1)  # 增加被偷的人的灵石
                msg = f"道友偷窃失手了，被对方发现并被派去义务劳工！赔款{coststone_num}灵石"
                await bot.send(event=event, message=msg)
                await steal_stone.finish()
            get_stone = random.randint(int(XiuConfig().tou_lower_limit * steal_user_stone),
                                       int(XiuConfig().tou_upper_limit * steal_user_stone))
            if int(get_stone) > int(steal_user_stone):
                await sql_message.update_ls(user_id, steal_user_stone, 1)  # 增加偷到的灵石
                await sql_message.update_ls(steal_qq, steal_user_stone, 2)  # 减少被偷的人的灵石
                msg = f"{steal_user['user_name']}道友已经被榨干了~"
                await bot.send(event=event, message=msg)
                await steal_stone.finish()
            else:
                await sql_message.update_ls(user_id, get_stone, 1)  # 增加偷到的灵石
                await sql_message.update_ls(steal_qq, get_stone, 2)  # 减少被偷的人的灵石
                msg = f"共偷取{steal_user['user_name']}道友{number_to(get_stone)}枚灵石！"
                await bot.send(event=event, message=msg)
                await steal_stone.finish()
        else:
            msg = result
            await bot.send(event=event, message=msg)
            await steal_stone.finish()
    else:
        msg = f"对方未踏入修仙界，不要对凡人出手！"
        await bot.send(event=event, message=msg)
        await steal_stone.finish()


# GM加灵石
@gm_command.handle(parameterless=[Cooldown()])
async def gm_command_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 这里曾经是风控模块，但是已经不再需要了
    msg_text = args.extract_plain_text()
    stone_num_match = get_num_from_str(msg_text)  # 提取数字
    give_qq = await get_id_from_str(msg_text)  # 道号
    command_target = get_strs_from_str(msg_text)
    if command_target:
        command_target = command_target[0]
    else:
        command_target = None
    give_stone_num = int(stone_num_match[0]) if stone_num_match else 0  # 默认灵石数为0，如果有提取到数字，则使用提取到的第一个数字
    if give_qq:
        give_user = await sql_message.get_user_info_with_id(give_qq)
        await sql_message.update_ls(give_qq, give_stone_num, 1)  # 增加用户灵石
        msg = f"共赠送{number_to(give_stone_num)}枚灵石给{give_user['user_name']}道友！"
        await bot.send(event=event, message=msg)
        await gm_command.finish()
    elif command_target == "all":
        await sql_message.update_ls_all(give_stone_num)
        msg = f"赠送所有用户{give_stone_num}灵石,请注意查收！"
        await bot.send(event=event, message=msg)
    else:
        msg = f"对方未踏入修仙界，不可赠送！"
        await bot.send(event=event, message=msg)
        await gm_command.finish()
    await gm_command.finish()


# GM加思恋结晶
@gm_command_miss.handle(parameterless=[Cooldown()])
async def gm_command_miss_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 这里曾经是风控模块，但是已经不再需要了
    msg_text = args.extract_plain_text()
    stone_num_match = get_num_from_str(msg_text)  # 提取数字
    give_qq = await get_id_from_str(msg_text)  # 道号
    command_target = get_strs_from_str(msg_text)
    if command_target:
        command_target = command_target[0]
    else:
        command_target = None
    give_stone_num = int(stone_num_match[0]) if stone_num_match else 0  # 默认灵石数为0，如果有提取到数字，则使用提取到的第一个数字
    if give_qq:
        give_user = await sql_message.get_user_info_with_id(give_qq)
        await xiuxian_impart.update_stone_num(give_stone_num, give_qq, 1)
        msg = f"共赠送{number_to(give_stone_num)}颗思恋结晶给{give_user['user_name']}道友！"
        await bot.send(event=event, message=msg)
        await gm_command_miss.finish()
    elif command_target == "all":
        await xiuxian_impart.update_impart_stone_all(give_stone_num)
        msg = f"赠送所有用户{give_stone_num}思恋结晶,请注意查收！"
        await bot.send(event=event, message=msg)
    else:
        msg = f"对方未踏入修仙界，不可赠送！"
        await bot.send(event=event, message=msg)
        await gm_command.finish()
    await gm_command_miss.finish()


# GM加祈愿结晶
@gm_command_pray.handle(parameterless=[Cooldown()])
async def gm_command_pray_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 这里曾经是风控模块，但是已经不再需要了
    msg_text = args.extract_plain_text()
    stone_num_match = get_num_from_str(msg_text)  # 提取数字
    give_qq = await get_id_from_str(msg_text)  # 道号
    command_target = get_strs_from_str(msg_text)
    if command_target:
        command_target = command_target[0]
    else:
        command_target = None
    give_stone_num = int(stone_num_match[0]) if stone_num_match else 0  # 默认为0，如果有提取到数字，则使用提取到的第一个数字
    if give_qq:
        give_user = await sql_message.get_user_info_with_id(give_qq)
        await xiuxian_impart.update_pray_stone_num(give_stone_num, give_qq, 1)
        msg = f"共赠送{number_to(give_stone_num)}颗祈愿结晶给{give_user['user_name']}道友！"
        await bot.send(event=event, message=msg)
        await gm_command_pray.finish()
    elif command_target == "all":
        await xiuxian_impart.update_impart_pray_stone_all(give_stone_num)
        msg = f"赠送所有用户{give_stone_num}祈愿结晶,请注意查收！"
        await bot.send(event=event, message=msg)
    else:
        msg = f"对方未踏入修仙界，不可赠送！"
        await bot.send(event=event, message=msg)
        await gm_command.finish()
    await gm_command_pray.finish()


@cz.handle(parameterless=[Cooldown()])
async def cz_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """创造物品"""
    # 这里曾经是风控模块，但是已经不再需要了
    msg = args.extract_plain_text()
    strs = get_strs_from_str(msg)
    nums = get_num_from_str(msg)
    if strs:
        goods_name = strs[0]
        if len(strs) > 1:
            send_name = strs[1]
        else:
            send_name = None
    else:
        goods_name = None
        send_name = None
        msg = f"请输入正确指令！例如：创造 物品 道号 数量 (道号为all赠送所有用户)"
        await bot.send(event=event, message=msg)
        await cz.finish()
    if nums:
        goods_num = int(nums[0])
    else:
        goods_num = 1
    goods_id = -1
    goods_type = None
    is_item = False
    for k, v in items.items.items():
        if goods_name == v['name']:
            goods_id = k
            goods_type = v['type']
            is_item = True
            break
        else:
            continue
    if is_item:
        pass
    else:
        msg = f"物品不存在！！！"
        await bot.send(event=event, message=msg)
        await cz.finish()
    give_qq = await sql_message.get_user_id(send_name)  # 使用道号获取用户id，代替原at
    if give_qq:
        give_user = await sql_message.get_user_info_with_id(give_qq)
        if give_user:
            await sql_message.send_back(give_qq, int(goods_id), goods_name, goods_type, goods_num, 1)
            msg = f"{give_user['user_name']}道友获得了系统赠送的{goods_num}个{goods_name}！"
        else:
            msg = f"对方未踏入修仙界，不可赠送！"
    elif send_name == "all":
        await sql_message.send_all_user_item(int(goods_id), goods_num, 1)  # 给每个用户发送物品
        msg = f"赠送所有用户{goods_name}{goods_num}个,请注意查收！"
    else:
        msg = "请输入正确指令！例如：创造 物品 道号 数量 (道号为all赠送所有用户)"
    await bot.send(event=event, message=msg)
    await cz.finish()


@cz_ts.handle(parameterless=[Cooldown()])
async def cz_ts_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """创造物品"""
    # 这里曾经是风控模块，但是已经不再需要了
    msg = args.extract_plain_text()
    strs = get_strs_from_str(msg)
    nums = get_num_from_str(msg)
    if strs:
        goods_name = strs[0]
        if len(strs) > 1:
            send_name = strs[1]
        else:
            send_name = None
    else:
        goods_name = None
        send_name = None
        msg = f"请输入正确指令！例如：创造 物品 道号 数量 (道号为all赠送所有用户)"
        await bot.send(event=event, message=msg)
        await cz_ts.finish()
    if nums:
        goods_num = int(nums[0])
    else:
        goods_num = 1
    item_id: int = items.items_map.get(goods_name)
    if not item_id:
        msg = f"物品不存在！！！"
        await bot.send(event=event, message=msg)
        await cz_ts.finish()
    item_info: dict = items.get_data_by_item_id(item_id)
    goods_type = item_info['type']
    give_qq = await sql_message.get_user_id(send_name)  # 使用道号获取用户id，代替原at
    if give_qq:
        give_user = await sql_message.get_user_info_with_id(give_qq)
        if give_user:
            await sql_message.send_back(give_qq, int(item_id), goods_name, goods_type, goods_num, 0)
            msg = f"{give_user['user_name']}道友获得了系统赠送的{goods_num}个{goods_name}！"
        else:
            msg = f"对方未踏入修仙界，不可赠送！"
    elif send_name == "all":
        await sql_message.send_all_user_item(int(item_id), goods_num, 0)  # 给每个用户发送物品
        msg = f"赠送所有用户{goods_name}{goods_num}个,请注意查收！"
    else:
        msg = "请输入正确指令！例如：创造 物品 道号 数量 (道号为all赠送所有用户)"
    await bot.send(event=event, message=msg)
    await cz_ts.finish()


# GM改灵根
@gmm_command.handle(parameterless=[Cooldown()])
async def gmm_command_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 这里曾经是风控模块，但是已经不再需要了
    arg = args.extract_plain_text()
    if not args:
        msg = f"请输入正确指令！例如：灵根更换 x(1为混沌,2为融合,3为超,4为龙,5为天,6为千世,7为万世,8为无上)"
        await bot.send(event=event, message=msg)
        await gm_command.finish()

    give_qq = await get_id_from_str(arg)  # 使用道号获取用户id，代替原at
    num = get_num_from_str(arg)
    root_num = num[0] if num else 1
    give_user = await sql_message.get_user_info_with_id(give_qq)
    if give_user:
        root_name = await sql_message.update_root(give_qq, root_num)
        await sql_message.update_power2(give_qq)
        msg = f"{give_user['user_name']}道友的灵根已变更为{root_name}！"
        await bot.send(event=event, message=msg)
        await gmm_command.finish()
    else:
        msg = f"对方未踏入修仙界，不可修改！"
        await bot.send(event=event, message=msg)
        await gmm_command.finish()


@rob_stone.handle(parameterless=[Cooldown(stamina_cost=0)])
async def rob_stone_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """抢劫
            player1 = {
            "NAME": player,
            "HP": player,
            "ATK": ATK,
            "COMBO": COMBO
        }"""
    user_info = await check_user(event)
    user_id = user_info["user_id"]
    give_qq = await sql_message.get_user_id(args)  # 使用道号获取用户id，代替原at
    player1 = {"user_id": None, "道号": None, "气血": None, "攻击": None, "真元": None, '会心': None, '爆伤': None,
               '防御': 0}
    player2 = {"user_id": None, "道号": None, "气血": None, "攻击": None, "真元": None, '会心': None, '爆伤': None,
               '防御': 0}
    user_2 = await sql_message.get_user_info_with_id(give_qq)
    if user_info and user_2:
        if user_info['root'] == "器师":
            msg = f"目前职业无法抢劫！"
            await bot.send(event=event, message=msg)
            await rob_stone.finish()

        if give_qq:
            if str(give_qq) == str(user_id):
                msg = f"请不要抢自己刷成就！"
                await bot.send(event=event, message=msg)
                await rob_stone.finish()

            if user_2['root'] == "器师":
                msg = f"对方职业无法被抢劫！"
                await bot.send(event=event, message=msg)
                await rob_stone.finish()

            if user_2:
                if user_info['hp'] is None:
                    # 判断用户气血是否为None
                    await sql_message.update_user_hp(user_id)
                    user_info = await sql_message.get_user_info_with_id(user_id)
                if user_2['hp'] is None:
                    await sql_message.update_user_hp(give_qq)
                    user_2 = await sql_message.get_user_info_with_id(give_qq)

                if user_2['hp'] <= user_2['exp'] / 10:
                    time_2 = leave_harm_time(give_qq)
                    msg = f"对方重伤藏匿了，无法抢劫！距离对方脱离生命危险还需要{time_2}分钟！"
                    await bot.send(event=event, message=msg)
                    await rob_stone.finish()

                if user_info['hp'] <= user_info['exp'] / 10:
                    time_msg = leave_harm_time(user_id)
                    msg = f"重伤未愈，动弹不得！距离脱离生命危险还需要{time_msg}分钟！"
                    msg += f"请道友进行闭关，或者使用药品恢复气血，不要干等，没有自动回血！！！"
                    await bot.send(event=event, message=msg)
                    await rob_stone.finish()

                impart_data_1 = await xiuxian_impart.get_user_info_with_id(user_id)
                player1['user_id'] = user_info['user_id']
                player1['道号'] = user_info['user_name']
                player1['气血'] = 1
                player1['攻击'] = 1
                player1['真元'] = user_info['mp']
                player1['会心'] = int(
                    (0.01 + impart_data_1['impart_know_per'] if impart_data_1 is not None else 0) * 100)
                player1['爆伤'] = int(
                    1.5 + impart_data_1['impart_burst_per'] if impart_data_1 is not None else 0)
                user_buff_data = UserBuffDate(user_id)
                user_armor_data = await user_buff_data.get_user_armor_buff_data()
                if user_armor_data is not None:
                    def_buff = int(user_armor_data['def_buff'])
                else:
                    def_buff = 0
                player1['防御'] = def_buff

                impart_data_2 = await xiuxian_impart.get_user_info_with_id(user_2['user_id'])
                player2['user_id'] = user_2['user_id']
                player2['道号'] = user_2['user_name']
                player2['气血'] = user_2['hp']
                player2['攻击'] = user_2['atk']
                player2['真元'] = user_2['mp']
                player2['会心'] = int(
                    (0.01 + impart_data_2['impart_know_per'] if impart_data_2 is not None else 0) * 100)
                player2['爆伤'] = int(
                    1.5 + impart_data_2['impart_burst_per'] if impart_data_2 is not None else 0)
                user_buff_data = UserBuffDate(user_2['user_id'])
                user_armor_data = await user_buff_data.get_user_armor_buff_data()
                if user_armor_data is not None:
                    def_buff = int(user_armor_data['def_buff'])
                else:
                    def_buff = 0
                player2['防御'] = def_buff

                result, victor = OtherSet().player_fight(player1, player2)
                await send_msg_handler(bot, event, '决斗场', bot.self_id, result)
                if victor == player1['道号']:
                    foe_stone = user_2['stone']
                    if foe_stone > 0:
                        exps = int(user_2['exp'] * 0.005)
                        msg = f"大战一番，战胜对手，获取灵石{number_to(foe_stone * 0.1)}枚，修为增加{number_to(exps)}，对手修为减少{number_to(exps / 2)}， 你不应该看见这个，重写版战斗系统灰度中！！"
                        if XiuConfig().img:
                            pic = await get_msg_pic(f"@{event.sender.nickname}\r" + msg)
                            await bot.send(event=event, message=MessageSegment.image(pic))
                        else:
                            await bot.send(event=event, message=msg)
                        await rob_stone.finish()
                    else:
                        exps = int(user_2['exp'] * 0.005)
                        msg = (
                            f"大战一番，战胜对手，结果对方是个穷光蛋，修为增加{number_to(exps)}，对手修为减少{number_to(exps / 2)}........"
                            f"实际上没有，重写版战斗系统灰度中！！")
                        if XiuConfig().img:
                            pic = await get_msg_pic(f"@{event.sender.nickname}\r" + msg)
                            await bot.send(event=event, message=MessageSegment.image(pic))
                        else:
                            await bot.send(event=event, message=msg)
                        await rob_stone.finish()

                elif victor == player2['道号']:
                    mind_stone = user_info['stone']
                    if mind_stone > 0:
                        exps = int(user_info['exp'] * 0.005)
                        msg = (
                            f"大战一番，被对手反杀，损失灵石{number_to(mind_stone * 0.1)}枚，修为减少{number_to(exps)}，对手获取灵石{number_to(mind_stone * 0.1)}枚，修为增加{number_to(exps / 2)}"
                            f"。。。。。。实际上没有，重写版战斗系统灰度中！！")
                        if XiuConfig().img:
                            pic = await get_msg_pic(f"@{event.sender.nickname}\r" + msg)
                            await bot.send(event=event, message=MessageSegment.image(pic))
                        else:
                            await bot.send(event=event, message=msg)
                        await rob_stone.finish()
                    else:
                        exps = int(user_info['exp'] * 0.005)
                        msg = (
                            f"大战一番，被对手反杀，修为减少{number_to(exps)}，对手修为增加{number_to(exps / 2)}，，，，，，，，"
                            f"实际上没有，重写版战斗系统灰度中！！")
                        if XiuConfig().img:
                            pic = await get_msg_pic(f"@{event.sender.nickname}\r" + msg)
                            await bot.send(event=event, message=MessageSegment.image(pic))
                        else:
                            await bot.send(event=event, message=msg)
                        await rob_stone.finish()

                else:
                    msg = f"发生错误，请检查后台！"
                    await bot.send(event=event, message=msg)
                    await rob_stone.finish()

    else:
        msg = f"对方未踏入修仙界，不可抢劫！"
        await bot.send(event=event, message=msg)
        await rob_stone.finish()
