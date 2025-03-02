import uuid
from datetime import datetime
from typing import TypedDict


class Goods(TypedDict):
    id: uuid.UUID
    """商品id，使用uuid"""
    owner_id: int
    """商品所有者id"""
    item_id: int
    """商品代表物品id"""
    item_type: str
    """商品代表物品类型"""
    item_price: int
    """商品价格"""
    insert_time: datetime
    """创建时间（用于删除过期商品）"""
    buyer: int
    """购买者（用于溯源）"""
