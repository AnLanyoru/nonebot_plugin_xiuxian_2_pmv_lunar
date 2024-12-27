from ..xiuxian_limit.limit_database import limit_data, limit_handle


class ImpartPk(object):
    @staticmethod
    async def get_impart_pk_num(user_id):
        limit_dict, is_pass = await limit_data.get_limit_by_user_id(user_id)
        impart_pk_num = limit_dict['impart_pk']
        return impart_pk_num

    @staticmethod
    async def update_impart_pk_num(user_id):
        is_pass = await limit_handle.update_user_limit(user_id, 4, 1)
        return is_pass

    @staticmethod
    async def re_data():
        """
        重置数据
        """
        await limit_data.redata_limit_by_key('impart_pk')


impart_pk = ImpartPk()
