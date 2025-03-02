from .. import XiuConfig
from ..xiuxian_utils.item_json import items


def back_pick_tool(user_back_data: list[dict], pick_key_word: list) -> dict[int, int]:
    """
    快速筛选符合关键词的背包内物品
    """
    the_same: dict[str, str] = XiuConfig().elixir_def
    real_args: list[str] = [the_same[i] if i in the_same else i for i in pick_key_word]
    pick_item_dict: dict[int, int] = {}
    sum_num: int = 0  # 总数量计数 不超过1w个物品
    max_num: int = 10000  # 单次处理上架上限
    for back in user_back_data:
        for goal_level in real_args:
            goods_id: int = back['goods_id']
            num: int = back['goods_num'] - back['bind_num'] - back['state']
            goods_type: str = back['goods_type']
            goods_name: str = back['goods_name']
            item_info: dict = items.get_data_by_item_id(goods_id)
            item_type: str = item_info['item_type']
            buff_type: str = item_info.get('buff_type')
            item_level: str = item_info.get('level')
            if num < 1:
                break
            if (item_level == goal_level
                    or goods_name == goal_level
                    or buff_type == goal_level
                    or goods_type == goal_level
                    or item_type == goal_level):
                if num + sum_num >= max_num:
                    num = max_num - sum_num
                    pick_item_dict[goods_id] = num
                    sum_num = max_num
                    break
                pick_item_dict[goods_id] = num
                sum_num += num
                break
    return pick_item_dict
