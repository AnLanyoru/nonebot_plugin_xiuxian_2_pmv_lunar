from ..xiuxian_database.database_connect import database


async def get_user_world_boss_info(user_id: int) -> dict:
    user_world_boss_info = await database.select(table='world_boss',
                                                 where={'user_id': user_id})
    if not user_world_boss_info:
        data = {'user_id': user_id}
        await database.insert(table='world_boss', create_column=0, **data)
        user_world_boss_info = {
            "user_id": user_id,
            "fight_num": 0,
            "world_id": 0,
            "world_point": 0,
            "fight_damage": 0, }
    return user_world_boss_info


async def update_user_world_boss_info(user_id: int, user_world_boss_info: dict):
    await database.update(table='world_boss',
                          where={'user_id': user_id},
                          **user_world_boss_info)
