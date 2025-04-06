import json
import operator
import os
import random
from pathlib import Path

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent
)
from nonebot.params import CommandArg

from .impart_data import impart_data_json
from .impart_uitls import impart_check, re_impart_data, get_rank_plus, join_card_check
from .. import NICKNAME
from ..xiuxian_utils.clean_utils import get_num_from_str, main_md, simple_md
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import check_user
from ..xiuxian_utils.xiuxian2_handle import xiuxian_impart

# 替换模块
cache_help = {}
img_path = Path(f"{os.getcwd()}/data/xiuxian/卡图")

impart_draw_fast = on_command("连续抽卡", aliases={"传承抽卡"}, priority=16, permission=GROUP, block=True)
impart_draw = on_command("传承共鸣", aliases={"传承祈愿"}, priority=16, permission=GROUP, block=True)
impart_back = on_command("传承背包", aliases={"我的传承背包"}, priority=15, permission=GROUP, block=True)
impart_info = on_command("传承信息", aliases={"我的传承信息", "我的传承"}, priority=10, permission=GROUP, block=True)
impart_help = on_command("传承帮助", aliases={"虚神界帮助"}, priority=8, permission=GROUP, block=True)
re_impart_load = on_command("加载传承数据", priority=45, permission=GROUP, block=True)
impart_img = on_command("传承卡图", aliases={"传承卡片"}, priority=50, permission=GROUP, block=True)
__impart_help__ = (f"✨虚神界介绍✨\r"
)


@impart_help.handle(parameterless=[Cooldown()])
async def impart_help_(bot: Bot, event: GroupMessageEvent):
    """传承帮助"""
    # 这里曾经是风控模块，但是已经不再需要了
    msg = main_md (__impart_help__,
                 f"1：传承抽卡\r"
                 f" 🔹 使用思恋结晶获取一次传承卡片\r"
                 f"2：传承祈愿\r"
                 f" 🔹 使用祈愿结晶获取一次虚神界闭关时间\r"
                 f" 🔹 与传承卡数量有关，0传承卡请勿使用\r"
                 f"3：传承信息\r"
                 f" 🔹 获取传承主要信息\r"
                 f"4：传承背包\r"
                 f" 🔹 获取传承全部信息\r"
                 f"5：加载传承数据\r"
                 f" 🔹 重新加载所有传承属性\r"
                 f"6：传承卡图\r"
                 f" 🔹 加上卡片名字获取传承卡牌详情\r"
                 f"7：虚神界对决\r"
                 f" 🔹 进入虚神界与{NICKNAME}进行对决\r"
                 f"8：虚神界祈愿\r"
                 f" 🔹 获得自身传承与虚神界内传承共鸣的机会\r"
                 f"9：虚神界闭关\r🔹 进入虚神界闭关效率是外界闭关的6倍\r"
                 f" "
                  f"虚神界祈愿获取祈愿结晶，共鸣越高祈愿时间越多！\r",
                  "虚神界对决", "虚神界对决",
                  "虚神界祈愿", "虚神界祈愿",
                  "虚神界闭关", "虚神界闭关",
                  "传承背包", "传承背包" )
    await bot.send(event=event, message=msg)
    await impart_help.finish()


@impart_img.handle(parameterless=[Cooldown()])
async def impart_img_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """传承卡图"""
    # 这里曾经是风控模块，但是已经不再需要了
    img_name = args.extract_plain_text().strip()
    all_data = impart_data_json.data_all_()
    x = img_name
    try:
        all_data[x]["type"]
    except KeyError:
        msg = f"没有找到此卡图！"
        await bot.send(event=event, message=msg)
        await impart_img.finish()
    msg = f"\r传承卡图：{img_name}\r效果：\r"
    if all_data[x]["type"] == "impart_two_exp":
        msg += "每日双修次数提升：" + str(all_data[x]["vale"])
    elif all_data[x]["type"] == "impart_exp_up":
        msg += "闭关经验提升：" + str(all_data[x]["vale"] * 100) + "%"
    elif all_data[x]["type"] == "impart_atk_per":
        msg += "攻击力提升：" + str(all_data[x]["vale"] * 100) + "%"
    elif all_data[x]["type"] == "impart_hp_per":
        msg += "气血提升：" + str(all_data[x]["vale"] * 100) + "%"
    elif all_data[x]["type"] == "impart_mp_per":
        msg += "真元提升" + str(all_data[x]["vale"] * 100) + "%"
    elif all_data[x]["type"] == "boss_atk":
        msg += "boss战攻击提升" + str(all_data[x]["vale"] * 100) + "%"
    elif all_data[x]["type"] == "impart_know_per":
        msg += "会心提升：" + str(all_data[x]["vale"] * 100) + "%"
    elif all_data[x]["type"] == "impart_burst_per":
        msg += "会心伤害提升：" + str(all_data[x]["vale"] * 100) + "%"
    elif all_data[x]["type"] == "impart_mix_per":
        msg += "炼丹收取数量增加：" + str(all_data[x]["vale"])
    elif all_data[x]["type"] == "impart_reap_per":
        msg += "灵田收取数量增加：" + str(all_data[x]["vale"])
    else:
        pass
    await bot.send(event=event, message=msg)
    await impart_img.finish()


@impart_draw.handle(parameterless=[Cooldown(cd_time=5)])
async def impart_draw_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """传承抽卡"""

    user_info = await check_user(event)
    user_id = user_info['user_id']
    arg = args.extract_plain_text()
    num = get_num_from_str(arg)
    num = int(num[0]) if num else 1
    impart_data_draw = await impart_check(user_id)
    fail_msg = [f"道友的祈愿结晶不足{num}个！！无法进行{num}次祈愿!"] if impart_data_draw.get('pray_stone_num',
                                                                                            0) < num else []
    if fail_msg:
        await bot.send(event=event, message='\r'.join(fail_msg))
        await impart_draw.finish()
    card = 0
    get_card = 0
    break_num = 0
    card_dict = {'had': [], 'new': []}
    cards = impart_data_draw['cards']
    user_had_cards = json.loads(cards) if cards else []
    hard_card_num = len(user_had_cards)
    if hard_card_num < 70:
        msg = simple_md("当前传承卡过少，无法得到传承共鸣！请先",
                        "传承抽卡", "传承抽卡", "获得足够传承卡后再试！")
        await bot.send(event=event, message=msg)
        await impart_draw.finish()
    img_list = impart_data_json.data_all_keys()
    user_impart_data = await xiuxian_impart.get_user_info_with_id(user_id)
    pray_count = user_impart_data.get('pray_card_num')
    msg = f"道友{user_info['user_name']}的传承祈愿"
    await xiuxian_impart.update_pray_stone_num(num, user_id, 2)
    for _ in range(num):
        if hard_card_num == 106:
            break_num += 1
            get_card += 20
            continue
        want_num = 20 * (hard_card_num / 106)
        get_car_value = random.randint(hard_card_num, 106)
        card_num = round(want_num * get_car_value / 106, 0)
        get_card += card_num
        if (pray_count := card_num + pray_count) > 19:
            reap_img = random.choice(img_list)
            card_status = 'had' if join_card_check(user_had_cards, reap_img) else 'new'
            card_dict[card_status].append(reap_img)
            pray_count -= 20
            hard_card_num += 1 if card_status == "new" else 0
            card += 1
    text = f"祈愿{num}次结果如下：\r"
    if had_card := card_dict['had']:
        text += f"获取重复传承卡片{len(had_card)}张如下：\r{'、'.join(set(had_card))}\r"
        text += f"已转化为{len(had_card) * 600}分钟余剩虚神界内闭关时间\r"
    if new_card := card_dict['new']:
        text += f"获取新传承卡片:\r{'、'.join(new_card)}\r"
    all_time = (get_card * 45) + (len(had_card) * 600) + (break_num * 600)
    text += f"共鸣数量：{get_card}, 获得{get_card * 45}分钟虚神界内闭关时间\r"
    if break_num:
        text += f"溢出：{break_num}张传承卡片, 获得{break_num * 600}分钟虚神界内闭关时间\r"
    text += f"累计共获得{all_time}分钟({all_time / 60}小时)余剩虚神界内闭关时间!\r"
    await xiuxian_impart.add_impart_exp_day(all_time, user_id)
    await xiuxian_impart.update_pray_card_num(pray_count, user_id, 2)
    await xiuxian_impart.update_user_cards(user_id, user_had_cards)
    msg = main_md(msg, text,
                  '传承背包', '传承背包',
                  '传承帮助', '传承帮助',
                  '虚神界祈愿', '虚神界对决',
                  '继续祈愿', '传承祈愿')
    await re_impart_data(user_id)
    await bot.send(event=event, message=msg)
    await impart_draw.finish()


@impart_draw_fast.handle(parameterless=[Cooldown(cd_time=5)])
async def impart_draw_fast_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """传承抽卡"""

    user_info = await check_user(event)
    user_id = user_info['user_id']
    arg = args.extract_plain_text()
    num = get_num_from_str(arg)
    num = int(num[0]) if num else 1
    impart_data_draw = await impart_check(user_id)
    fail_msg = [f"道友思恋结晶不足{num}个！！无法进行{num}次抽卡!"] if impart_data_draw.get('stone_num', 0) < num else []
    fail_msg += [f"{num}次抽卡也太多拉！！1000次1000次慢慢来吧！！"] if 1000 < num else []
    if fail_msg:
        await bot.send(event=event, message='\r'.join(fail_msg))
        await impart_draw_fast.finish()
    card = 0
    img_list = impart_data_json.data_all_keys()
    user_impart_data = await xiuxian_impart.get_user_info_with_id(user_id)
    wish_count = user_impart_data.get('wish')
    msg = f"道友{user_info['user_name']}的传承抽卡"
    await xiuxian_impart.update_stone_num(num, user_id, 2)
    cards = impart_data_draw['cards']
    user_had_cards = json.loads(cards) if cards else []
    hard_card_num = len(user_had_cards)
    if hard_card_num == 106:
        all_time = 180 * num
        text = f'传承卡片溢出！\r已转化为{all_time}分钟虚神界内闭关时间'
        await xiuxian_impart.add_impart_exp_day(all_time, user_id)
        msg = main_md(msg, text,
                      '传承背包', '传承背包',
                      '传承帮助', '传承帮助',
                      '虚神界对决', '虚神界对决',
                      '继续抽卡', '传承抽卡')
        await bot.send(event=event, message=msg)
        await impart_draw_fast.finish()
    for i in range(num):
        # 抽 num * 10 次
        if get_rank_plus(wish_count):
            card += 1
            wish_count = 0
        else:
            wish_count += 10
    card_dict = {'had': [], 'new': []}
    for _ in range(card):
        reap_img = random.choice(img_list)
        card_status = 'had' if join_card_check(user_had_cards, reap_img) else 'new'
        card_dict[card_status].append(reap_img)
    text = ''
    if had_card := card_dict['had']:
        text += f"获取重复传承卡片{'、'.join(set(had_card))}\r"
        text += f"已转化为{len(had_card) * 45}分钟余剩虚神界内闭关时间\r"
    if new_card := card_dict['new']:
        text += f"获取新传承卡片{'、'.join(set(new_card))}\r"
    all_time = (num * 50) - (card * 5) + (len(had_card) * 45)
    all_card = '\r'.join(set(operator.add(new_card, had_card)))
    text += f"累计共获得{all_time}分钟余剩虚神界内闭关时间!\r"
    text += f"抽卡{10 * num}次结果如下：\r"
    text += f"{all_card}5分钟虚神界闭关时间 X{((num * 10) - card)}"
    await xiuxian_impart.add_impart_exp_day(all_time, user_id)
    await xiuxian_impart.update_impart_wish(wish_count, user_id)
    await xiuxian_impart.update_user_cards(user_id, user_had_cards)
    msg = main_md(
        msg, text,
        '传承背包', '传承背包',
        '继续抽卡', '传承抽卡',
        '虚神界对决', '虚神界对决',
        '传承帮助', '传承帮助')
    await re_impart_data(user_id)
    await bot.send(event=event, message=msg)
    await impart_draw_fast.finish()


@impart_back.handle(parameterless=[Cooldown()])
async def impart_back_(bot: Bot, event: GroupMessageEvent):
    """传承背包"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    impart_data_draw = await impart_check(user_id)
    if impart_data_draw is None:
        msg = f"发生未知错误，多次尝试无果请找晓楠！"
        await bot.send(event=event, message=msg)
        await impart_back.finish()

    msg = ""
    cards = impart_data_draw['cards']
    user_had_cards = json.loads(cards) if cards else []
    msg += (f"--道友{user_info['user_name']}的传承物资--\r"
            f"思恋结晶：{impart_data_draw['stone_num']}颗\r"
            f"祈愿结晶：{impart_data_draw['pray_stone_num']}颗\r"
            f"抽卡次数：{impart_data_draw['wish']}/90次\r"
            f"共鸣进度：{impart_data_draw['pray_card_num']}/20\r"
            f"传承卡图数量：{len(user_had_cards)}/106\r"
            f"余剩虚神界内闭关时间：{impart_data_draw['exp_day']}分钟\r")
    text = (f"--道友{user_info['user_name']}的传承总属性--\r"
            f"攻击提升:{int(impart_data_draw['impart_atk_per'] * 100)}%\r"
            f"气血提升:{int(impart_data_draw['impart_hp_per'] * 100)}%\r"
            f"真元提升:{int(impart_data_draw['impart_mp_per'] * 100)}%\r"
            f"会心提升：{int(impart_data_draw['impart_know_per'] * 100)}%\r"
            f"会心伤害提升：{int(impart_data_draw['impart_burst_per'] * 100)}%\r"
            f"闭关经验提升：{int(impart_data_draw['impart_exp_up'] * 100)}%\r"
            f"炼丹收获数量提升：{impart_data_draw['impart_mix_per']}颗\r"
            f"灵田收取数量提升：{impart_data_draw['impart_reap_per']}颗\r"
            f"每日双修次数提升：{impart_data_draw['impart_two_exp']}次\r"
            f"boss战攻击提升:{int(impart_data_draw['boss_atk'] * 100)}%\r"
            f"道友拥有的传承卡片如下:\r")

    text += "\r".join(user_had_cards)
    msg = main_md(msg, text, '传承卡图 【卡图名称】', '传承卡图', '传承抽卡', '传承抽卡', '虚神界对决', '虚神界对决',
                  '传承帮助', '传承帮助')
    await bot.send(event=event, message=msg)
    await impart_back.finish()


@re_impart_load.handle(parameterless=[Cooldown()])
async def re_impart_load_(bot: Bot, event: GroupMessageEvent):
    """加载传承数据"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    impart_data_draw = await impart_check(user_id)
    if impart_data_draw is None:
        msg = f"发生未知错误，多次尝试无果请找晓楠！"
        await bot.send(event=event, message=msg)
        await re_impart_load.finish()
    # 更新传承数据
    info = await re_impart_data(user_id)
    if info:
        msg = f"传承数据加载完成！"
    else:
        msg = f"传承数据加载失败！"
    await bot.send(event=event, message=msg)
    await re_impart_load.finish()


@impart_info.handle(parameterless=[Cooldown()])
async def impart_info_(bot: Bot, event: GroupMessageEvent):
    """传承信息"""

    user_info = await check_user(event)

    user_id = user_info['user_id']
    impart_data_draw = await impart_check(user_id)
    if impart_data_draw is None:
        msg = f"发生未知错误，多次尝试无果请找晓楠！"
        await bot.send(event=event, message=msg)
        await impart_info.finish()
    cards = impart_data_draw['cards']
    user_had_cards = json.loads(cards) if cards else []
    msg = f"""--道友{user_info['user_name']}的传承物资--
思恋结晶：{impart_data_draw['stone_num']}颗
抽卡次数：{impart_data_draw['wish']}/90次
传承卡图数量：{len(user_had_cards)}/106
余剩虚神界内闭关时间：{impart_data_draw['exp_day']}分钟
    """
    await bot.send(event=event, message=msg)
    await impart_info.finish()
