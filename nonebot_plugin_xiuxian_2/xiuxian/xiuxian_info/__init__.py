import os
from base64 import b64encode
from io import BytesIO
from pathlib import Path

from PIL import Image
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

from .draw_user_info import draw_user_info_img
from .send_image_tool import convert_img
from ..user_data_handle import UserBuffHandle
from ..xiuxian_data.data.境界_data import level_data
from ..xiuxian_data.data.宗门玩法配置_data import sect_config_data
from ..xiuxian_data.data.突破概率_data import break_rate
from ..xiuxian_utils.clean_utils import get_strs_from_str, simple_md
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.other_set import OtherSet
from ..xiuxian_utils.utils import (
    check_user, number_to
)
from ..xiuxian_utils.xiuxian2_handle import (
    sql_message, UserBuffDate
)

xiuxian_message = on_command("我的修仙信息", aliases={"我的存档", "我的信息", "存档", "修仙信息"}, priority=23,
                             permission=GROUP, block=True)
pic_test = on_command("测试图片", aliases={"图片测试"}, priority=23, permission=SUPERUSER, block=True)


def img2b64(out_img) -> str:
    """ 将图片转换为base64 """
    buf = BytesIO()
    out_img.save(buf, format="PNG")
    base64_str = "base64://" + b64encode(buf.getvalue()).decode()
    return base64_str


img_path = Path(f"{os.getcwd()}/data/xiuxian/image")


@pic_test.handle(parameterless=[Cooldown()])
async def impart_img_(bot: Bot, event: GroupMessageEvent):
    # 这里曾经是风控模块，但是已经不再需要了
    img = img_path / f"background.png"
    img_r = Image.open(img)
    img_r = img2b64(img_r)
    await bot.send(event=event, message=MessageSegment.image(img_r))
    await pic_test.finish()


@xiuxian_message.handle(parameterless=[Cooldown()])
async def xiuxian_message_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """我的修仙信息"""
    # 这里曾经是风控模块，但是已经不再需要了
    args = args.extract_plain_text()
    args = get_strs_from_str(args)
    if args:
        args = args[0]
    else:
        args = None

    user_info = await check_user(event)

    user_id = user_info['user_id']
    user_info = await sql_message.get_user_real_info(user_id)
    user_name = user_info['user_name']
    user_num = user_info['id']
    rank = await sql_message.get_exp_rank(user_id)
    user_rank = int(rank[0])
    stone = await sql_message.get_stone_rank(user_id)
    user_stone = int(stone[0])

    if user_name:
        pass
    else:
        user_name = f"无名氏(发送指令 改头换面 更新)"

    level_rate = await sql_message.get_root_rate(user_info['root_type'])  # 灵根倍率
    realm_rate = level_data[user_info['level']]["spend"]  # 境界倍率
    sect_id = user_info['sect_id']
    if sect_id:
        sect_info = await sql_message.get_sect_info(sect_id)
        sectmsg = sect_info['sect_name']
        sectzw = sect_config_data[f"{user_info['sect_position']}"]["title"]
    else:
        sectmsg = f"无宗门"
        sectzw = f"无"

    # 判断突破的修为
    list_all = len(OtherSet().level) - 1
    now_index = OtherSet().level.index(user_info['level'])
    if list_all == now_index:
        exp_meg = f"位面至高"
    else:
        is_updata_level = OtherSet().level[now_index + 1]
        need_exp = await sql_message.get_level_power(is_updata_level)
        get_exp = need_exp - user_info['exp']
        if get_exp > 0:
            exp_meg = f"还需{number_to(get_exp)}修为可突破！"
        else:
            exp_meg = f"可突破！"

    user_buff_data = UserBuffDate(user_id)
    user_main_buff_date = await user_buff_data.get_user_main_buff_data()
    user_sub_buff_date = await user_buff_data.get_user_sub_buff_data()
    user_sec_buff_date = await user_buff_data.get_user_sec_buff_data()
    user_weapon_data = await user_buff_data.get_user_weapon_data()
    user_armor_data = await user_buff_data.get_user_armor_buff_data()
    main_buff_name = f"无"
    sub_buff_name = f"无"
    sec_buff_name = f"无"
    weapon_name = f"无"
    armor_name = f"无"
    if user_main_buff_date is not None:
        main_buff_name = f"{user_main_buff_date['name']}({user_main_buff_date['level']})"
    if user_sub_buff_date is not None:
        sub_buff_name = f"{user_sub_buff_date['name']}({user_sub_buff_date['level']})"
    if user_sec_buff_date is not None:
        sec_buff_name = f"{user_sec_buff_date['name']}({user_sec_buff_date['level']})"
    if user_weapon_data is not None:
        weapon_name = f"{user_weapon_data['name']}({user_weapon_data['level']})"
    if user_armor_data is not None:
        armor_name = f"{user_armor_data['name']}({user_armor_data['level']})"

    user_buff_handle = UserBuffHandle(user_id)
    user_new_equipment_msg = await user_buff_handle.get_new_equipment_msg()

    main_rate_buff = await UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升
    await sql_message.update_last_check_info_time(user_id)  # 更新查看修仙信息时间
    leveluprate = int(user_info['level_up_rate'])  # 用户失败次数加成
    number = main_rate_buff["number"] if main_rate_buff is not None else 0

    if args == "图片版":
        DETAIL_MAP = {
            "道号": f"{user_name}",
            "境界": f"{user_info['level']}",
            "修为": f"{number_to(user_info['exp'])}",
            "灵石": f"{number_to(user_info['stone'])}",
            "战力": f"{number_to(int(user_info['exp'] * level_rate * realm_rate))}",
            "灵根": f"{user_info['root']}({user_info['root_type']}+{int(level_rate * 100)}%)",
            "突破状态": f"{exp_meg}概率：{break_rate.get(user_info['level'], 1) + leveluprate + number}%",
            "攻击力": f"{number_to(user_info['atk'])}，攻修等级{user_info['atkpractice']}级",
            "所在宗门": sectmsg,
            "宗门职位": sectzw,
            "主修功法": main_buff_name,
            "辅修功法": sub_buff_name,
            "副修神通": sec_buff_name,
            "法器": weapon_name,
            "防具": armor_name,
            "注册位数": f"道友是踏入修仙世界的第{int(user_num)}人",
            "修为排行": f"道友的修为排在第{user_rank}位",
            "灵石排行": f"道友的灵石排在第{user_stone}位",
        }
        img_res = await draw_user_info_img(user_id, DETAIL_MAP)
        await bot.send(event=event, message=MessageSegment.image(img_res))
        await xiuxian_message.finish()
    else:
        msg = (f"道号: {user_name}\r"
               f"ID: {user_id}\r"
               f"境界: {user_info['level']}\r"
               f"修为: {number_to(user_info['exp'])}\r"
               f"灵石: {number_to(user_info['stone'])}|{user_info['stone']}\r"
               f"灵根: {user_info['root']}\r"
               f"({user_info['root_type']}+{int(level_rate * 100)}%)\r"
               f"突破状态: {exp_meg} (概率：{break_rate.get(user_info['level'], 1) + leveluprate + number}%)\r"
               f"宗门: {sectmsg} (职位: {sectzw})\r"
               f"功法: {main_buff_name}\r"
               f"辅修: {sub_buff_name}\r"
               f"神通: {sec_buff_name}\r"
               f"法器: {weapon_name}\r"
               f"防具: {armor_name}\r"
               f"法宝: {user_new_equipment_msg['lifebound_treasure']}\r"
               f"秘宝: {user_new_equipment_msg['support_artifact']}\r"
               f"道袍: {user_new_equipment_msg['daoist_robe']}\r"
               f"道靴: {user_new_equipment_msg['daoist_boots']}\r"
               f"内甲: {user_new_equipment_msg['inner_armor']}\r"
               f"灵戒: {user_new_equipment_msg['spirit_ring']}\r")
        msg = simple_md(msg, "查看图片版", "我的修仙信息图片版", "!")
        await bot.send(event=event, message=msg)
        await xiuxian_message.finish()
