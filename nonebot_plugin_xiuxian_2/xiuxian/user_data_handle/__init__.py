import json
import pickle

from ..xiuxian_database.database_connect import database
from ..xiuxian_utils.clean_utils import zips
from ..xiuxian_utils.item_json import items

buff_type_def = {'atk': '攻击提升',
                 'hp': '气血提升',
                 'mp': '真元提升',
                 '破甲': '破甲提升',
                 '破厄': '抵消负面buff'}
temp_buff_def = {'atk': '攻击',
                 'hp': '气血',
                 'mp': '真元'}


class UserBuffData:
    def __init__(self, user_id: int):
        self.user_id: int = user_id
        self.__table = 'buff_info'

    async def __select_data(self, columns: list):
        sql = f"select {','.join(columns)} from {self.__table} where user_id=$1"
        async with database.pool.acquire() as conn:
            result = await conn.fetch(sql, self.user_id)
            return zips(**result[0]) if result else None

    async def __update_data(self, columns_data: dict):
        column_count = len(columns_data) + 2
        update_column = ",".join([f"{column_name}=${count}" for column_name, count
                                  in zip(columns_data.keys(), range(2, column_count))])
        sql = f"update {self.__table} set {update_column} where user_id=$1"
        async with database.pool.acquire() as conn:
            await conn.execute(sql, self.user_id, *columns_data.values())

    async def get_fight_temp_buff(self):
        temp_buff = await self.__select_data(['elixir_buff'])
        temp_buff_bit = temp_buff['elixir_buff']
        return pickle.loads(temp_buff_bit) if temp_buff_bit else {}

    async def update_fight_temp_buff(self, temp_buff: dict):
        data = {'elixir_buff': pickle.dumps(temp_buff)}
        await self.__update_data(data)

    async def get_fast_elixir_set(self) -> list[int]:
        temp_buff = await self.__select_data(['prepare_elixir_set'])
        temp_buff_bit = temp_buff['prepare_elixir_set']
        return json.loads(temp_buff_bit) if temp_buff_bit else []

    async def update_fast_elixir_set(self, temp_buff: list[str]):
        data = {'prepare_elixir_set': json.dumps(temp_buff)}
        await self.__update_data(data)

    async def add_fight_temp_buff(self, elixir_buff_info: dict) -> tuple[str, bool]:
        temp_buff_info = await self.get_fight_temp_buff()
        buff_msg = ''
        for buff_type, buff_value in elixir_buff_info.items():
            if buff_type in temp_buff_info:
                return f'道友已使用临时{buff_type_def[buff_type]}类丹药，请将对应药性耗尽后重新使用', False
            temp_buff_info[buff_type] = buff_value
            buff_msg += f"{buff_type_def[buff_type]}:{buff_value * 100}%"
        await self.update_fight_temp_buff(temp_buff_info)
        return f"下场战斗内{buff_msg}", True

    async def set_prepare_elixir(self, elixir_name_list: list[str]) -> tuple[str, bool]:
        for elixir_name in elixir_name_list:
            item_id = items.get_item_id(item_name=elixir_name)
            if not item_id:
                return '使用列表中含有未知的物品', False
            item_info = items.get_data_by_item_id(item_id)
            item_type = item_info['type']
            if item_type != "丹药":
                return '使用列表中含有非丹药', False
        await self.update_fast_elixir_set(elixir_name_list)
        return "成功设置", True
