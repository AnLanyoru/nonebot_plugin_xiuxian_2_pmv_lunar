from ..types import BaseItem

try:
    import ujson as json
except ImportError:
    import json
from pathlib import Path
from typing import List

READPATH = Path() / "data" / "xiuxian"
SKILLPATHH = READPATH / "功法"
WEAPONPATH = READPATH / "装备"
ELIXIRPATH = READPATH / "丹药"
GIFT_PATH = READPATH / "礼包"
XIULIANITEMPATH = READPATH / "修炼物品"
BOSSDROPS = READPATH / "boss掉落物"


class Items:
    def __init__(self) -> None:
        self.mainbuff_jsonpath = SKILLPATHH / "主功法.json"
        self.subbuff_jsonpath = SKILLPATHH / "辅修功法.json"
        self.secbuff_jsonpath = SKILLPATHH / "神通.json"
        self.weapon_jsonpath = WEAPONPATH / "法器.json"
        self.armor_jsonpath = WEAPONPATH / "防具.json"
        self.elixir_jsonpath = ELIXIRPATH / "丹药.json"
        self.lb_jsonpath = GIFT_PATH / "礼包.json"
        self.yaocai_jsonpath = ELIXIRPATH / "药材.json"
        self.mix_elixir_type_jsonpath = ELIXIRPATH / "炼丹丹药.json"
        self.ldl_jsonpath = ELIXIRPATH / "炼丹炉.json"
        self.jlq_jsonpath = XIULIANITEMPATH / "聚灵旗.json"
        self.tools_jsonpath = XIULIANITEMPATH / "道具.json"
        self.sw_jsonpath = ELIXIRPATH / "神物.json"
        self.world_qw_jsonpath = ELIXIRPATH / "天地奇物.json"
        self.items = {}
        self.items_map = {}

    @staticmethod
    def readf(FILEPATH):
        with open(FILEPATH, "r", encoding="UTF-8") as f:
            data = f.read()
        return json.loads(data)

    def load_items(self):
        self.set_item_data(self.get_armor_data(), "防具")
        self.set_item_data(self.get_weapon_data(), "法器")
        self.set_item_data(self.get_main_buff_data(), "功法")
        self.set_item_data(self.get_sub_buff_data(), "辅修功法")
        self.set_item_data(self.get_sec_buff_data(), "神通")
        self.set_item_data(self.get_elixir_data(), "丹药")
        self.set_item_data(self.get_lb_data(), "礼包")
        self.set_item_data(self.get_yaocai_data(), "药材")
        self.set_item_data(self.get_mix_elixir_type_data(), "合成丹药")
        self.set_item_data(self.get_ldl_data(), "炼丹炉")
        self.set_item_data(self.get_jlq_data(), "聚灵旗")
        self.set_item_data(self.get_tools_data(), "道具")
        self.set_item_data(self.get_sw_data(), "神物")
        self.set_item_data(self.get_world_qw_data(), "天地奇物")
        self.items_map = {self.items[item_id]['name']: int(item_id) for item_id in self.items}

    def get_armor_data(self):
        return self.readf(self.armor_jsonpath)

    def get_weapon_data(self):
        return self.readf(self.weapon_jsonpath)

    def get_main_buff_data(self):
        return self.readf(self.mainbuff_jsonpath)

    def get_sub_buff_data(self):  # 辅修功法5
        return self.readf(self.subbuff_jsonpath)

    def get_sec_buff_data(self):
        return self.readf(self.secbuff_jsonpath)

    def get_elixir_data(self):
        return self.readf(self.elixir_jsonpath)

    def get_lb_data(self):
        return self.readf(self.lb_jsonpath)

    def get_yaocai_data(self):
        return self.readf(self.yaocai_jsonpath)

    def get_mix_elixir_type_data(self):
        return self.readf(self.mix_elixir_type_jsonpath)

    def get_ldl_data(self):
        return self.readf(self.ldl_jsonpath)

    def get_jlq_data(self):
        return self.readf(self.jlq_jsonpath)

    def get_tools_data(self):
        return self.readf(self.tools_jsonpath)

    def get_sw_data(self):
        return self.readf(self.sw_jsonpath)

    def get_world_qw_data(self):
        return self.readf(self.world_qw_jsonpath)

    def get_data_by_item_id(self, item_id) -> BaseItem:
        if item_id is None:
            return {}
        if (str_item_id := str(item_id)) not in self.items:
            return {}
        return self.items[str_item_id]

    def set_item_data(self, dict_data, item_type):
        for k, v in dict_data.items():
            if item_type == '功法' or item_type == '神通' or item_type == '辅修功法':  # 辅修功法7
                v['rank'], v['level'] = v['level'], v['rank']
                v['type'] = '技能'
            self.items[k] = v
            self.items[k].update({'item_type': item_type})

            if '境界' in v:
                self.items[k]['境界'] = v['境界']

    def get_data_by_item_type(self, item_type):
        temp_dict = {}
        for k, v in self.items.items():
            if v['item_type'] in item_type:
                temp_dict[k] = v
        return temp_dict

    def get_random_id_list_by_rank_and_item_type(
            self,
            final_rank: int,
            item_type: List = None
    ):
        """
        获取随机一个物品ID,可以指定物品类型,物品等级和用户等级相差150级以上会被抛弃
        :param final_rank:用户的最终rank,最终rank由用户rank和rank增幅事件构成
        :param item_type:type:list,物品类型，可以为空，枚举值：法器、防具、神通、功法、丹药
        :return 获得的ID列表,type:list
        """
        l_id = []
        final_rank += 0  # 新增境界补正
        for k, v in self.items.items():
            if item_type is not None:
                if v['item_type'] in item_type and abs(int(v['rank']) - 55) <= final_rank and final_rank - int(
                        abs(int(v['rank']) - 55)) <= 150:
                    l_id.append(k)
                else:
                    continue
            else:  # 全部随机
                if int(abs(int(v['rank']) - 55)) <= final_rank and final_rank - int(abs(int(v['rank']) - 55)) <= 150:
                    l_id.append(k)
                else:
                    continue
        return l_id

    def get_item_id(self, item_name):
        item_id = self.items_map.get(item_name, 0)
        return item_id

    def change_id_num_dict_to_msg(self, item_dict: dict[int, int]) -> str:
        msg: str = ''
        for item_id, item_num in item_dict.items():
            msg += f"\r{self.get_data_by_item_id(item_id)['name']} {item_num}"
        return msg


items = Items()
items.load_items()
