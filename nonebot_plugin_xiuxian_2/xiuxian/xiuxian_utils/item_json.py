from ..types import BaseItem

try:
    import ujson as json
except ImportError:
    import json
from pathlib import Path
from typing import List

READ_PATH = Path() / "data" / "xiuxian"
SKILL_PATH = READ_PATH / "功法"
WEAPON_PATH = READ_PATH / "装备"
ELIXIR_PATH = READ_PATH / "丹药"
GIFT_PATH = READ_PATH / "礼包"
XIU_LIAN_ITEM_PATH = READ_PATH / "修炼物品"
BOSS_DROPS = READ_PATH / "boss掉落物"


class Items:
    def __init__(self) -> None:
        self.ITEM_JSON_PATH = {
            "防具": WEAPON_PATH / "防具.json",
            "法器": WEAPON_PATH / "法器.json",
            "功法": SKILL_PATH / "主功法.json",
            "辅修功法": SKILL_PATH / "辅修功法.json",
            "神通": SKILL_PATH / "神通.json",
            "丹药": ELIXIR_PATH / "丹药.json",
            "礼包": GIFT_PATH / "礼包.json",
            "药材": ELIXIR_PATH / "药材.json",
            "合成丹药": ELIXIR_PATH / "炼丹丹药.json",
            "炼丹炉": ELIXIR_PATH / "炼丹炉.json",
            "聚灵旗": XIU_LIAN_ITEM_PATH / "聚灵旗.json",
            "道具": XIU_LIAN_ITEM_PATH / "道具.json",
            "神物": ELIXIR_PATH / "神物.json",
            "天地奇物": ELIXIR_PATH / "天地奇物.json"}
        self.items = {}
        self.items_map = {}

    @staticmethod
    def read_file(file_path):
        with open(file_path, "r", encoding="UTF-8") as f:
            data = f.read()
        return json.loads(data)

    def load_items(self):
        for item_type, item_data_path in self.ITEM_JSON_PATH:
            self.set_item_data(self.read_file(item_data_path), item_type)
        self.items_map = {self.items[item_id]['name']: int(item_id) for item_id in self.items}

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
