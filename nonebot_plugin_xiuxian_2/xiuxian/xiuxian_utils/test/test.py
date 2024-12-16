import math
import operator
import sys
from decimal import Decimal, InvalidOperation
from timeit import timeit

"""
测试
"""
sys.set_int_max_str_digits(1000000)


def num_len(num):
    """
    获取数字长度
    :param num:
    :return:
    """
    if num:
        if isinstance(num, str):
            num = int(num)
        num = num if operator.gt(num, 0) else operator.neg(num)
        return int(operator.floordiv(num.bit_length(), math.log2(10)))
    else:
        return 1


def num_to(num):
    """
    转换长数字到单位制
    :param num:
    :return:
    """
    if not num:
        return "零"
    if isinstance(num, str):
        num = int(num)
    if operator.gt(0, num):
        fh = "-"
    else:
        fh = ''
    digits = num_len(num)
    level = operator.floordiv(digits, 4) if operator.mod(digits, 4) else operator.sub(operator.floordiv(digits, 4), 1)
    units = ['', '万', '亿', '万亿', '兆', '万兆', '亿兆', '万亿兆', '京', '万京', '亿京', '万亿京', '兆京', '万兆京',
             '亿兆京',
             '万亿兆京', '垓', '万垓', '亿垓', '万亿垓', '兆垓', '万兆垓', '亿兆垓', '万亿兆垓', '京垓', '万京垓',
             '亿京垓',
             '万亿京垓', '兆京垓', '万兆京垓', '亿兆京垓', '万亿兆京垓', '秭', '万秭', '亿秭', '万亿秭', '兆秭',
             '万兆秭', '亿兆秭',
             '万亿兆秭', '京秭', '万京秭', '亿京秭', '万亿京秭', '兆京秭', '万兆京秭', '亿兆京秭', '万亿兆京秭', '垓秭',
             '万垓秭',
             '亿垓秭', '万亿垓秭', '兆垓秭', '万兆垓秭', '亿兆垓秭', '万亿兆垓秭', '京垓秭', '万京垓秭', '亿京垓秭',
             '万亿京垓秭',
             '兆京垓秭', '万兆京垓秭', '亿兆京垓秭', '万亿兆京垓秭', '壤', '万壤', '亿壤', '万亿壤', '兆壤', '万兆壤',
             '亿兆壤',
             '万亿兆壤', '京壤', '万京壤', '亿京壤', '万亿京壤', '兆京壤', '万兆京壤', '亿兆京壤', '万亿兆京壤', '垓壤',
             '万垓壤',
             '亿垓壤', '万亿垓壤', '兆垓壤', '万兆垓壤', '亿兆垓壤', '万亿兆垓壤', '京垓壤', '万京垓壤', '亿京垓壤',
             '万亿京垓壤',
             '兆京垓壤', '万兆京垓壤', '亿兆京垓壤', '万亿兆京垓壤', '秭壤', '万秭壤', '亿秭壤', '万亿秭壤', '兆秭壤',
             '万兆秭壤',
             '亿兆秭壤', '万亿兆秭壤', '京秭壤', '万京秭壤', '亿京秭壤', '万亿京秭壤', '兆京秭壤', '万兆京秭壤',
             '亿兆京秭壤',
             '万亿兆京秭壤', '垓秭壤', '万垓秭壤', '亿垓秭壤', '万亿垓秭壤', '兆垓秭壤', '万兆垓秭壤', '亿兆垓秭壤',
             '万亿兆垓秭壤',
             '京垓秭壤', '万京垓秭壤', '亿京垓秭壤', '万亿京垓秭壤', '兆京垓秭壤', '万兆京垓秭壤', '亿兆京垓秭壤',
             '万亿兆京垓秭壤', ]
    cost = operator.pow(10, operator.mul(4, level))
    last_num = operator.truediv(math.trunc(operator.floordiv(operator.mul(num, 10), cost)), 10)
    level_name = units[level] if operator.lt(level, len(units)) else f'未知{level}'
    return f"{fh}{last_num}{level_name}"


def number_to(num):
    """
    科学计数法
    转换长数字到单位制
    """
    units = [
        '', '万', '亿', '兆', '京', '垓', '秭', '穰', '沟', '涧', '正', '载', '极',
        '恒河沙', '阿僧祗', '那由他', '不思议', '无量大', '万无量大', '亿无量大',
        '兆无量大', '京无量大', '垓无量大', '秭无量大', '穰无量大', '沟无量大',
        '涧无量大', '正无量大', '载无量大', '极无量大',
        '大数', '巨数', '天数', '地数', '宇宙数', '无限数', '无穷数', '无尽数',
        '无边数', '无际数', '无量数', '无垠数', '无极数', '无界数', '无量无边数',
        '微尘数', '星河数', '时光数', '梦境数', '幻象数', '须弥数', '轮回数',
        '虚空数', '混沌数', '宿命数', '因果数', '光明数', '黑暗数', '元素数',
        '宇宙尘埃数', '灵魂数', '智慧数', '命运轨迹数', '女帝', '万女帝', '亿女帝', '兆女帝', '京女帝',
        '垓女帝', '秭女帝', '穰女帝', '沟女帝', '涧女帝', '正女帝', '载女帝', '极女帝',
        '恒河沙女帝', '阿僧祗女帝', '那由他女帝', '不思议女帝', '无量大女帝', '万无量大女帝', '天帝', '万天帝',
        '亿天帝', '兆天帝', '京天帝',
        '垓天帝', '秭天帝', '穰天帝', '沟天帝', '涧天帝', '正天帝', '载天帝', '极天帝',
        '恒河沙天帝', '阿僧祗天帝', '那由他天帝', '不思议天帝', '无量天帝', '万无量天帝', '绝世天帝', '万绝世天帝',
        '亿绝世天帝', '兆绝世天帝', '京绝世天帝',
        '垓绝世天帝', '秭绝世天帝', '穰绝世天帝', '沟绝世天帝', '涧绝世天帝', '正绝世天帝', '载绝世天帝', '极绝世天帝',
        '恒河沙绝世天帝', '阿僧祗绝世天帝', '那由他绝世天帝', '不思议绝世天帝', '无量大绝世天帝', '万无量大绝世天帝',
        '终极天帝', '万终极天帝', '亿终极天帝', '兆终极天帝', '京终极天帝',
        '垓终极天帝', '秭终极天帝', '穰终极天帝', '沟终极天帝', '涧终极天帝', '正终极天帝', '载终极天帝', '极终极天帝',
        '恒河沙终极天帝', '阿僧祗终极天帝', '那由他终极天帝', '不思议终极天帝', '无量大终极天帝', '万无量大终极天帝',
        '欧皇'
    ]

    if num is None:
        return "0"

    try:
        num = Decimal(str(num))
    except InvalidOperation:
        return "无效数字"

    if "e" in str(num):
        num = num.quantize(Decimal('1.0'))

    sign = '-' if num < 0 else ''
    num = abs(num)

    level = 0
    while num >= 10000:
        num /= 10000
        level += 1

    if level >= len(units):
        unknown_level = (level - len(units)) + 1
        return f"{sign}{num.quantize(Decimal('1.0'))}未知{unknown_level}"

    return f"{sign}{num.quantize(Decimal('1.0'))}{units[level]}"


test_dict = {str(x): x * x for x in range(100)}


def check_get(num):
    value = test_dict.get(num)
    if value:
        return True, value
    return False


def check_in(num):
    if num in test_dict:
        value = test_dict[num]
        return True, value
    return False


if __name__ == "__main__":
    while True:
        # number = '9' * int(input())
        number = input()
        use_time_2 = timeit(stmt=f'check_in({number})',
                            globals=globals(), number=1000000)
        print("check_in 耗时:", use_time_2)
        print(check_in(number))
        use_time = timeit(stmt=f'check_get({number})',
                          globals=globals(), number=1000000)
        print("get 耗时:", use_time)
        print(check_get(number))
