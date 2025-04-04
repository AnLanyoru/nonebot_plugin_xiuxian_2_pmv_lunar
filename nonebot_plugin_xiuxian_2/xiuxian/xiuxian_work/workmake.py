import random

from ..xiuxian_config import convert_rank
from ..xiuxian_data.work_data.暗杀 import work_data_kill
from ..xiuxian_data.work_data.灵材 import work_data_plant
from ..xiuxian_data.work_data.等级奖励稿 import level_prise_data
from ..xiuxian_data.work_data.镇妖 import work_data_fight
from ..xiuxian_utils.item_json import items as item_s
from ..xiuxian_utils.other_set import OtherSet


class WorkMsg:
    def __init__(self, user_id):
        self.user = user_id
        self.time = 0
        self.msg = 0
        self.world = []


def workmake(work_level, exp, user_level):
    if work_level == '求道者':
        work_level = '求道者'
    else:
        work_level = work_level[:3]  # 取境界前3位，补全初期、中期、圆满任务可不取

    yaocai_data = work_data_plant
    levelpricedata = level_prise_data
    ansha_data = work_data_kill
    zuoyao_data = work_data_fight
    work_json = {}
    work_list = [yaocai_data[work_level], ansha_data[work_level], zuoyao_data[work_level]]
    i = 1
    for w in work_list:
        work_name_list = []
        for k, v in w.items():
            work_name_list.append(k)
        work_name = random.choice(work_name_list)
        work_info = w[work_name]
        level_price_data = levelpricedata[work_level][work_info['level']]
        rate, is_out = countrate(exp, level_price_data["needexp"])
        success_msg = work_info['succeed']
        fail_msg = work_info['fail']
        item_type = get_random_item_type()
        item_id = item_s.get_random_id_list_by_rank_and_item_type(convert_rank(user_level)[0], item_type)
        if not item_id:
            item_id = 0
        else:
            item_id = random.choice(item_id)
        if work_name in work_json:
            work_name = "和凌云一起" + work_name
        work_json[work_name] = [rate, level_price_data["award"], int(level_price_data["time"] * is_out), item_id,
                                success_msg, fail_msg]
        i += 1
    return work_json


def get_random_item_type():
    type_rate = {
        "功法": {
            "type_rate": 500,
        },
        "神通": {
            "type_rate": 50,
        },
        "药材": {
            "type_rate": 500,
        }
    }
    temp_dict = {}
    for i, v in type_rate.items():
        try:
            temp_dict[i] = v["type_rate"]
        except:
            continue
    key = [OtherSet().calculated(temp_dict)]
    return key


def countrate(exp, needexp):
    rate = int(exp / needexp * 100)
    is_out = 1
    if rate >= 100:
        tp = 1
        flag = True
        while flag:
            r = exp / needexp * 100
            if r > 100:
                tp += 1
                exp /= 1.5
            else:
                flag = False

        rate = 100
        is_out = float(1 - tp * 0.05)
        if is_out < 0.5:
            is_out = 0.5
    return rate, round(is_out, 2)
