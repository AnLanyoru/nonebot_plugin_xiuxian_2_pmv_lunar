import random

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent
)
from nonebot.params import CommandArg
from ..xiuxian_utils.clean_utils import simple_md
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import check_user
from ..xiuxian_utils.xiuxian2_handle import sql_message, xiuxian_impart

NUM_LIST = [3, 3, 3, 3, 6, 6, 6, 8, 8, 10]


def get_num_new_year():
    return random.choice(NUM_LIST)


async def send_impart_stone(user_id):
    num = get_num_new_year()
    await xiuxian_impart.update_stone_num(impart_num=num, user_id=user_id, type_=1)
    return f'思恋结晶 {num}个', {}


async def send_buff_elixir(user_id):
    num = get_num_new_year()
    elixir_list = [2035, 2026, 2015]
    elixir_id = random.choice(elixir_list)
    elixir_info = items.get_data_by_item_id(elixir_id)
    elixir_name = elixir_info['name']
    return f"{elixir_name} {num}个", {elixir_id: num}


async def send_stam_tool(user_id):
    """复元水 3-10个"""
    num = get_num_new_year()
    item_id = 610004
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


async def send_work(user_id):
    """悬赏衙令 3-10个"""
    num = get_num_new_year()
    item_id = 640001
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


async def send_money(user_id):
    """金元宝 3-10个"""
    num = random.choice([3, 3, 3, 3, 3, 3, 6, 6, 8, 10])
    item_id = 990001
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


async def send_jiao_zi(user_id):
    """饺子 3-10个"""
    num = get_num_new_year()
    item_id = 25012
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


gift_list = {'思恋结晶': send_impart_stone,
             '增益丹药': send_buff_elixir,
             '复元水': send_stam_tool,
             '悬赏衙令': send_work,
             '金元宝': send_money,
             '饺子': send_jiao_zi}

new_year_gift_get = on_command("使用二零二五新春福包", priority=1, permission=GROUP, block=True)


@new_year_gift_get.handle(parameterless=[Cooldown(cd_time=5)])
async def new_year_gift_get_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """二零二五新春福包"""

    user_info = await check_user(event)
    user_id = user_info['user_id']
    user_name = user_info['user_name']
    new_year_gift_info = await sql_message.get_item_by_good_id_and_user_id(user_id, 700001)
    if not new_year_gift_info:
        msg = f"道友没有二零二五新春福包呢！！\r"
        msg = simple_md(msg,
                        "查看福包奖励", "查二零二五新春福包",
                        "\r —— 查看所有该福包内含奖励")
        await bot.send(event=event, message=msg)
        await new_year_gift_get.finish()
    if (gift_num := new_year_gift_info.get('goods_num')) <= 0:
        msg = f"道友的二零二五新春福包不够呢！！\r"
        msg = simple_md(msg, "查看福包奖励",
                        "查二零二五新春福包",
                        "\r —— 查看所有该福包内含奖励")
        await bot.send(event=event, message=msg)
        await new_year_gift_get.finish()

    all_gift = list(gift_list.keys())
    random.shuffle(all_gift)
    msg_list = []
    item_send = {}
    for gift_type in all_gift[:3]:
        msg_per, item_dict = await gift_list[gift_type](user_id)
        item_send.update(item_dict)
        msg_list.append(msg_per)
    await sql_message.send_item(user_id, item_send, 1)
    await sql_message.update_back_j(user_id, 700001, 1, 2)
    msg = f"恭喜{user_name}道友打开福包获取了以下奖励：\r" + '\r'.join(msg_list) + '\r'
    msg = simple_md(msg,
                    f"继续拆福袋(余剩{gift_num - 1})",
                    "使用二零二五新春福包",
                    "！！")
    await bot.send(event=event, message=msg)
    await new_year_gift_get.finish()
