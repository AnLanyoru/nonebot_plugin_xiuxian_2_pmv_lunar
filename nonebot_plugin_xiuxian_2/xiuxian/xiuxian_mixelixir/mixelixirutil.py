import random
from collections import Counter
from random import shuffle

from ..xiuxian_utils.item_json import items

# "-1": "性寒",
# "0": "性平",
# "1": "性热",
# "2": "生息",
# "3": "养气",
# "4": "炼气",
# "5": "聚元",
# "6": "凝神",
herb_value_def = {
    -1: "性寒",
    0: "性平",
    1: "性热",
    2: "生息",
    3: "养气",
    4: "炼气",
    5: "聚元",
    6: "凝神"}


async def tiaohe(zhuyao_info, zhuyao_num, yaoyin_info, yaoyin_num):
    _zhuyao = zhuyao_info['主药']['h_a_c']['type'] * zhuyao_info['主药']['h_a_c']['power'] * zhuyao_num
    _yaoyin = yaoyin_info['药引']['h_a_c']['type'] * yaoyin_info['药引']['h_a_c']['power'] * yaoyin_num

    return await absolute(_zhuyao + _yaoyin) > yonhudenji


def get_herb_info(herb_id):
    real_herb_info = items.get_data_by_item_id(herb_id)
    herb_info = {
        '药名': real_herb_info['name'],
        '主药': {
            '冷热': real_herb_info['主药']['h_a_c']['type'] * real_herb_info['主药']['h_a_c']['power'],
            '药性': herb_value_def[real_herb_info['主药']['type']],
            '药力': real_herb_info['主药']['power']},
        '药引': {
            '冷热': real_herb_info['药引']['h_a_c']['type'] * real_herb_info['药引']['h_a_c']['power']},
        '辅药': {
            '药性': herb_value_def[real_herb_info['辅药']['type']],
            '药力': real_herb_info['辅药']['power']}}
    return herb_info


class AlchemyFurnace:
    def __init__(self):
        # 丹炉属性
        self.name: str = "无"
        self.fire_sub: int = 0
        self.herb_save: int = 0

        # 丹炉状态
        self.fire_value: float = 0
        self.herb_power: dict = {
            "生息": 0,
            "养气": 0,
            "炼气": 0,
            "聚元": 0,
            "凝神": 0}

    def get_sum_herb_power(self) -> int:
        return sum(self.herb_power.keys())

    def get_herb_power_rank(self):
        return sorted(self.herb_power, key=lambda x: self.herb_power[x], reverse=True)

    def get_main_herb_power(self):
        if self.get_sum_herb_power():
            herb_power_rank = self.get_herb_power_rank()
            return herb_power_rank[:1]
        else:
            return ["无"]

    def get_herb_power_msg(self):
        had_herb_power = [f"{herb_power_type}: {self.herb_power[herb_power_type]}"
                          for herb_power_type in self.get_herb_power_rank()
                          if self.herb_power[herb_power_type] > 0]
        if not had_herb_power:
            return "当前无药力"
        return "\r".join(had_herb_power)

    def get_state_msg(self) -> str:

        msg = (f"丹炉状态：\r"
               f"丹炉名称：{self.name}\r"
               f"丹火：普通火焰\r"
               f"炉温：{self.fire_value}\r"
               f"炉内总药力：{self.get_sum_herb_power()}\r"
               f"炉内主导药力：{self.get_main_herb_power()}\r"
               f"药力详情：\r"
               f"{self.get_herb_power_msg()}")

        return msg

    def input_herb_as_main(self, user_fire_control, user_herb_knowledge, herb_id, herb_num) -> str:
        herb_info = get_herb_info(herb_id)
        herb_info_main = herb_info['主药']
        herb_fire_charge = herb_info_main['冷热'] * herb_num
        herb_type = herb_info_main['药性']
        add_herb_power = herb_info_main['药力'] * herb_num

        # 丹炉温度变化
        fire_min_param = (int(user_fire_control / (user_fire_control + 5000) * 20)
                          + int(user_fire_control / (user_fire_control + 500) * 10)
                          + int(user_fire_control / (user_fire_control + 100) * 20))

        fire_max_param = (int(user_fire_control / (user_fire_control + 500000) * 20)
                          + int(user_fire_control / (user_fire_control + 50000) * 20)
                          + int(user_fire_control / (user_fire_control + 5000) * 20)
                          + int(user_fire_control / (user_fire_control + 500) * 30))

        base_fire_charge = random.randint(50 - fire_min_param, 100 - fire_max_param) + 100

        # 丹炉药性变化
        power_keep_max_param = (int(user_herb_knowledge / (user_herb_knowledge + 5000) * 20)
                                + int(user_herb_knowledge / (user_herb_knowledge + 500) * 10)
                                + int(user_herb_knowledge / (user_herb_knowledge + 100) * 20))

        power_keep_min_param = (int(user_herb_knowledge / (user_herb_knowledge + 500000) * 20)
                                + int(user_herb_knowledge / (user_herb_knowledge + 50000) * 20)
                                + int(user_herb_knowledge / (user_herb_knowledge + 5000) * 20)
                                + int(user_herb_knowledge / (user_herb_knowledge + 500) * 30))
        herb_power_keep = random.randint(10 + power_keep_min_param, 50 + power_keep_max_param)
        herb_power_keep_present = round(herb_power_keep / 100, 2)
        herb_fire_charge *= herb_power_keep_present
        add_herb_power *= herb_power_keep_present
        self.herb_power[herb_type] += add_herb_power
        self.fire_value += base_fire_charge + herb_fire_charge
        result = '加入'
        return result


mix_config = items.get_data_by_item_type(['合成丹药'])
mix_configs = {}
for k, v in mix_config.items():
    mix_configs[k] = v['elixir_config']

yonhudenji = 0
Llandudno_info = {
    "max_num": 10,
    "rank": 20
}


async def check_mix(elixir_config):
    is_mix = False
    l_id = []
    # mix_configs = await get_mix_config()
    for k, v in mix_configs.items():  # 这里是丹药配方
        type_list = []
        for ek, ev in elixir_config.items():  # 这是传入的值判断
            # 传入的丹药config
            type_list.append(ek)
        formula_list = []
        for vk, vv in v.items():  # 这里是每个配方的值
            formula_list.append(vk)
        if sorted(type_list) == sorted(formula_list):  # key满足了
            flag = False
            for typek in type_list:
                if elixir_config[typek] >= v[typek]:
                    flag = True
                    continue
                else:
                    flag = False
                    break
            if flag:
                l_id.append(k)

            continue
        else:
            continue
    id = 0
    if l_id:
        is_mix = True
        id_config = {}
        for id in l_id:
            for k, v in mix_configs[id].items():
                id_config[id] = v
                break
        id = sorted(id_config.items(), key=lambda x: x[1], reverse=True)[0][0]  # 选出最优解

    return is_mix, id


async def get_mix_elixir_msg(yaocai):
    mix_elixir_msg = {}
    num = 0
    for k, v in yaocai.items():  # 这里是用户所有的药材dict
        i = 1
        while i <= v['num'] and i <= 5:  # 尝试第一个药材为主药
            # _zhuyao = v['主药']['h_a_c']['type'] * v['主药']['h_a_c']['power'] * i
            for kk, vv in yaocai.items():
                if kk == k:  # 相同的药材不能同时做药引
                    continue
                o = 1
                while o <= vv['num'] and o <= 5:
                    # _yaoyin = vv['药引']['h_a_c']['type'] * vv['药引']['h_a_c']['power'] * o
                    if await tiaohe(v, i, vv, o):  # 调和失败
                        # if await absolute(_zhuyao + _yaoyin) > yonhudenji:#调和失败
                        o += 1
                        continue
                    else:
                        elixir_config = {}
                        zhuyao_type = str(v['主药']['type'])
                        zhuyao_power = v['主药']['power'] * i
                        elixir_config[zhuyao_type] = zhuyao_power
                        for kkk, vvv in yaocai.items():
                            p = 1
                            # 尝试加入辅药
                            while p <= vvv['num'] and p <= 5:
                                fuyao_type = str(vvv['辅药']['type'])
                                fuyao_power = vvv['辅药']['power'] * p
                                elixir_config = {}
                                zhuyao_type = str(v['主药']['type'])
                                zhuyao_power = v['主药']['power'] * i
                                elixir_config[zhuyao_type] = zhuyao_power
                                elixir_config[fuyao_type] = fuyao_power
                                # print(elixir_config)         
                                is_mix, id_ = await check_mix(elixir_config)
                                if is_mix:  # 有可以合成的
                                    if i + o + p <= Llandudno_info["max_num"]:
                                        # 判断背包里药材是否足够(同个药材多种类型)
                                        if len({v["name"], vv["name"], vvv["name"]}) != 3:
                                            num_dict = Counter(
                                                [*[v["name"]] * i, *[vv["name"]] * o, *[vvv["name"]] * p])
                                            if any(num_dict[yao["name"]] > yao["num"] for yao in [v, vv, vvv]):
                                                p += 1
                                                continue

                                        mix_elixir_msg[num] = {}
                                        mix_elixir_msg[num]['id'] = id_
                                        mix_elixir_msg[num]['配方'] = elixir_config
                                        mix_elixir_msg[num][
                                            '配方简写'] = f"主药{v['name']}{i}药引{vv['name']}{o}辅药{vvv['name']}{p}"
                                        mix_elixir_msg[num]['主药'] = v['name']
                                        mix_elixir_msg[num]['主药_num'] = i
                                        mix_elixir_msg[num]['主药_level'] = v['level']
                                        mix_elixir_msg[num]['药引'] = vv['name']
                                        mix_elixir_msg[num]['药引_num'] = o
                                        mix_elixir_msg[num]['药引_level'] = vv['level']
                                        mix_elixir_msg[num]['辅药'] = vvv['name']
                                        mix_elixir_msg[num]['辅药_num'] = p
                                        mix_elixir_msg[num]['辅药_level'] = vvv['level']
                                        num += 1
                                        p += 1
                                        continue
                                    else:
                                        p += 1
                                        continue
                                else:
                                    p += 1
                                    continue
                            continue
                    o += 1
            i += 1
    temp_dict = {}
    temp_id_list = []
    finall_mix_elixir_msg = {}
    if mix_elixir_msg == {}:
        return finall_mix_elixir_msg
    for k, v in mix_elixir_msg.items():
        temp_id_list.append(v['id'])
    temp_id_list = set(temp_id_list)
    for id_ in temp_id_list:
        temp_dict[id_] = {}
        for k, v in mix_elixir_msg.items():
            if id_ == v['id']:
                temp_dict[id_][k] = v['主药_num'] + v['药引_num'] + v['辅药_num']
            else:
                continue
        id_ = sorted(temp_dict[id_].items(), key=lambda x: x[1])[0][0]
        finall_mix_elixir_msg[id_] = {}
        finall_mix_elixir_msg[id_]['id'] = mix_elixir_msg[id_]['id']
        finall_mix_elixir_msg[id_]['配方'] = mix_elixir_msg[id_]

    return finall_mix_elixir_msg


async def absolute(x):
    if x >= 0:
        return x
    else:
        return -x


async def tiaohe(zhuyao_info, zhuyao_num, yaoyin_info, yaoyin_num):
    _zhuyao = zhuyao_info['主药']['h_a_c']['type'] * zhuyao_info['主药']['h_a_c']['power'] * zhuyao_num
    _yaoyin = yaoyin_info['药引']['h_a_c']['type'] * yaoyin_info['药引']['h_a_c']['power'] * yaoyin_num

    return await absolute(_zhuyao + _yaoyin) > yonhudenji


async def make_dict(old_dict):
    old_dict_key = list(old_dict.keys())
    shuffle(old_dict_key)
    if len(old_dict_key) >= 25:
        old_dict_key = old_dict_key[:25]
    new_dic = {}
    for key in old_dict_key:
        new_dic[key] = old_dict.get(key)
    return new_dic
