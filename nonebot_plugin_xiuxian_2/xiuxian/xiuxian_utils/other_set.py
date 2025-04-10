import random

from .clean_utils import number_to
from .xiuxian2_handle import sql_message, xiuxian_impart
from .. import XiuConfig
from ..user_data_handle import UserBuffHandle
from ..xiuxian_place import place


class OtherSet(XiuConfig):

    def __init__(self):
        super().__init__()

    async def set_closing_type(self, user_level):
        list_all = len(self.level) - 1
        now_index = self.level.index(user_level)
        if list_all == now_index:
            need_exp = 1
        else:
            is_updata_level = self.level[now_index + 1]
            need_exp = await sql_message.get_level_power(is_updata_level)
        return need_exp

    async def get_type(self, user_exp, rate, user_level, user_info):
        list_all = len(self.level) - 1
        now_index = self.level.index(user_level)
        if list_all == now_index:
            return "道友已是最高境界，无法突破！"

        is_updata_level = self.level[now_index + 1]
        need_exp = await sql_message.get_level_power(is_updata_level)

        # 判断修为是否足够突破
        if user_exp < need_exp:
            return f"道友的修为不足以突破！距离下次突破需要{need_exp - user_exp}修为！突破境界为：{is_updata_level}"
        # 判断目标境界是否需要特殊灵根
        now_root = user_info["root_type"]
        user_place = user_info['place_id']
        user_world = place.get_world_id(user_place)
        world_name = place.get_world_name(user_place)
        # 境界限制
        limit_level = {
            "合道境后期": 1,
            "登仙境·九劫": 2,
            "无极仙尊·大圆满": 3
        }
        if user_level in limit_level.keys():
            if user_world < limit_level[user_level]:
                msg = f"道友所在世界【{world_name}】天地法则限制道友无法突破\r【{world_name}】可承载的最高境界为{user_level}"
                return msg
        elif user_level == "道无涯·掌缘生灭":
            if now_root != "道之本源":
                msg = f"道友的根基不足支持本次以突破！突破{is_updata_level}需要拥有道之本源！！！"
                return msg
        success_rate = True if random.randint(0, 99) < rate else False

        if success_rate:
            return [self.level[now_index + 1]]
        else:
            return '失败'

    @staticmethod
    def calculated(rate: dict) -> str:
        """
        根据概率计算，轮盘型
        :rate:格式{"数据名":"获取几率"}
        :return: 数据名
        """

        get_list = []  # 概率区间存放

        n = 1
        for name, value in rate.items():  # 生成数据区间
            value_rate = int(value)
            list_rate = [_i for _i in range(n, value_rate + n)]
            get_list.append(list_rate)
            n += value_rate

        now_n = n - 1
        get_random = random.randint(1, now_n)  # 抽取随机数

        index_num = None
        for list_r in get_list:
            if get_random in list_r:  # 判断随机在那个区间
                index_num = get_list.index(list_r)
                break

        return list(rate.keys())[index_num]

    @staticmethod
    def get_power_rate(mind, other):
        power_rate = mind / (other + mind)
        if power_rate >= 0.8:
            return "道友偷窃小辈实属天道所不齿！"
        elif power_rate <= 0.05:
            return "道友请不要不自量力！"
        else:
            return int(power_rate * 100)

    @staticmethod
    def player_fight(player1: dict, player2: dict):
        """
        回合制战斗
        type_in : 1 为完整返回战斗过程（未加）
        2：只返回战斗结果
        数据示例：
        {"道号": None, "气血": None, "攻击": None, "真元": None, '会心':None}
        """
        msg1 = "{}发起攻击，造成了{}伤害\r"
        msg2 = "{}发起攻击，造成了{}伤害\r"

        play_list = []
        suc = None
        if player1['气血'] <= 0:
            player1['气血'] = 1
        if player2['气血'] <= 0:
            player2['气血'] = 1
        while True:
            player1_gj = int(round(random.uniform(0.95, 1.05), 2) * player1['攻击'])
            if random.randint(0, 100) <= player1['会心']:
                player1_gj = int(player1_gj * player1['爆伤'])
                msg1 = "{}发起会心一击，造成了{}伤害\r"

            player2_gj = int(round(random.uniform(0.95, 1.05), 2) * player2['攻击'])
            if random.randint(0, 100) <= player2['会心']:
                player2_gj = int(player2_gj * player2['爆伤'])
                msg2 = "{}发起会心一击，造成了{}伤害\r"

            play1_sh: int = int(player1_gj * (1 - player2['防御']))
            play2_sh: int = int(player2_gj * (1 - player1['防御']))

            play_list.append(msg1.format(player1['道号'], number_to(play1_sh)))
            player2['气血'] = player2['气血'] - play1_sh
            play_list.append(f"{player2['道号']}剩余血量{number_to(player2['气血'])}")
            xiuxian_impart.update_user_hp_mp(player2['user_id'], player2['气血'], player2['真元'])

            if player2['气血'] <= 0:
                play_list.append(f"{player1['道号']}胜利")
                suc = f"{player1['道号']}"
                xiuxian_impart.update_user_hp_mp(player2['user_id'], 1, player2['真元'])
                break

            play_list.append(msg2.format(player2['道号'], number_to(play2_sh)))
            player1['气血'] = player1['气血'] - play2_sh
            play_list.append(f"{player1['道号']}剩余血量{number_to(player1['气血'])}\r")
            xiuxian_impart.update_user_hp_mp(player1['user_id'], player1['气血'], player1['真元'])

            if player1['气血'] <= 0:
                play_list.append(f"{player2['道号']}胜利")
                suc = f"{player2['道号']}"
                xiuxian_impart.update_user_hp_mp(player1['user_id'], 1, player1['真元'])
                break
            if player1['气血'] <= 0 or player2['气血'] <= 0:
                play_list.append("逻辑错误！！！")
                break

        return play_list, suc

    @staticmethod
    async def send_hp_mp(user_id, time_min: int):
        user_buff_handle = UserBuffHandle(user_id)
        user_info = await user_buff_handle.get_user_fight_info()
        max_hp = user_info['exp'] / 2
        max_mp = user_info['exp']
        max_hp_see = user_info['max_hp']
        max_mp_see = user_info['max_mp']
        regain_present = 0.01 * time_min
        regain_hp = max_hp * regain_present
        regain_mp = max_mp * regain_present
        regain_hp_see = max_hp_see * regain_present
        regain_mp_see = max_mp_see * regain_present
        msg = []
        hp_mp = []

        if (new_hp := user_info['hp'] + regain_hp) < max_hp:
            msg.append(f',回复气血：{number_to(regain_hp_see)}|{regain_hp_see}')
        else:
            new_hp = max_hp
            msg.append(f',气血已回满！')

        if user_info['mp'] + regain_mp < max_mp:
            new_mp = user_info['mp'] + regain_mp
            msg.append(f',回复真元：{number_to(regain_mp_see)}|{regain_mp_see}')
        else:
            new_mp = max_mp
            msg.append(',真元已回满！')

        hp_mp.append(new_hp)
        hp_mp.append(new_mp)
        hp_mp.append(user_info['exp'])

        return msg, hp_mp
