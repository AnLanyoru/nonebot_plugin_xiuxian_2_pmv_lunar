import json

from .. import DRIVER
from ..xiuxian_database.database_connect import database
from ..xiuxian_database.database_util import limit_db, tower_db, store_db, main_db, impart_db, all_table_data_move, \
    move_bank_json_data, move_mix_elixir_json_data, move_move_data, move_work_data, read_impart_person_data
from ..xiuxian_utils.xiuxian2_handle import sql_message


# 数据转移工具
@DRIVER.on_startup
async def move_bank_data():
    move_data = 1
    if move_data:
        print("迁移工具加载。")
        print("迁移开始")
        # sqlite数据迁移道具
        await all_table_data_move(database, limit_db)
        await all_table_data_move(database, tower_db)
        await all_table_data_move(database, store_db, values_type_check=True)
        await all_table_data_move(database, main_db, values_type_check=True)
        await all_table_data_move(database, impart_db)

        # json数据迁移
        # 传承卡图
        img_tp: dict = read_impart_person_data()
        update_data = []
        for user_id, cards in img_tp.items():
            update_data.append((json.dumps(cards), user_id))
        pool = database.pool
        sql = 'update xiuxian_impart set cards=$1 where user_id=$2'
        async with pool.acquire() as conn:
            await conn.executemany(sql, update_data)
        # 灵庄部分
        all_user_id = await sql_message.get_all_user_id()
        await move_bank_json_data(database, all_user_id)
        await move_mix_elixir_json_data(database, all_user_id)

        # 移动数据
        all_user_moving_id = await sql_message.get_all_user_moving_id()
        await move_move_data(database, all_user_moving_id)

        # 悬赏令数据
        all_user_working_id = await sql_message.get_all_user_working_id()
        await move_work_data(database, all_user_working_id)

        # 获取序列最大值
        print('序列预处理')
        max_ids = []
        columns = [('buff_info', 'id'),
                   ('sects', 'sect_id'),
                   ('user_xiuxian', 'id'),
                   ('xiuxian_impart', 'id')]
        for table, column in columns:
            result = await database.select(table=table, where={}, need_column=[f'max({column})'])
            print(result)
            result = result['max'] + 1
            max_ids.append(result)

        # 处理序列
        print('开始处理序列')
        sqls = ["alter sequence buff_info_id_seq restart with {}",
                "alter sequence sects_sect_id_seq restart with {}",
                "alter sequence user_xiuxian_id_seq restart with {}",
                "alter sequence xiuxian_impart_id_seq restart with {}"]
        for sql, max_id in zip(sqls, max_ids):
            await database.sql_execute(sql.format(max_id))
        print('序列处理成功')
    else:
        print('默认不加载迁移数据工具，'
              '请前往nonebot_plugin_xiuxian_2/xiuxian/xiuxian_move_data/__init__.py'
              '配置数据迁移工具')
