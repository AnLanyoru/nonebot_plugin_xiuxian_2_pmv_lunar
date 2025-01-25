from datetime import datetime
from typing import Any, Tuple

from nonebot import on_regex
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    GROUP,
)
from nonebot.params import RegexGroup

from .bank_config import CONFIG as BANK_CONFIG
from ..xiuxian_database.database_connect import database
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import check_user, number_to
from ..xiuxian_utils.xiuxian2_handle import sql_message

bank = on_regex(
    r'^灵庄(存灵石|取灵石|升级会员|信息|结算)?(.*)?',
    priority=9,
    permission=GROUP,
    block=True
)

__bank_help__ = f"""
灵庄帮助信息:
指令：
1：灵庄
 - 查看灵庄帮助信息
2：灵庄存灵石
 - 指令后加存入的金额,获取利息
3：灵庄取灵石
 - 指令后加取出的金额,会先结算利息,再取出灵石
4：灵庄升级会员
 - 灵庄利息倍率与灵庄会员等级有关,升级会员会提升利息倍率
5：灵庄信息
 - 查询自己当前的灵庄信息
6：灵庄结算
 - 结算利息
——tips——
官方群914556251
""".strip()


@bank.handle(parameterless=[Cooldown(at_sender=False)])
async def bank_(bot: Bot, event: GroupMessageEvent, args: Tuple[Any, ...] = RegexGroup()):
    _, user_info, _ = await check_user(event)
    mode = args[0]  # 存灵石、取灵石、升级会员、信息查看
    num = args[1]  # 数值
    if mode is None:
        msg = __bank_help__
        await bot.send(event=event, message=msg)
        await bank.finish()

    if mode == '存灵石' or mode == '取灵石':
        try:
            num = int(num)
            if num <= 0:
                msg = f"请输入正确的金额！"
                await bot.send(event=event, message=msg)
                await bank.finish()
        except ValueError:
            msg = f"请输入正确的金额！"
            await bot.send(event=event, message=msg)
            await bank.finish()
    user_id = user_info['user_id']
    bank_info = await read_user_bank_info(user_id)
    if not bank_info:
        bank_info = await create_user_bank_info(user_id)

    if mode == '存灵石':  # 存灵石逻辑
        if int(user_info['stone']) < num:
            msg = (f"道友所拥有的灵石为{number_to(user_info['stone'])}|{user_info['stone']}枚，"
                   f"金额不足，请重新输入！")
            await bot.send(event=event, message=msg)
            await bank.finish()

        save_max = BANK_CONFIG[bank_info['bank_level']]['save_max']
        now_max = save_max - bank_info['save_stone']

        if num > now_max:
            msg = (f"道友当前灵庄会员等级为{BANK_CONFIG[bank_info['bank_level']]['level']}，"
                   f"可存储的最大灵石为{number_to(save_max)}|{save_max}枚,"
                   f"当前已存{number_to(bank_info['save_stone'])}|{bank_info['save_stone']}枚灵石，"
                   f"可以继续存{number_to(now_max)}|{now_max}枚灵石！")
            await bot.send(event=event, message=msg)
            await bank.finish()

        bank_info, give_stone, time_def = get_give_stone(bank_info)
        user_info_now_stone = int(user_info['stone']) - num
        bank_info['save_stone'] += num
        await sql_message.update_ls(user_id, num, 2)
        await sql_message.update_ls(user_id, give_stone, 1)
        bank_info['save_time'] = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        await save_user_bank_info(user_id, bank_info)
        msg = (f"道友本次结息时间为：{time_def}小时，"
               f"获得灵石：{number_to(give_stone)}|{give_stone}枚!\r"
               f"道友存入灵石{number_to(num)}|{num}枚，"
               f"当前所拥有灵石{number_to(user_info_now_stone + give_stone)}|{user_info_now_stone + give_stone}枚，"
               f"灵庄存有灵石{number_to(bank_info['save_stone'])}|{bank_info['save_stone']}枚")
        await bot.send(event=event, message=msg)
        await bank.finish()

    elif mode == '取灵石':  # 取灵石逻辑
        if int(bank_info['save_stone']) < num:
            msg = (f"道友当前灵庄所存有的灵石为{number_to(bank_info['save_stone'])}|{bank_info['save_stone']}枚，"
                   f"金额不足，请重新输入！")
            await bot.send(event=event, message=msg)
            await bank.finish()

        # 先结算利息
        bank_info, give_stone, time_def = get_give_stone(bank_info)

        user_info_now_stone = int(user_info['stone']) + num + give_stone
        bank_info['save_stone'] -= num
        await sql_message.update_ls(user_id, num + give_stone, 1)
        await save_user_bank_info(user_id, bank_info)
        msg = (f"道友本次结息时间为：{time_def}小时，获得灵石：{number_to(give_stone)}|{give_stone}枚!\r"
               f"取出灵石{number_to(num)}|{num}枚，当前所拥有灵石{number_to(user_info_now_stone)}|{user_info_now_stone}枚，"
               f"灵庄存有灵石{number_to(bank_info['save_stone'])}|{bank_info['save_stone']}枚!")
        await bot.send(event=event, message=msg)
        await bank.finish()

    elif mode == '升级会员':  # 升级会员逻辑
        user_level = bank_info["bank_level"]
        if int(user_level) == int(len(BANK_CONFIG)) - 1:
            msg = f"灵庄分庄已被他人建设！"
            await bot.send(event=event, message=msg)
            await bank.finish()

        if user_level == len(BANK_CONFIG):
            msg = f"道友已经是本灵庄最大的会员啦！"
            await bot.send(event=event, message=msg)
            await bank.finish()
        stone_cost = BANK_CONFIG[user_level]['level_up']
        if int(user_info['stone']) < stone_cost:
            msg = (f"道友所拥有的灵石为{number_to(user_info['stone'])}|{user_info['stone']}枚，"
                   f"当前升级会员等级需求灵石{number_to(stone_cost)}|{stone_cost}枚金额不足，请重新输入！")
            await bot.send(event=event, message=msg)
            await bank.finish()

        await sql_message.update_ls(user_id, stone_cost, 2)
        bank_info['bank_level'] += 1
        await save_user_bank_info(user_id, bank_info)
        msg = (f"道友成功升级灵庄会员等级，消耗灵石{number_to(stone_cost)}|{stone_cost}枚，"
               f"当前为：{BANK_CONFIG[user_level + 1]['level']}，"
               f"灵庄可存有灵石上限{number_to(BANK_CONFIG[user_level + 1]['save_max'])}"
               f"|{BANK_CONFIG[user_level + 1]['save_max']}枚")

        await bot.send(event=event, message=msg)
        await bank.finish()

    elif mode == '信息':  # 查询灵庄信息
        msg = f'''道友的灵庄信息：
已存：{number_to(bank_info['save_stone'])}|{bank_info['save_stone']}灵石
存入时间：{bank_info['save_time']}
灵庄会员等级：{BANK_CONFIG[bank_info['bank_level']]['level']}
当前拥有灵石：{number_to(user_info['stone'])}|{user_info['stone']}
当前等级存储灵石上限：{BANK_CONFIG[bank_info['bank_level']]['save_max']}枚
'''
        await bot.send(event=event, message=msg)
        await bank.finish()

    elif mode == '结算':

        bankinfo, give_stone, time_def = get_give_stone(bank_info)
        await sql_message.update_ls(user_id, give_stone, 1)
        await save_user_bank_info(user_id, bankinfo)
        msg = f"道友本次结息时间为：{time_def}小时，获得灵石：{number_to(give_stone)}|{give_stone}枚！"
        await bot.send(event=event, message=msg)
        await bank.finish()


def get_give_stone(bank_info):
    """获取利息：利息=give_stone,结算时间差=time_def"""
    save_time = bank_info['save_time']  # str
    nowtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # str
    time_def = round((datetime.strptime(nowtime, '%Y-%m-%d %H:%M:%S') -
                      datetime.strptime(save_time, '%Y-%m-%d %H:%M:%S')).total_seconds() / 3600, 2)
    give_stone = int(bank_info['save_stone'] * time_def * BANK_CONFIG[bank_info['bank_level']]['interest'])
    bank_info['save_time'] = nowtime

    return bank_info, give_stone, time_def


async def read_user_bank_info(user_id):
    bank_data = await database.select(
        table='bank_info',
        where={'user_id': user_id},
        need_column=['save_stone', 'save_time', 'bank_level'])
    return bank_data


async def save_user_bank_info(user_id, data):
    await database.update(table='bank_info', where={'user_id': user_id}, **data)


async def create_user_bank_info(user_id):
    data = {'user_id': user_id,
            'save_stone': 0,
            'save_time': str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'bank_level': 1, }
    await database.insert(table='bank_info', **data)
    del data['user_id']
    return data
