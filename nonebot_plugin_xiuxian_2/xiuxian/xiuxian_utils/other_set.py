import random

from .clean_utils import number_to
from .. import XiuConfig
from ..xiuxian_data.data.境界_data import level_data
from ..xiuxian_place import place
from .xiuxian2_handle import sql_message, \
    UserBuffDate, xiuxian_impart


class OtherSet(XiuConfig):

    def __init__(self):
        super().__init__()

    async def set_closing_type(self, user_level):
        list_all = len(self.level) - 1
        now_index = self.level.index(user_level)
        if list_all == now_index:
            need_exp = 0.001
        else:
            is_updata_level = self.level[now_index + 1]
            need_exp = await xiuxian_impart.get_level_power(is_updata_level)
        return need_exp

    async def get_type(self, user_exp, rate, user_level, user_id):
        list_all = len(self.level) - 1
        now_index = self.level.index(user_level)
        if list_all == now_index:
            return "道友已是最高境界，无法突破！"

        is_updata_level = self.level[now_index + 1]
        need_exp = await xiuxian_impart.get_level_power(is_updata_level)

        # 判断修为是否足够突破
        if user_exp >= need_exp:
            pass
        else:
            return f"道友的修为不足以突破！距离下次突破需要{need_exp - user_exp}修为！突破境界为：{is_updata_level}"
        # 判断目标境界是否需要特殊灵根
        user_msg = await sql_message.get_user_info_with_id(user_id)
        now_root = user_msg["root_type"]
        user_place = place.get_now_place_id(user_id)
        user_world = place.get_world_id(user_place)
        world_name = place.get_world_name(user_place)
        # 哼，我就写垃圾代码怎么了？
        if user_level == "合道境后期":
            if user_world < 1:
                msg = f"道友所在世界【{world_name}】天地法则限制道友无法突破\r【{world_name}】可承载的最高境界为{user_level}"
                return msg
            else:
                pass
        elif user_level == "羽化境后期":
            if user_world < 2:
                msg = f"道友所在世界【{world_name}】天地法则限制道友无法突破\r【{world_name}】可承载的最高境界为{user_level}"
                return msg
            else:
                pass
        elif user_level == "仙帝境后期":
            if user_world < 3:
                msg = f"道友所在世界【{world_name}】天地法则限制道友无法突破\r【{world_name}】可承载的最高境界为{user_level}"
                return msg
            else:
                pass
        elif user_level == "道无涯后期":
            if now_root == "道之本源":
                pass
            else:
                msg = f"道友的根基不足支持本次以突破！突破{is_updata_level}需要拥有道之本源！！！"
                return msg
        else:
            pass
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
    async def send_hp_mp(user_id, hp, mp):
        user_info = await xiuxian_impart.get_user_info_with_id(user_id)
        max_hp = int(user_info['exp'] / 2)
        max_mp = int(user_info['exp'])

        msg = []
        hp_mp = []

        if user_info['hp'] < max_hp:
            if user_info['hp'] + hp < max_hp:
                new_hp = user_info['hp'] + hp
                msg.append(f',回复气血：{number_to(hp)}|{hp}')
            else:
                new_hp = max_hp
                msg.append(f',回复气血：{number_to(hp)}|{hp},气血已回满！')
        else:
            new_hp = user_info['hp']
            msg.append('')

        if user_info['mp'] < max_mp:
            if user_info['mp'] + mp < max_mp:
                new_mp = user_info['mp'] + mp
                msg.append(f',回复真元：{number_to(mp)}|{mp}')
            else:
                new_mp = max_mp
                msg.append(',真元已回满！')
        else:
            new_mp = user_info['mp']
            msg.append('')

        hp_mp.append(new_hp)
        hp_mp.append(new_mp)
        hp_mp.append(user_info['exp'])

        return msg, hp_mp
