import json
import pickle
from copy import deepcopy

from ..types import NewEquipmentBuffs
from ..types.user_info import UserFightInfo
from ..xiuxian_data.data.境界_data import level_data
from ..xiuxian_database.database_connect import database
from ..xiuxian_utils.clean_utils import zips
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.xiuxian2_handle import sql_message, xiuxian_impart, UserBuffDate

buff_type_def = {'atk': '攻击提升',
                 'hp': '气血提升',
                 'mp': '真元提升',
                 '破甲': '破甲提升',
                 '破厄': '抵消负面buff'}
temp_buff_def = {'atk': '攻击',
                 'hp': '气血',
                 'mp': '真元'}

new_equipment_name_def = {'法器': 'faqi_buff',
                          '防具': 'armor_buff',
                          '本命法宝': 'lifebound_treasure',
                          '辅助法宝': 'support_artifact',
                          '内甲': 'inner_armor',
                          '道袍': 'daoist_robe',
                          '道靴': 'daoist_boots',
                          '灵戒': 'spirit_ring'}

new_equipment_buff_def = {'空间穿梭': 'miss_rate',
                          '空间封锁': 'decrease_miss_rate',
                          '攻击': 'atk',
                          '生命': 'hp',
                          '会心率': 'crit',
                          '抗会心率': 'decrease_crit',
                          '神魂伤害': 'soul_damage_add',
                          '神魂抵抗': 'decrease_soul_damage',
                          '护盾': 'shield',
                          '因果转嫁': 'back_damage',
                          '冰之印记': 'ice_mark'}

base_new_equipment_buff = {'miss_rate': 0,
                           'decrease_miss_rate': 0,
                           'atk': 0,
                           'hp': 0,
                           'crit': 0,
                           'decrease_crit': 0,
                           'soul_damage_add': 0,
                           'decrease_soul_damage': 0,
                           'shield': 0,
                           'back_damage': 0,
                           'ice_mark': 0}


class UserBuffHandle:
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

    async def update_new_equipment(self, item_id: int) -> str:
        item_info = items.get_data_by_item_id(item_id)
        item_type = item_info['item_type']
        item_name = item_info['name']
        item_column = new_equipment_name_def[item_type]
        wearing_item_dict = await self.__select_data([item_column])
        wearing_item_id = wearing_item_dict[item_column] if wearing_item_dict else 0
        if wearing_item_id == item_id:
            return f'道友已经装备了一件{item_name}！请勿重复装备！'
        if wearing_item_id:
            # 已装备其他同类物品，先卸载
            await sql_message.mark_item_state(self.user_id, wearing_item_id, 0)
        await self.__update_data({item_column: item_id})
        await sql_message.mark_item_state(self.user_id, item_id, 1)
        return f'{item_name}装备成功！'

    async def get_all_new_equipment_buff(self) -> NewEquipmentBuffs:
        new_equipment_info = await self.__select_data(
            ['lifebound_treasure',
             'support_artifact',
             'inner_armor',
             'daoist_robe',
             'daoist_boots',
             'spirit_ring'])
        empty_new_equipment_buff = deepcopy(base_new_equipment_buff)
        all_suits_info = {}
        for equipment_id in new_equipment_info.values():
            if not equipment_id:
                continue
            item_info = items.get_data_by_item_id(equipment_id)
            for buff_name, buff_value in item_info['buff'].items():
                buff_name_real = new_equipment_buff_def[buff_name]
                empty_new_equipment_buff[buff_name_real] += buff_value

            # 记录套装效果
            if 'suits' in item_info:
                item_suits = item_info['suits']
                if item_suits in all_suits_info:
                    all_suits_info[item_suits] += 1
                else:
                    all_suits_info[item_suits] = 1

        # 套装效果
        for suits_name, suits_num in all_suits_info.items():
            for unlock_num, suits_buff in items.suits[suits_name]['套组效果'].items():
                if suits_num >= int(unlock_num):
                    for buff_name, buff_value in suits_buff.items():
                        buff_name_real = new_equipment_buff_def[buff_name]
                        empty_new_equipment_buff[buff_name_real] += buff_value

        return empty_new_equipment_buff

    async def get_user_fight_info(self) -> UserFightInfo:
        user_info = await sql_message.get_user_info_with_id(self.user_id)
        user_fight_info, _ = await final_user_data(user_info)
        return user_fight_info

    async def get_user_fight_info_with_buff_info(self) -> tuple[UserFightInfo, dict]:
        user_info = await sql_message.get_user_info_with_id(self.user_id)
        user_fight_info, buff_info = await final_user_data(user_info)
        return user_fight_info, buff_info


async def final_user_data(user_info):
    """
    传入用户当前信息、buff信息,返回最终信息
    """
    # 通过字段名称获取相应的值
    user_id = user_info['user_id']

    # 虚神界属性
    impart_hp_per = 0
    impart_mp_per = 0
    impart_atk_per = 0
    impart_know_per = 0
    impart_burst_per = 0
    impart_data = await xiuxian_impart.get_user_info_with_id(user_id)
    if not impart_data:
        await xiuxian_impart.impart_create_user(user_id)
        impart_data = await xiuxian_impart.get_user_info_with_id(user_id)
    if impart_data:
        impart_hp_per = impart_data['impart_hp_per']
        impart_mp_per = impart_data['impart_mp_per']
        impart_atk_per = impart_data['impart_atk_per']
        impart_know_per = impart_data['impart_know_per']
        impart_burst_per = impart_data['impart_burst_per']

    user_buff = UserBuffDate(user_id)
    user_buff_data_old = await user_buff.buff_info

    # 防具属性实现
    armor_atk_buff = 0
    armor_def_buff = 0
    armor_crit_buff = 0
    if int(user_buff_data_old['armor_buff']) != 0:
        armor_info = items.get_data_by_item_id(user_buff_data_old['armor_buff'])
        armor_atk_buff = armor_info['atk_buff']
        armor_def_buff = armor_info['def_buff']  # 防具减伤
        armor_crit_buff = armor_info['crit_buff']

    # 法器属性实现
    weapon_atk_buff = 0
    weapon_crit_buff = 0
    weapon_def_buff = 0
    weapon_burst_buff = 0
    if int(user_buff_data_old['faqi_buff']) != 0:
        weapon_info = items.get_data_by_item_id(user_buff_data_old['faqi_buff'])
        weapon_atk_buff = weapon_info['atk_buff']
        weapon_crit_buff = weapon_info['crit_buff']
        weapon_burst_buff = weapon_info['critatk']
        weapon_def_buff = weapon_info['def_buff']  # 武器减伤

    # 功法属性实现
    main_hp_buff = 0
    main_mp_buff = 0
    main_atk_buff = 0
    main_def_buff = 0
    main_crit_buff = 0
    main_burst_buff = 0
    main_buff_data = await user_buff.get_user_main_buff_data()
    if main_buff_data:
        main_hp_buff = main_buff_data['hpbuff']
        main_mp_buff = main_buff_data['mpbuff']
        main_atk_buff = main_buff_data['atkbuff']
        main_def_buff = main_buff_data['def_buff']  # 功法减伤
        main_crit_buff = main_buff_data['crit_buff']
        main_burst_buff = main_buff_data['critatk']

    user_buff_data = UserBuffHandle(user_id)
    new_equipment_buff = await user_buff_data.get_all_new_equipment_buff()
    new_equipment_hp_buff = new_equipment_buff['hp']
    new_equipment_atk_buff = new_equipment_buff['atk']
    new_equipment_crit_buff = new_equipment_buff['crit']
    # 传入加成
    user_info['miss_rate'] = int(new_equipment_buff['miss_rate'] * 100)
    user_info['decrease_miss_rate'] = int(new_equipment_buff['decrease_miss_rate'] * 100)
    user_info['decrease_crit'] = int(new_equipment_buff['decrease_crit'] * 100)
    user_info['soul_damage_add'] = new_equipment_buff['soul_damage_add']
    user_info['decrease_soul_damage'] = new_equipment_buff['decrease_soul_damage']
    user_info['shield'] = new_equipment_buff['shield']
    user_info['back_damage'] = new_equipment_buff['back_damage']
    user_info['ice_mark'] = new_equipment_buff['ice_mark']

    # 境界血量补正
    hp_rate = level_data[user_info['level']]["HP"]

    # 最终buff计算
    hp_final_buff = (1 + main_hp_buff + impart_hp_per) * (1 + new_equipment_hp_buff) * hp_rate
    mp_final_buff = (1 + main_mp_buff + impart_mp_per)

    # 获取面板血量加成
    user_info['hp_buff'] = hp_final_buff
    # 战斗中使用血量
    user_info['fight_hp'] = int(user_info['hp'] * hp_final_buff)
    # 战斗中基础最大血量
    user_info['max_hp'] = int(user_info['exp'] * hp_final_buff / 2)
    # 获取面板真元加成
    user_info['mp_buff'] = mp_final_buff
    # 战斗中使用真元
    user_info['fight_mp'] = int(user_info['mp'] * mp_final_buff)
    # 战斗中基础最大真元
    user_info['max_mp'] = int(user_info['exp'] * mp_final_buff)
    # 用于计算神通消耗的真元基础值
    user_info['base_mp'] = int(user_info['exp'])

    user_info['atk'] = int((user_info['atk']
                            * (user_info['atkpractice'] * 0.04 + 1)  # 攻击修炼
                            * (1 + main_atk_buff)  # 功法攻击加成
                            * (1 + weapon_atk_buff)  # 武器攻击加成
                            * (1 + armor_atk_buff)  # 防具攻击加成
                            * (1 + impart_atk_per)  # 传承攻击加成
                            * (1 + new_equipment_atk_buff))  # 六件套装备加成
                           + int(user_buff_data_old['atk_buff']))  # 攻击丹药加成

    user_info['crit'] = int((main_crit_buff
                             + weapon_crit_buff
                             + armor_crit_buff
                             + impart_know_per
                             + new_equipment_crit_buff)
                            * 100)

    user_info['burst'] = (1.5
                          + impart_burst_per
                          + weapon_burst_buff
                          + main_burst_buff)

    user_info['defence'] = round((1 - armor_def_buff)
                                 * (1 - weapon_def_buff)
                                 * (1 - main_def_buff), 2)
    user_info['sub_buff_info'] = await user_buff.get_user_sub_buff_data()
    user_info['sec_buff_info'] = await user_buff.get_user_sec_buff_data()

    buff_info = {'main_buff': main_buff_data,
                 'impart_data': impart_data}

    return user_info, buff_info
