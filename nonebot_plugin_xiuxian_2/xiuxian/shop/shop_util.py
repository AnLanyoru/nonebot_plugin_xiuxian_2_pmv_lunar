from .. import XiuConfig
from ..xiuxian_utils.item_json import items


def back_pick_tool(user_back_data: list[dict], pick_key_word: list) -> dict[int, int]:
    """
    快速筛选符合关键词的背包内物品
    """
    the_same: dict[str, str] = XiuConfig().elixir_def
    real_args: list[str] = [the_same[i] if i in the_same else i for i in pick_key_word]
    pick_item_dict: dict[int, int] = {}
    for goal_level in real_args:
        for back in user_back_data:
            goods_id: int = back['goods_id']
            num: int = back['goods_num'] - back['bind_num'] - back['state']
            goods_type: str = back['goods_type']
            goods_name: str = back['goods_name']
            item_info: dict = items.get_data_by_item_id(goods_id)
            item_type: str = item_info['item_type']
            buff_type: str = item_info.get('buff_type')
            item_level: str = item_info.get('level')
            if num < 1:
                continue
            if (item_level == goal_level
                    or goods_name == goal_level
                    or buff_type == goal_level
                    or goods_type == goal_level
                    or item_type == goal_level):
                pick_item_dict[goods_id] = num
    return pick_item_dict
