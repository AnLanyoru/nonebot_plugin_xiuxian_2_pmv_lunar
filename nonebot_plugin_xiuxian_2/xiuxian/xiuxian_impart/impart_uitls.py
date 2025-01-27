import numpy

from .impart_data import impart_data_json
from ..xiuxian_utils.xiuxian2_handle import xiuxian_impart


# 替换模块


def random_int():
    return numpy.random.randint(low=0, high=10000, size=None, dtype='l')


# 抽卡概率来自https://www.bilibili.com/read/cv10468091
# 角色抽卡概率
def character_probability(count):
    count += 1
    if count <= 73:
        ret = 60
    else:
        ret = 60 + 600 * (count - 73)
    return ret


async def get_rank(user_id):
    impart_data = await xiuxian_impart.get_user_info_with_id(user_id)
    value = random_int()
    num = int(impart_data['wish'])
    for x in range(num, num + 10):
        index_5 = character_probability(x)
        if value <= index_5:
            return True
        if x >= 89:
            return True
    return False


def get_rank_plus(wish_count):
    value = random_int()
    num = int(wish_count)
    for x in range(num, num + 10):
        index_5 = character_probability(x)
        if value <= index_5:
            return True
        if x >= 89:
            return True
    return False


def join_card_check(card_list: list, card_pre_join: str) -> bool:
    if card_pre_join in card_list:
        return True
    card_list.append(card_pre_join)
    return False

async def impart_check(user_id):
    if await xiuxian_impart.get_user_info_with_id(user_id) is None:
        await xiuxian_impart.impart_create_user(user_id)
        return await xiuxian_impart.get_user_info_with_id(user_id)
    else:
        return await xiuxian_impart.get_user_info_with_id(user_id)


async def re_impart_data(user_id):
    list_tp = await xiuxian_impart.get_user_impart_cards(user_id)
    if list_tp is None:
        return False
    else:
        all_data = impart_data_json.data_all_()
        impart_two_exp = 0
        impart_exp_up = 0
        impart_atk_per = 0
        impart_hp_per = 0
        impart_mp_per = 0
        boss_atk = 0
        impart_know_per = 0
        impart_burst_per = 0
        impart_mix_per = 0
        impart_reap_per = 0
        for x in list_tp:
            if all_data[x]["type"] == "impart_two_exp":
                impart_two_exp = impart_two_exp + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_exp_up":
                impart_exp_up = impart_exp_up + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_atk_per":
                impart_atk_per = impart_atk_per + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_hp_per":
                impart_hp_per = impart_hp_per + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_mp_per":
                impart_mp_per = impart_mp_per + all_data[x]["vale"]
            elif all_data[x]["type"] == "boss_atk":
                boss_atk = boss_atk + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_know_per":
                impart_know_per = impart_know_per + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_burst_per":
                impart_burst_per = impart_burst_per + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_mix_per":
                impart_mix_per = impart_mix_per + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_reap_per":
                impart_reap_per = impart_reap_per + all_data[x]["vale"]
            else:
                pass
        await xiuxian_impart.update_impart_all_buff(
            impart_hp_per,
            impart_atk_per,
            impart_mp_per,
            impart_exp_up,
            boss_atk,
            impart_know_per,
            impart_burst_per,
            impart_mix_per,
            impart_reap_per,
            impart_two_exp,
            user_id)
        return True
