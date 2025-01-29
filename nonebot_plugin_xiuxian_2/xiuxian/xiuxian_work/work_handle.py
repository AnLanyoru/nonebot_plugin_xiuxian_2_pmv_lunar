import random

from .work_database import save_work_info, read_work_info
from .workmake import workmake
from ..xiuxian_utils.clean_utils import number_to
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.xiuxian2_handle import sql_message


async def work_handle(key, work_name=None, level="求道者", exp=None, user_id=None, work_data=None):
    """悬赏令获取"""
    if key == 0:  # 如果没有获取过，则返回悬赏令
        data = workmake(level, exp, (await sql_message.get_user_info_with_id(user_id))['level'])
        get_work_list = []
        for k, v in data.items():
            if v[3] == 0:
                item_msg = '!'
            else:
                item_info = items.get_data_by_item_id(v[3])
                item_msg = f"可能额外获得:🎁{item_info['level']}:{item_info['name']}!"
            get_work_list.append([k, v[0], v[1], v[2], item_msg])
        await save_work_info(user_id, data)
        return get_work_list

    elif key == 2:  # 如果是结算，则获取结果

        bigsuc = False
        if work_data[work_name][0] >= 100:
            bigsuc = True

        success_msg = work_data[work_name][4]
        fail_msg = work_data[work_name][5]
        item_id = work_data[work_name][3]
        await save_work_info(user_id, {})

        if random.randint(1, 100) <= work_data[work_name][0]:
            return success_msg, work_data[work_name][1], True, item_id, bigsuc
        else:
            return fail_msg, int(work_data[work_name][1] / 2), False, 0, bigsuc


def get_work_msg(work_):
    msg = f"{work_[0]}\r完成机率🎲{work_[1]}%\r基础报酬💗{number_to(work_[2])}修为,预计需⏳{work_[3]}分钟\r{work_[4]}\r"
    return msg


def change_data_to_msg(work_data):
    work_info = []
    for k, v in work_data.items():
        if v[3] == 0:
            item_msg = '!'
        else:
            item_info = items.get_data_by_item_id(v[3])
            item_msg = f"可能额外获得:🎁{item_info['level']}:{item_info['name']}!"
        work_info.append([k, v[0], v[1], v[2], item_msg])

    work_list = []
    work_msg = []
    for i in work_info:
        work_list.append([i[0], i[3]])
        work_msg.append(get_work_msg(i))
    return work_msg, work_list
