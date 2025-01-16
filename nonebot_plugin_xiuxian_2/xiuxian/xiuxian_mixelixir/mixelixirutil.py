import random
from collections import Counter
from random import shuffle

from ..xiuxian_utils.item_json import items

# 药性定义
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


def count_mix_param(user_fire_control=None, user_herb_knowledge=None):
    # 计算丹炉温度变化
    if user_fire_control is not None:
        fire_min_param = (int(user_fire_control / (user_fire_control + 5000) * 5)
                          + int(user_fire_control / (user_fire_control + 500) * 3)
                          + int(user_fire_control / (user_fire_control + 100) * 2))

        fire_max_param = (int(user_fire_control / (user_fire_control + 500000) * 15)
                          + int(user_fire_control / (user_fire_control + 50000) * 15)
                          + int(user_fire_control / (user_fire_control + 5000) * 10)
                          + int(user_fire_control / (user_fire_control + 500) * 10))

        base_fire_change = random.randint(10 - fire_min_param, 50 - fire_max_param) * random.choice([1, -1])
    else:
        base_fire_change = 0

    # 丹炉药性变化
    if user_herb_knowledge is not None:
        power_keep_max_param = (int(user_herb_knowledge / (user_herb_knowledge + 5000) * 20)
                                + int(user_herb_knowledge / (user_herb_knowledge + 500) * 10)
                                + int(user_herb_knowledge / (user_herb_knowledge + 100) * 20))

        power_keep_min_param = (int(user_herb_knowledge / (user_herb_knowledge + 500000) * 20)
                                + int(user_herb_knowledge / (user_herb_knowledge + 50000) * 20)
                                + int(user_herb_knowledge / (user_herb_knowledge + 5000) * 20)
                                + int(user_herb_knowledge / (user_herb_knowledge + 500) * 30))
        herb_power_keep = random.randint(10 + power_keep_min_param, 50 + power_keep_max_param)
    else:
        herb_power_keep = 0

    return base_fire_change, herb_power_keep


def count_fire_control(user_fire_control):
    fire_over_improve = (int(user_fire_control / (user_fire_control + 500000) * 50)
                         + int(user_fire_control / (user_fire_control + 50000) * 50)
                         + int(user_fire_control / (user_fire_control + 5000) * 30)
                         + int(user_fire_control / (user_fire_control + 500) * 30))
    return fire_over_improve


class AlchemyFurnace:
    def __init__(self, alchemy_furnace_id):
        # 丹炉属性
        self.alchemy_furnace_id = alchemy_furnace_id
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

        # 初始化丹炉属性
        alchemy_furnace_info = items.get_data_by_item_id(alchemy_furnace_id)
        self.name: str = alchemy_furnace_info['name']
        self.fire_sub: int = alchemy_furnace_info['buff']
        self.herb_save: int = alchemy_furnace_info['buff']

    def get_sum_herb_power(self) -> int:
        return sum(self.herb_power.values())

    def get_herb_power_rank(self):
        return sorted(self.herb_power, key=lambda x: self.herb_power[x], reverse=True)

    def get_main_herb_power(self):
        if self.get_sum_herb_power():
            herb_power_rank = self.get_herb_power_rank()
            return '、'.join(herb_power_rank[:1])
        else:
            return "无"

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

    def __check_alchemy_furnace_state(self, user_fire_control) -> [str, int]:
        over_fire = self.fire_value - 500
        if over_fire < 500:
            return "丹炉炉温十分平稳", 6
        over_point = abs(over_fire) / (200
                                       + self.fire_sub * 20
                                       + count_fire_control(user_fire_control))
        if over_point > 1.5:
            if over_fire > 0:
                msg = "\r炉温严重超出控制，丹炉发生了爆炸！！"
                safe_level = 0
            else:
                msg = "\r炉温严重过低，丹炉内的药液彻底冷凝了！！"
                safe_level = 1
            for herb_type in self.herb_power:
                self.herb_power[herb_type] *= 0.1 * safe_level
            return msg, safe_level
        elif over_point > 1.2:
            # 20% 超出
            msg = "\r炉温超出控制，药性发生了严重流失！！"
            loss_power = over_point - 1
            if over_fire > 0:
                loss_power *= 2
                msg += f'\r药力蒸发流失了{loss_power * 100}%!!'
            else:
                msg += f'\r药力凝固流失了{loss_power * 100}%!!'
            for herb_type in self.herb_power:
                self.herb_power[herb_type] *= 1 - loss_power
            safe_level = 2
            return msg, safe_level
        elif over_point > 1:
            # 超出
            loss_power = (over_point - 1) / 2 + 0.1
            if over_fire > 0:
                loss_msg = f'\r药力蒸发流失了{loss_power * 100}%!!'
                loss_type = "高"
            else:
                loss_msg = f'\r药力凝固流失了{loss_power * 100}%!!'
                loss_type = "低"
            for herb_type in self.herb_power:
                self.herb_power[herb_type] *= 1 - loss_power
            msg = f"\r炉温过{loss_type}，药性发生了严重流失！！" + loss_msg
            safe_level = 3
            return msg, safe_level

        elif over_point > 0.5:
            # 接近超出
            loss_power = 0.1 * over_point / 1
            if over_fire > 0:
                loss_msg = f'\r药力蒸发流失了{loss_power * 100}%!!'
                loss_type = "高"
            else:
                loss_msg = f'\r药力凝固流失了{loss_power * 100}%!!'
                loss_type = "低"
            for herb_type in self.herb_power:
                self.herb_power[herb_type] *= 1 - loss_power
            msg = f"\r炉温偏{loss_type}，药性发生了流失！！" + loss_msg
            safe_level = 4
            return msg, safe_level

        elif over_point > 0.3:
            if over_fire > 0:
                loss_type = "高"
            else:
                loss_type = "低"
            msg = f'当前炉温略{loss_type},道友注意控制丹炉温度！！'
            safe_level = 5
            return msg, safe_level
        else:
            msg = f'当前丹炉平稳运行！'
            safe_level = 6
            return msg, safe_level

    def __input_herb_as_main(self, user_fire_control, user_herb_knowledge, herb_id, herb_num) -> str:
        herb_info = get_herb_info(herb_id)
        herb_info_main = herb_info['主药']
        herb_fire_change = herb_info_main['冷热'] * herb_num
        herb_type = herb_info_main['药性']
        add_herb_power = herb_info_main['药力'] * herb_num

        # 计算技巧系数
        base_fire_change, herb_power_keep = count_mix_param(user_fire_control=user_fire_control,
                                                            user_herb_knowledge=user_herb_knowledge)

        herb_power_keep_present = round(herb_power_keep / 100, 2)
        herb_fire_change *= herb_power_keep_present
        add_herb_power *= herb_power_keep_present
        self.herb_power[herb_type] += add_herb_power
        self.fire_value += base_fire_change + herb_fire_change
        result = f'加入{herb_info["药名"]}{herb_num}珠作为主药 保留{herb_power_keep}%药性'
        return result

    def __input_herb_as_ingredient(self, user_fire_control, user_herb_knowledge, herb_id, herb_num) -> str:
        herb_info = get_herb_info(herb_id)
        herb_info_main = herb_info['药引']
        herb_fire_change = herb_info_main['冷热'] * herb_num

        # 计算技巧系数
        base_fire_change, herb_power_keep = count_mix_param(user_fire_control=user_fire_control,
                                                            user_herb_knowledge=user_herb_knowledge)

        self.fire_value += base_fire_change + herb_fire_change
        result = f'加入{herb_info["药名"]}{herb_num}珠作为药引 保留{herb_power_keep}%药性'
        return result

    def __input_herb_as_sub(self, user_fire_control, user_herb_knowledge, herb_id, herb_num) -> str:
        herb_info = get_herb_info(herb_id)
        herb_info_main = herb_info['辅药']
        herb_type = herb_info_main['药性']
        add_herb_power = herb_info_main['药力'] * herb_num

        # 计算技巧系数
        _, herb_power_keep = count_mix_param(user_fire_control=user_fire_control,
                                             user_herb_knowledge=user_herb_knowledge)

        herb_power_keep_present = round(herb_power_keep / 100, 2)
        add_herb_power *= herb_power_keep_present
        self.herb_power[herb_type] += add_herb_power
        result = f'加入{herb_info["药名"]}{herb_num}珠作为辅药 保留{herb_power_keep}%药性'
        return result

    def input_herbs(self, user_fire_control, user_herb_knowledge, input_herb_list: dict):

        # 记录初始炉温
        start_fire = self.fire_value
        msg = "开始向炉火中添加药材:"

        # 处理主药
        if "主药" in input_herb_list:
            for main_herb in input_herb_list["主药"]:
                msg += "\r" + self.__input_herb_as_main(
                    user_fire_control,
                    user_herb_knowledge,
                    herb_id=main_herb[0],
                    herb_num=main_herb[1])

        # 处理药引
        if "药引" in input_herb_list:
            for main_herb in input_herb_list["药引"]:
                msg += "\r" + self.__input_herb_as_ingredient(
                    user_fire_control,
                    user_herb_knowledge,
                    herb_id=main_herb[0],
                    herb_num=main_herb[1])

        # 处理辅药
        if "辅药" in input_herb_list:
            for main_herb in input_herb_list["辅药"]:
                msg += "\r" + self.__input_herb_as_sub(
                    user_fire_control,
                    user_herb_knowledge,
                    herb_id=main_herb[0],
                    herb_num=main_herb[1])

        fire_change = self.fire_value - start_fire
        msg += f"\r炉温{'升高' if fire_change > 0 else '降低'}了 {abs(fire_change)}!"
        fire_msg, safe_level = self.__check_alchemy_furnace_state(user_fire_control)
        msg += fire_msg
        return msg


mix_user: [int, AlchemyFurnace] = {}

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
