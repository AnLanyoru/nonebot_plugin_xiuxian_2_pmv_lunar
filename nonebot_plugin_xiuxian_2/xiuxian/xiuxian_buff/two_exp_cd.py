from ..xiuxian_limit.limit_database import limit_handle, limit_data


class TWO_EXP_CD(object):

    def find_user(self, user_id):
        """
        匹配词条
        :param user_id:
        """
        limit_dict, is_pass = await limit_data.get_limit_by_user_id(user_id)
        two_exp_num = limit_dict['two_exp_up']
        return two_exp_num

    def add_user(self, user_id) -> bool:
        """
        加入数据
        :param user_id: qq号
        :return: True or False
        """
        limit_handle.update_user_limit(user_id, 5, 1)
        return True

    def re_data(self):
        """
        重置数据
        """
        await limit_data.redata_limit_by_key('two_exp_up')


two_exp_cd = TWO_EXP_CD()
