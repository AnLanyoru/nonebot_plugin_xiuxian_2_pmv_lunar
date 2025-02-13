import json
import math
import random

from .mix_elixir_database import get_user_mix_elixir_info
from ..xiuxian_database.database_connect import database
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

# 加载丹药合成表
all_mix_elixir = {item_id: items_info
                  for item_id, items_info in items.items.items()
                  if items_info["item_type"] == '合成丹药'}

all_mix_elixir_table = {}
for mix_elixir_id, mix_elixir_info in all_mix_elixir.items():
    elixir_mix_type_list = [herb_value_def[int(here_type)]
                       for here_type in mix_elixir_info['elixir_config'].keys()]
    elixir_mix_type_list.sort()
    elixir_mix_type = "".join(elixir_mix_type_list)
    need_power = sum(mix_elixir_info['elixir_config'].values())
    if elixir_mix_type in all_mix_elixir_table:
        all_mix_elixir_table[elixir_mix_type][need_power] = int(mix_elixir_id)
    else:
        all_mix_elixir_table[elixir_mix_type] = {need_power: int(mix_elixir_id)}
for mix_elixir_table in all_mix_elixir_table:
    all_mix_elixir_table[mix_elixir_table] = dict(sorted(all_mix_elixir_table[mix_elixir_table].items(),
                                                         key=lambda x: x[0], reverse=True))


def round_two(num):
    return round(num, 2)


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
            '药力': real_herb_info['辅药']['power']},
        '品级': math.log(real_herb_info['主药']['power'], 2)}
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
        herb_power_keep = random.randint(10 + power_keep_min_param, 52 + power_keep_max_param)
    else:
        herb_power_keep = 0

    return base_fire_change, herb_power_keep


def count_fire_control(user_fire_control):
    fire_over_improve = (int(user_fire_control / (user_fire_control + 500000) * 10)
                         + int(user_fire_control / (user_fire_control + 50000) * 10)
                         + int(user_fire_control / (user_fire_control + 5000) * 30)
                         + int(user_fire_control / (user_fire_control + 500) * 40))
    return fire_over_improve


class AlchemyFurnace:
    def __init__(self, alchemy_furnace_id):
        # 丹炉属性
        self.alchemy_furnace_id = alchemy_furnace_id
        self.name: str = "无"
        self.fire_sub: int = 0
        self.herb_save: int = 0
        self.make_elixir_improve: int = 0

        # 丹炉状态
        self.__fire_value: float = 0
        self.__herb_power: dict = {
            "生息": 0,
            "养气": 0,
            "炼气": 0,
            "聚元": 0,
            "凝神": 0}

        # 炼丹技术属性成长
        self.__sum_herb_value_input = 0
        self.__fire_control_num = 0

        # 初始化丹炉属性
        alchemy_furnace_info = items.get_data_by_item_id(alchemy_furnace_id)
        self.name: str = alchemy_furnace_info['name']
        self.fire_sub: int = alchemy_furnace_info['buff']
        self.herb_save: int = alchemy_furnace_info['buff']
        self.make_elixir_improve: int = alchemy_furnace_info['buff']

    async def save_data(self, user_id: int):

        data_json = {"alchemy_furnace_id": self.alchemy_furnace_id,
                     "fire_value": self.__fire_value,
                     "herb_power": self.__herb_power,
                     "sum_herb_value_input": self.__sum_herb_value_input,
                     "fire_control_num": self.__fire_control_num}

        data = {"last_alchemy_furnace_data": json.dumps(data_json)}
        await database.update(
            table='mix_elixir_info',
            where={'user_id': user_id},
            **data
        )

    def reload_data(self, data_dict: dict):
        self.__fire_value = data_dict['fire_value']
        self.__herb_power = data_dict['herb_power']
        self.__sum_herb_value_input = data_dict['sum_herb_value_input']
        self.__fire_control_num = data_dict['fire_control_num']

    def get_sum_herb_power(self) -> int:
        return sum(self.__herb_power.values())

    def get_herb_power_rank(self):
        had_herb_power = [herb_type for herb_type in self.__herb_power.keys() if self.__herb_power[herb_type] > 0]
        return sorted(had_herb_power, key=lambda x: self.__herb_power[x], reverse=True)

    def get_main_herb_power(self):
        if self.get_sum_herb_power():
            herb_power_rank = self.get_herb_power_rank()
            return '、'.join(herb_power_rank[:2])
        else:
            return "无"

    def get_herb_power_msg(self):
        had_herb_power = [f"{herb_power_type}: {round(self.__herb_power[herb_power_type], 2)}"
                          for herb_power_type in self.get_herb_power_rank()
                          if self.__herb_power[herb_power_type]]
        if not had_herb_power:
            return "当前无药力"
        return "\r".join(had_herb_power)

    def get_state_msg(self, fire_name) -> str:

        msg = (f"丹炉状态：\r"
               f"丹炉名称：{self.name}\r"
               f"丹火：{fire_name}\r"
               f"炉温：{self.__fire_value:.2f}\r"
               f"炉内总药力：{self.get_sum_herb_power():.2f}\r"
               f"炉内主导药力：{self.get_main_herb_power()}\r"
               f"药力详情：\r"
               f"{self.get_herb_power_msg()}")

        return msg

    def __check_alchemy_furnace_state(self, user_fire_control) -> [str, int]:
        over_fire = self.__fire_value - 500

        over_point = abs(over_fire) / (200
                                       + self.fire_sub * 20
                                       + count_fire_control(user_fire_control) * 2)

        if not self.get_sum_herb_power():
            if over_point > 1.5:
                if over_fire > 0:
                    msg = f"\r炉温({self.__fire_value:.2f})严重超出控制，丹炉发生了爆炸！！"
                    safe_level = 0
                    self.__fire_value = random.randint(50, 100)
                else:
                    msg = f"\r炉温({self.__fire_value:.2f})过低！！请提高温度后加入药材！！"
                    safe_level = 1

            elif over_point > 0.3:
                msg = f"\r当前炉温({self.__fire_value:.2f})偏"
                msg += '高' if over_fire > 0 else '低'
                msg += ' 不宜加入药材'
                safe_level = 3
            else:
                msg = f"\r当前炉温({self.__fire_value:.2f})平稳，宜加入药材"
                safe_level = 6
            return msg, safe_level

        if over_point > 1.5:
            if over_fire > 0:
                msg = f"\r炉温({self.__fire_value:.2f})严重超出控制，丹炉发生了爆炸！！"
                safe_level = 0
                self.__fire_value = random.randint(50, 100)
            else:
                msg = f"\r炉温({self.__fire_value:.2f})严重过低，丹炉内的药液彻底冷凝了！！"
                safe_level = 1
                self.__fire_value = max(self.__fire_value, 0)
            for herb_type in self.__herb_power:
                self.__herb_power[herb_type] *= 0.1 * safe_level
            return msg, safe_level
        elif over_point > 1.2:
            # 20% 超出
            msg = f"\r炉温({self.__fire_value:.2f})超出控制，药性发生了严重流失！！"
            loss_power = over_point - 1
            if over_fire > 0:
                loss_power *= 2
                msg += f"\r药力蒸发流失了{loss_power * 100:.2f}%!!"
            else:
                msg += f"\r药力凝固流失了{loss_power * 100:.2f}%!!"
            for herb_type in self.__herb_power:
                self.__herb_power[herb_type] *= 1 - loss_power
            safe_level = 2
        elif over_point > 1:
            # 超出
            loss_power = (over_point - 1) / 2 + 0.1
            if over_fire > 0:
                loss_msg = f"\r药力蒸发流失了{loss_power * 100:.2f}%!!"
                loss_type = "高"
            else:
                loss_msg = f"\r药力凝固流失了{loss_power * 100:.2f}%!!"
                loss_type = "低"
            for herb_type in self.__herb_power:
                self.__herb_power[herb_type] *= 1 - loss_power
            msg = f"\r炉温({self.__fire_value:.2f})过{loss_type}，药性发生了严重流失！！" + loss_msg
            safe_level = 3

        elif over_point > 0.5:
            # 接近超出
            loss_power = 0.1 * over_point / 1
            if over_fire > 0:
                loss_msg = f'\r药力蒸发流失了{loss_power * 100:.2f}%!!'
                loss_type = "高"
            else:
                loss_msg = f'\r药力凝固流失了{loss_power * 100:.2f}%!!'
                loss_type = "低"
            for herb_type in self.__herb_power:
                self.__herb_power[herb_type] *= 1 - loss_power
            msg = f"\r炉温({self.__fire_value:.2f})偏{loss_type}，药性发生了流失！！" + loss_msg
            safe_level = 4

        elif over_point > 0.3:
            if over_fire > 0:
                loss_type = "高"
            else:
                loss_type = "低"
            msg = f'当前炉温({self.__fire_value:.2f})略{loss_type},道友注意控制丹炉温度！！'
            safe_level = 5

        else:
            msg = f'当前丹炉平稳运行！炉温({self.__fire_value:.2f})'
            safe_level = 6
        return msg, safe_level

    def __input_herb_as_main(self,
                             user_fire_control,
                             user_herb_knowledge,
                             user_fire_more_power,
                             herb_id, herb_num) -> str:
        herb_info = get_herb_info(herb_id)
        herb_info_main = herb_info['主药']
        herb_fire_change = herb_info_main['冷热'] * herb_num
        herb_type = herb_info_main['药性']
        add_herb_power = herb_info_main['药力'] * herb_num
        self.__sum_herb_value_input += herb_info['品级'] * herb_num

        # 计算技巧系数
        base_fire_change, herb_power_keep = count_mix_param(user_fire_control=user_fire_control,
                                                            user_herb_knowledge=user_herb_knowledge)

        # 丹火增幅
        herb_power_keep *= (1 + 0.3 * user_fire_more_power)
        # 实际百分比系数
        herb_power_keep_present = herb_power_keep / 100
        # 计算实际炉温变化
        herb_fire_change *= herb_power_keep_present
        # 计算实际药性保留
        add_herb_power *= herb_power_keep_present
        self.__herb_power[herb_type] += add_herb_power
        self.__fire_value += base_fire_change + herb_fire_change
        result = (f"\r加入{herb_info['药名']}{herb_num}珠作为主药"
                  f"\r保留{herb_power_keep:.2f}%药性({herb_type}:{add_herb_power:.2f})")
        if herb_fire_change:
            if herb_fire_change > 0:
                temp_type = '性热'
                temp_change_type = '升高'
            else:
                temp_type = '性寒'
                temp_change_type = '降低'
            result += f"炉温因药材{temp_type}, {temp_change_type}了{abs(herb_fire_change):.2f}"
        return result

    def __input_herb_as_ingredient(self,
                                   user_fire_control,
                                   user_herb_knowledge,
                                   user_fire_more_power,
                                   herb_id, herb_num) -> str:
        herb_info = get_herb_info(herb_id)
        herb_info_main = herb_info['药引']
        herb_fire_change = herb_info_main['冷热'] * herb_num
        self.__sum_herb_value_input += herb_info['品级'] * herb_num
        if not herb_fire_change:
            return f"\r加入{herb_info['药名']}{herb_num}珠作为药引，但无效果"

        # 计算技巧系数
        base_fire_change, herb_power_keep = count_mix_param(user_fire_control=user_fire_control,
                                                            user_herb_knowledge=user_herb_knowledge)

        # 丹火增幅
        herb_power_keep *= (1 + 0.3 * user_fire_more_power)
        # 最终保留药性（冷热）
        herb_fire_change = herb_fire_change * herb_power_keep / 100
        # 炉温变化
        self.__fire_value += base_fire_change + herb_fire_change
        # 判断输出文本
        if herb_fire_change > 0:
            temp_type = '性热'
            temp_change_type = '升高'
        else:
            temp_type = '性寒'
            temp_change_type = '降低'
        result = (f"\r加入{herb_info['药名']}{herb_num}珠作为药引"
                  f"\r保留{herb_power_keep:.2f}%药性({temp_type}:{herb_fire_change:.2f})\r"
                  f"炉温因药材{temp_type}, {temp_change_type}了{abs(herb_fire_change):.2f}")

        return result

    def __input_herb_as_sub(self,
                            user_fire_control,
                            user_herb_knowledge,
                            user_fire_more_power,
                            herb_id, herb_num) -> str:
        herb_info = get_herb_info(herb_id)
        herb_info_main = herb_info['辅药']
        herb_type = herb_info_main['药性']
        add_herb_power = herb_info_main['药力'] * herb_num
        self.__sum_herb_value_input += herb_info['品级'] * herb_num

        # 计算技巧系数
        base_fire_change, herb_power_keep = count_mix_param(user_fire_control=user_fire_control,
                                             user_herb_knowledge=user_herb_knowledge)

        # 丹火增幅
        herb_power_keep *= (1 + 0.3 * user_fire_more_power)
        # 计算保留率 实际值
        herb_power_keep_present = herb_power_keep / 100
        # 计算药性保留
        add_herb_power *= herb_power_keep_present
        # 炉温变化
        self.__fire_value = max(self.__fire_value + base_fire_change, 0)
        if herb_power_rank := self.get_herb_power_rank():
            # 辅药添加后不超过最大值的95%
            most_herb_type = herb_power_rank[0]
            most_herb_power = self.__herb_power[most_herb_type] * 0.95
        else:
            most_herb_type = herb_type
            most_herb_power = 0
        if herb_type == most_herb_type:
            return f"\r加入{herb_info['药名']}{herb_num}珠作为辅药\r因为药性没有主药力调和，药性全部流失了"
        max_add_herb_power = most_herb_power - self.__herb_power[herb_type]
        real_add_herb_power = min(add_herb_power, max_add_herb_power)
        self.__herb_power[herb_type] += real_add_herb_power
        result = (f"\r加入{herb_info['药名']}{herb_num}珠作为辅药"
                  f"\r保留{herb_power_keep:.2f}%药性({herb_type}:{add_herb_power:.2f})")
        if real_add_herb_power < add_herb_power:
            final_keep = real_add_herb_power / add_herb_power
            loss_power = 1 - final_keep
            result += (f"\r由于主药力不足，保留的药性流失了{loss_power * 100:.2f}%！！\r"
                       f"最终保留{(herb_power_keep * final_keep):.2f}%药性({herb_type}:{real_add_herb_power:.2f})")
        return result

    def input_herbs(self,
                    user_fire_control,
                    user_herb_knowledge,
                    user_fire_more_power,
                    input_herb_list: dict):

        # 记录初始炉温
        start_fire = self.__fire_value
        msg = "开始向炉火中添加药材:"

        # 处理主药
        if "主药" in input_herb_list:
            for main_herb in input_herb_list["主药"]:
                msg += "\r" + self.__input_herb_as_main(
                    user_fire_control,
                    user_herb_knowledge,
                    user_fire_more_power,
                    herb_id=main_herb[0],
                    herb_num=main_herb[1])

        # 处理药引
        if "药引" in input_herb_list:
            for main_herb in input_herb_list["药引"]:
                msg += "\r" + self.__input_herb_as_ingredient(
                    user_fire_control,
                    user_herb_knowledge,
                    user_fire_more_power,
                    herb_id=main_herb[0],
                    herb_num=main_herb[1])

        # 处理辅药
        if "辅药" in input_herb_list:
            for main_herb in input_herb_list["辅药"]:
                msg += "\r" + self.__input_herb_as_sub(
                    user_fire_control,
                    user_herb_knowledge,
                    user_fire_more_power,
                    herb_id=main_herb[0],
                    herb_num=main_herb[1])

        self.__fire_value = max(self.__fire_value, 0)

        fire_change = self.__fire_value - start_fire
        msg += f"\r炉温{'升高' if fire_change > 0 else '降低'}了 {abs(fire_change)}!"

        # 增加控火经验
        self.__fire_control_num = min(10 + self.__fire_control_num, 100)
        fire_msg, safe_level = self.__check_alchemy_furnace_state(user_fire_control)
        msg += fire_msg
        return msg

    def change_temp(self, user_fire_control, goal_value: int, is_warm_up=True):
        change_type = '升高' if is_warm_up else '降低'
        msg = f"尝试{change_type}{goal_value}点炉温：\r"
        fire_control_param = count_fire_control(user_fire_control)
        random_param = random.randint(10 + fire_control_param, 190 - fire_control_param) / 100
        user_fire_change = random_param * goal_value

        random_fire_change = ((random.randint(10 + fire_control_param, 190 - fire_control_param) - 100)
                              * random.choice([1, -1]))
        msg += (f"{change_type}炉温过程中，"
                f"丹炉温度波动{'升高' if random_fire_change > 0 else '降低'}了{abs(random_fire_change):.2f}\r")
        msg += f"道友成功使丹炉温度{change_type}了{abs(user_fire_change):.2f}\r"
        if not is_warm_up:
            user_fire_change *= -1
        sum_fire_change = user_fire_change + random_fire_change
        msg += f"丹炉总温度{'升高' if sum_fire_change > 0 else '降低'}了{abs(sum_fire_change):.2f}\r"
        self.__fire_value = max(sum_fire_change + self.__fire_value, 0)
        msg += self.__check_alchemy_furnace_state(user_fire_control)[0]

        # 增加控火经验
        self.__fire_control_num = min(10 + self.__fire_control_num, 100)
        return msg

    def make_elixir(self):
        herb_power_rank = self.get_herb_power_rank()[:2]
        herb_power_rank.sort()
        herb_power_rank_set = "".join(herb_power_rank)
        make_elixir_info = {}
        if herb_power_rank_set not in all_mix_elixir_table:
            msg = f"当前药力无法成丹！！"
            return msg, make_elixir_info
        mix_table = all_mix_elixir_table[herb_power_rank_set]
        now_sum_power = self.get_sum_herb_power()
        msg = f"药力不足，还不足以凝聚丹药！！"
        for elixir_need_power, elixir_id in mix_table.items():
            if now_sum_power > elixir_need_power:
                make_elixir_info = items.get_data_by_item_id(elixir_id)
                make_elixir_info['item_id'] = elixir_id
                make_elixir_info['give_fire_control_exp'] = self.__fire_control_num
                make_elixir_info['give_herb_knowledge_exp'] = self.__sum_herb_value_input * 5
                msg = f"成功凝聚丹药{make_elixir_info['name']}"
                for herb_type in self.__herb_power:
                    self.__herb_power[herb_type] = 0
                self.__fire_control_num = 0
                self.__sum_herb_value_input = 0
                break
        return msg, make_elixir_info


mix_user_temp: [int, AlchemyFurnace] = {}


async def get_user_alchemy_furnace(user_id: int) -> AlchemyFurnace:
    if user_id in mix_user_temp:
        user_alchemy_furnace: AlchemyFurnace = mix_user_temp[user_id]
    else:
        user_mix_elixir_info = await get_user_mix_elixir_info(user_id)
        elixir_data_json = user_mix_elixir_info['last_alchemy_furnace_data']
        elixir_data = json.loads(elixir_data_json)
        mix_user_temp[user_id] = AlchemyFurnace(elixir_data['alchemy_furnace_id'])
        mix_user_temp[user_id].reload_data(elixir_data)
        user_alchemy_furnace: AlchemyFurnace = mix_user_temp[user_id]
    return user_alchemy_furnace


def remove_mix_user(user_id: int) -> None:
    if user_id in mix_user_temp:
        del mix_user_temp[user_id]
