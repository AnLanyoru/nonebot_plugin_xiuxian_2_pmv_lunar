from ..xiuxian_database.database_connect import database


async def create_user_mix_elixir_info(user_id):
    data = {
        "user_id": user_id,
        "farm_num": 0,
        "farm_grow_speed": 0,
        "farm_harvest_time": None,
        "last_alchemy_furnace_data": None,
        "user_fire_control": 0,
        "user_herb_knowledge": 0,
        "user_mix_elixir_exp": 0,
        "user_fire_name": None,
        "user_fire_more_num": 0,
        "user_fire_more_power": 0,
        "mix_elixir_data": None,
        "sum_mix_num": 0}
    await database.insert(table='mix_elixir_info', **data)
    return data


async def get_user_mix_elixir_info(user_id):
    user_mix_elixir_info = await database.select(
        table='mix_elixir_info',
        where={'user_id': user_id},
        need_column=["farm_num",
                     "farm_grow_speed",
                     "farm_harvest_time",
                     "last_alchemy_furnace_data",
                     "user_fire_control",
                     "user_herb_knowledge",
                     "user_mix_elixir_exp",
                     "user_fire_name",
                     "user_fire_more_num",
                     "user_fire_more_power",
                     "mix_elixir_data",
                     "sum_mix_num"])
    if not user_mix_elixir_info:
        user_mix_elixir_info = await create_user_mix_elixir_info(user_id)
    return user_mix_elixir_info
