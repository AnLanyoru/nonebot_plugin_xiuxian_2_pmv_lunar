all_world_id = [0, 1, 2, 3]


async def get_world_boss_damage_top_limit(database, no: int, world_id: int):
    """获取全部用户id"""
    sql = f"SELECT user_id FROM world_boss WHERE world_id=$1 ORDER BY fight_damage DESC limit {no}"
    async with database.pool.acquire() as db:
        result = await db.fetch(sql, world_id)
        if result:
            return [row[0] for row in result]
        else:
            return None


async def send_world_boss_point(database, user_list, num):
    if not user_list:
        return 0
    sql = 'update world_boss set world_point=world_point+$1 where user_id=$2'
    data = [(num, user_id) for user_id in user_list]
    async with database.pool.acquire() as db:
        await db.executemany(sql, data)


async def send_world_boss_point_all(database, num):
    sql = 'update world_boss set world_point=world_point+$1'
    async with database.pool.acquire() as db:
        await db.execute(sql, num)


async def send_world_boss_point_top_3(database):
    point_num_list = [100, 70, 50]
    for world_id in all_world_id:
        user_list = await get_world_boss_damage_top_limit(database, 3, world_id)
        if not user_list:
            continue
        sql = 'update world_boss set world_point=world_point+$1 where user_id=$2'
        data = [(point, user_id) for point, user_id in zip(point_num_list, user_list)]
        async with database.pool.acquire() as db:
            await db.executemany(sql, data)
