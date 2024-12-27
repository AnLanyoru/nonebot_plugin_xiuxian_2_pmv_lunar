from ..xiuxian_limit.limit_database import limit_data


class TwoExpCd(object):

    @staticmethod
    async def find_user(user_id):
        """
        匹配词条
        :param user_id:
        """
        limit_dict, is_pass = await limit_data.get_limit_by_user_id(user_id)
        two_exp_num = limit_dict['two_exp_up']
        return two_exp_num

    @staticmethod
    async def re_data():
        """
        重置数据
        """
        await limit_data.redata_limit_by_key('two_exp_up')


two_exp_cd = TwoExpCd()
