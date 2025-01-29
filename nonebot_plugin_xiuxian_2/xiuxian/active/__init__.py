import datetime
import json
import random
import asyncpg

from nonebot import on_command, require
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent
)
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .. import DRIVER
from ..xiuxian_config import convert_rank
from ..xiuxian_database.database_connect import database
from ..xiuxian_utils.clean_utils import three_md, msg_handler, number_to, main_md, zips, get_args_num
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.player_fight import boss_fight
from ..xiuxian_utils.utils import check_user
from ..xiuxian_utils.xiuxian2_handle import sql_message, xiuxian_impart

active_daily_reset = require("nonebot_plugin_apscheduler").scheduler
all_problems = [{"题目": "我国的全称是叫什么答案七个字", "答案": ["中华人民共和国"]},
                {"题目": "新中国成立于多少年答案四个数字", "答案": ["1949"]},
                {"题目": "改革开放是哪一年答案四个数字", "答案": ["1978"]},
                {"题目": "我国禁枪是哪一年答案四个数字", "答案": ["1996"]},
                {"题目": "前往灵界需要什么境界答案三个字", "答案": ["天人境"]},
                {"题目": "前往仙界需要什么境界答案五个字", "答案": ["登仙境后期"]},
                {"题目": "凡界塔一共有多少层答案两个数字或者汉字", "答案": ["40", "四十"]},
                {"题目": "什么物品能增加240体力值答案三个字", "答案": ["复元水"]},
                {"题目": "元朝一共统治了多少年答案两个数字", "答案": ["97"]},
                {"题目": "日本投降于多少年答案四个数字", "答案": ["1945"]},
                {"题目": "日本投降赔偿我国多少美金答案三个数字", "答案": ["216"]},
                {"题目": "我国有多少个少数民族答案两个数字", "答案": ["55"]},
                {"题目": "我国由多少个民族组成答案两个数字", "答案": ["56"]},
                {"题目": "圣诞节那天站在槲寄生下方的人，不能拒绝对方什么行为", "答案": ["亲吻"]},
                {"题目": "被称为魔鬼大三角的百慕大三角位于答案三字", "答案": ["大西洋"]},
                {"题目": "琵琶本名批把一词来源于什么答案四字", "答案": ["演奏方式"]},
                {"题目": "端午节五彩线除了青红黑白还有什么颜色答案两字", "答案": ["黄色"]},
                {"题目": "端午节的端字是什么意思两字", "答案": ["开端"]},
                {"题目": "世界第一张圣诞卡诞生于那一年答案四数字", "答案": ["1843"]},
                {"题目": "吸血鬼害怕十字架、狼人怕什么答案一字", "答案": ["银"]},
                {"题目": "大禹治水的故事家喻户晓、大禹治理是那个流域的洪水答案两字", "答案": ["黄河"]},
                {"题目": "埃及最大的金字塔是", "答案": ["胡夫金字塔"]},
                {"题目": "国际象棋哪一方先走", "答案": ["白方"]},
                {"题目": "龙在中国文化中代表祥瑞、在西方文化中代表什么答案两字", "答案": ["邪恶"]},
                {"题目": "沉鱼落雁闭月羞花、中的闭月是指答案两字", "答案": ["貂蝉"]},
                {"题目": "红楼梦中的大家族有几个答案一个数字", "答案": ["4"]},
                {"题目": "但愿人长久千里共婵娟中的婵娟是指什么", "答案": ["月亮"]},
                {"题目": "呼之欲来下一句是", "答案": ["挥之即去"]},
                {"题目": "烽火连三月家书抵万金、古代书信通过邮驿传递、唐代管理这类工作的是答案三字", "答案": ["尚书省"]},
                {"题目": "杜甫的春夜喜雨、随凤潜入夜的下一句是什么", "答案": ["润雨细无声"]},
                {"题目": "虎门销烟是由谁主持的", "答案": ["林则徐"]}, {"题目": "周树人的化名叫什么", "答案": ["鲁迅"]},
                {"题目": "飞上枝头变凤凰最早是指哪位美女", "答案": ["陈圆圆"]},
                {"题目": "曾经沧海难为水下一句是", "答案": ["除却巫山不是云"]},
                {"题目": "文学试试呗成为小李杜的是李商隐和谁", "答案": ["杜牧"]},
                {"题目": "常用语、把台下的犯人称作为", "答案": ["阶下囚"]},
                {"题目": "赫然回首、那人却在灯火阑珊处是指那个节日答案两字", "答案": ["元宵"]},
                {"题目": "每个人只有一个但是10亿人加起来有12个是什么", "答案": ["生肖"]},
                {"题目": "俗语人善被人欺下一句", "答案": ["马善被人骑"]},
                {"题目": "文章合为时而者、歌诗合为事而作，是由谁提出的", "答案": ["白居易"]},
                {"题目": "道高一尺下一句是", "答案": ["魔高一丈"]},
                {"题目": "逢毕生辉中的蓬荜是指房子的", "答案": ["门"]},
                {"题目": "高山仰止的下一句是", "答案": ["景行行止"]},
                {"题目": "我一挥手不带走一片云彩、是出自于徐志摩的", "答案": ["再别康桥"]},
                {"题目": "采菊东篱下、下一句是", "答案": ["悠然见南山"]},
                {"题目": "味摩诘之诗，诗中有画，提到的诗人是", "答案": ["王维"]},
                {"题目": "每逢佳节倍思亲中的佳节是指什么节", "答案": ["重阳"]},
                {"题目": "欲穷千里目下一句是", "答案": ["更上一层楼"]},
                {"题目": "花自飘零水自流、一种思想", "答案": ["两处闲愁"]},
                {"题目": "青青芹蕨下、叠卧双白鱼、无声但呀呀、以气相煦濡隐藏了一个什么成语", "答案": ["相濡以沫"]},
                {"题目": "旗袍起源于我国那个少数民族的服装", "答案": ["满族"]},
                {"题目": "成语、爱屋及乌中的乌是指那种动物", "答案": ["乌鸦"]},
                {"题目": "世界陆地表面最低点是", "答案": ["死海"]}, {"题目": "书法中的柳体是指谁", "答案": ["柳公权"]},
                {"题目": "丑小鸭这个童话故事是谁写的", "答案": ["安徒生"]},
                {"题目": "国学医典中的本草纲目的作者是谁", "答案": ["李时珍"]},
                {"题目": "如果没有空气、在楼上掉落一根羽毛跟一个锤子谁先落地答案两字", "答案": ["同时"]},
                {"题目": "地震时各地震级一样吗", "答案": ["一样"]},
                {"题目": "我国少数民族中、人最多的民族是", "答案": ["壮族"]},
                {"题目": "被西方称为地狱之主的恶魔之王是谁", "答案": ["撒旦"]},
                {"题目": "玄冥二老用什么招式打中了小时候的张无忌", "答案": ["玄冥神掌"]},
                {"题目": "中华民族的摇篮是什么领域答案两字", "答案": ["黄河"]},
                {"题目": "距离圣诞节最近的气是", "答案": ["冬至"]},
                {"题目": "传说中圣诞袜子的主要颜色是", "答案": ["红色"]},
                {"题目": "那种动物的叫声能驱赶凶神、恶鬼", "答案": ["公鸡"]},
                {"题目": "屈原的绝笔之作是", "答案": ["怀沙"]}].copy()

NUM_LIST = [3, 3, 3, 3, 6, 6, 6, 8, 8, 10]


def get_num_new_year():
    return random.choice(NUM_LIST)


async def send_impart_stone(user_id):
    num = get_num_new_year()
    await xiuxian_impart.update_stone_num(impart_num=num, user_id=user_id, type_=1)
    return f'思恋结晶 {num}个', {}


async def send_buff_elixir(user_id):
    num = get_num_new_year()
    elixir_list = [2035, 2026, 2015]
    elixir_id = random.choice(elixir_list)
    elixir_info = items.get_data_by_item_id(elixir_id)
    elixir_name = elixir_info['name']
    return f"{elixir_name} {num}个", {elixir_id: num}


async def send_stam_tool(user_id):
    """复元水 3-10个"""
    num = get_num_new_year()
    item_id = 610004
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


async def send_work(user_id):
    """悬赏衙令 3-10个"""
    num = get_num_new_year()
    item_id = 640001
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


async def send_money(user_id):
    """金元宝 3-10个"""
    num = random.choice([3, 3, 3, 3, 3, 3, 6, 6, 8, 10])
    item_id = 990001
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


async def send_jiao_zi(user_id):
    """饺子 3-10个"""
    num = get_num_new_year()
    item_id = 25012
    item_info = items.get_data_by_item_id(item_id)
    item_name = item_info['name']
    return f"{item_name} {num}个", {item_id: num}


gift_list = {'思恋结晶': send_impart_stone,
             '增益丹药': send_buff_elixir,
             '复元水': send_stam_tool,
             '悬赏衙令': send_work,
             '金元宝': send_money,
             '饺子': send_jiao_zi}

daily_gift_list = {1: {'msg':
                           '年夜饭一桌，年年有余！\r福包 1个\r',
                       'items':
                           {610005: 1, 700001: 1}},
                   2: {'msg':
                           '金元宝十个，金银满堂！\r福包 1个\r',
                       'items':
                           {990001: 10, 700001: 1}},
                   3: {'msg':
                           '汤圆十个，团团圆圆！\r福包 1个\r',
                       'items':
                           {25011: 10, 700001: 1}},
                   4: {'msg':
                           '饺子十个，平安如意！\r福包 2个\r',
                       'items':
                           {25012: 10, 700001: 2}},
                   5: {'msg':
                           '复元水五瓶，精力充沛！\r福包 2个\r',
                       'items':
                           {610004: 5, 700001: 2}},
                   6: {'msg':
                           '悬赏衙令五个，诸事无阻！\r福包 2个\r',
                       'items':
                           {640001: 5, 700001: 2}},
                   7: {'msg':
                           '福包五个，五福临门！！\r',
                       'items':
                           {700001: 5}}}


# 创建一个临时活动数据库
@DRIVER.on_startup
async def new_year_prepare():
    async with database.pool.acquire() as conn:
        try:
            await conn.execute(f"select count(1) from new_year_temp")
        except asyncpg.exceptions.UndefinedTableError:
            await conn.execute(f"""CREATE TABLE "new_year_temp" (
                "user_id" bigint PRIMARY KEY,
                "daily_sign" smallint DEFAULT 0,
                "fight_num" smallint DEFAULT 0,
                "today_answered" smallint DEFAULT 0,
                "all_sign_num" smallint DEFAULT 0,
                "now_problem" json,
                "fight_damage" numeric DEFAULT 0
                );""")


async def get_user_new_year_info(user_id: int) -> dict:
    user_new_year_info = await database.select(table='new_year_temp',
                                               where={'user_id': user_id})
    if not user_new_year_info:
        data = {'user_id': user_id}
        await database.insert(table='new_year_temp', create_column=0, **data)
        user_new_year_info = {
            "user_id": user_id,
            "daily_sign": 0,
            "fight_num": 0,
            "today_answered": 0,
            "all_sign_num": 0,
            "now_problem": None,
            "fight_damage": 0, }
    return user_new_year_info


async def update_user_new_year_info(user_id: int, user_new_year_info: dict):
    await database.update(table='new_year_temp',
                          where={'user_id': user_id},
                          **user_new_year_info)


async def get_new_year_battle_info(user_id):
    """获取Boss战事件的内容"""
    player = await sql_message.get_user_real_info(user_id)
    player['道号'] = player['user_name']
    player['气血'] = player['fight_hp']
    player['攻击'] = player['atk']
    player['真元'] = player['fight_mp']

    new_year_fight_hp = player['max_hp'] * 100
    boss_info = {
        "name": "年兽",
        "气血": new_year_fight_hp,
        "总血量": new_year_fight_hp,
        "攻击": 0,
        "真元": 0,
        "jj": f"{convert_rank()[1][65][:3]}",
        'stone': 1,
        'defence': 0.2
    }

    result, _, final_boss_info, _ = await boss_fight(player, boss_info)  # 未开启，1不写入，2写入

    return result, final_boss_info


async def get_new_year_fight_top():
    """挑战排行"""
    sql = (f"SELECT "
           f"(SELECT max(user_name) FROM user_xiuxian WHERE user_xiuxian.user_id = new_year_temp.user_id) "
           f"as user_name, "
           f"fight_damage "
           f"FROM new_year_temp "
           f"ORDER BY fight_damage DESC "
           f"limit 100")
    async with database.pool.acquire() as db:
        result = await db.fetch(sql)
        result_all = [zips(**result_per) for result_per in result]
        return result_all


# 活动日常刷新
@active_daily_reset.scheduled_job("cron", hour=0, minute=10)
async def active_daily_reset_():
    await database.sql_execute("update new_year_temp set daily_sign=0, fight_num=0, today_answered=0")


new_year_active_menu = on_command("新春", priority=9, permission=GROUP, block=True)
new_year_guess_menu = on_command("猜谜活动", priority=9, permission=GROUP, block=True)
new_year_guess_get = on_command("获取谜题", aliases={"获取题目"}, priority=9, permission=GROUP, block=True)
new_year_guess_answer = on_command("答题", priority=9, permission=GROUP, block=True)
new_year_gift_get = on_command("拆福袋", priority=9, permission=GROUP, block=True)
new_year_daily_gift_get = on_command("新春祈愿", priority=8, permission=GROUP, block=True)
new_year_fight_menu = on_command("年兽菜单", priority=9, permission=GROUP, block=True)
new_year_fight = on_command("驱逐年兽", priority=9, permission=GROUP, block=True)
new_year_fight_top = on_command("年兽伤害排行", priority=9, permission=GROUP, block=True)

time_set_new_year = on_command('逆转新春', priority=15, permission=SUPERUSER, block=True)


@new_year_fight_top.handle(parameterless=[Cooldown(at_sender=False)])
async def new_year_fight_top_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """年兽伤害排行榜"""
    page = get_args_num(args, 1, default=1)
    lt_rank = await get_new_year_fight_top()
    long_rank = len(lt_rank)
    page_all = (long_rank // 20) + 1 if long_rank % 20 != 0 else long_rank // 20  # 总页数
    if page_all < page != 1:
        msg = f"挑战排行榜没有那么广阔！！！"
        await bot.send(event=event, message=msg)
        await new_year_fight_top.finish()
    if long_rank != 0:
        # 获取页数物品数量
        item_num = page * 20 - 20
        item_num_end = item_num + 20
        lt_rank = lt_rank[item_num:item_num_end]
        top_msg = f"✨【年兽】伤害排行TOP{item_num_end}✨"
        msg = ''
        num = item_num
        for i in lt_rank:
            i = list(i.values())
            num += 1
            msg += f"第{num}位 {i[0]} 最高造成:{number_to(i[1])}伤害\r"
        msg += f"第 {page}/{page_all} 页"
        msg = main_md(top_msg, msg,
                      '主菜单', '新春菜单',
                      '猜谜活动', '猜谜活动菜单',
                      '查看奖励规则', '年兽菜单',
                      '前往驱逐年兽', '驱逐年兽')
    else:
        msg = f"该排行榜空空如也！"
    await bot.send(event=event, message=msg)
    await new_year_fight_top.finish()


@new_year_fight.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_fight_(bot: Bot, event: GroupMessageEvent):
    """驱逐年兽"""
    now_day = datetime.date.today()
    if not (datetime.date(year=2025, month=1, day=28) < now_day):
        msg = "活动尚未开始！！"
        await bot.send(event=event, message=msg)
        await new_year_fight.finish()

    if not (datetime.date(year=2025, month=2, day=5) > now_day):
        msg = "活动已结束！！"
        await bot.send(event=event, message=msg)
        await new_year_fight.finish()

    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']
    user_new_year_info = await get_user_new_year_info(user_id)
    user_name = user_info['user_name']
    if user_new_year_info['fight_num'] > 2:
        msg = f"道友今天已经为驱逐年兽做出了足够大的奉献啦！！\r去看看别的活动吧\r"
        msg = three_md(msg, "猜谜活动", "猜谜活动菜单", "\r —— 答题成功将获得福袋奖励！！\r",
                       "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_fight.finish()

    msg_list, boss_info = await get_new_year_battle_info(user_id)
    new_damage = boss_info['总血量'] - boss_info['气血']
    user_new_year_info['fight_num'] += 1
    user_new_year_info['fight_damage'] = max(user_new_year_info['fight_damage'], new_damage)
    await update_user_new_year_info(user_id, user_new_year_info)
    text = msg_handler(msg_list)
    msg = f"{user_name}道友全力施为，对年兽造成{number_to(new_damage)}伤害！！"
    msg = main_md(
        msg, text,
        '主菜单', '新春菜单',
        '猜谜活动', '猜谜活动菜单',
        '查看排行', '年兽伤害排行',
        '再次驱逐', '驱逐年兽')
    await bot.send(event=event, message=msg)
    await new_year_fight.finish()


@new_year_fight_menu.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_fight_menu_(bot: Bot, event: GroupMessageEvent):
    """年兽活动菜单！！"""
    now_day = datetime.date.today()
    if not (datetime.date(year=2025, month=1, day=28) < now_day):
        msg = "活动尚未开始！！"
        await bot.send(event=event, message=msg)
        await new_year_fight_menu.finish()

    if not (datetime.date(year=2025, month=2, day=5) > now_day):
        msg = "活动已结束！！"
        await bot.send(event=event, message=msg)
        await new_year_fight_menu.finish()

    _, user_info, _ = await check_user(event)

    user_name = user_info['user_name']
    msg = (f"祝{user_name}道友新春快乐！！\r"
           f"驱逐年兽活动规则：\r"
           f"每位道友每日可以挑战三次年兽，记录伤害最高的一次战斗\r"
           f"将于挑战活动结束后为各位道友发放与伤害排名对应的福袋奖励\r"
           f"奖励内容如下：\r"
           f"前50位：福袋5，前100位：福袋3\r"
           f"无论伤害如何，凡造成伤害者均发放参与奖：福袋*2！\r"
           f"高贡献额外奖励：\r"
           f"1位：福袋50，2位：福袋30，3位：福袋20，4-10位：福袋10\r")
    msg = three_md(msg, "开始驱逐年兽", "驱逐年兽", "\r —— 共同击退年兽获取福袋奖励！！\r",
                   "驱逐年兽排行", "年兽伤害排行", "\r —— 查看为驱逐年兽做出巨大贡献的玩家！！\r",
                   "主菜单", "新春菜单", "\r —— 查看所有活动！！\r"
                                         "新春活动于大年初一开放，初七过后结束，祈愿签到活动额外持续七日！")
    await bot.send(event=event, message=msg)
    await new_year_fight_menu.finish()


@time_set_new_year.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def time_set_new_year_(bot: Bot, event: GroupMessageEvent):
    """春节活动重载！！"""

    _, user_info, _ = await check_user(event)
    await database.sql_execute("update new_year_temp set daily_sign=0, fight_num=0, today_answered=0")
    msg = f"又是一年好新春！！"
    await bot.send(event=event, message=msg)
    await time_set_new_year.finish()


@new_year_daily_gift_get.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_daily_gift_get_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """新春签到"""

    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']
    user_name = user_info['user_name']
    user_new_year_info = await get_user_new_year_info(user_id)
    is_sign = user_new_year_info['daily_sign']
    if is_sign:
        msg = f"道友今天已经签到过啦，快去参与其他新春活动吧！！\r"
        msg = three_md(msg, "查看福包奖励", "查二零二五新春福包", "\r —— 查看所有福包内含奖励！！\r",
                       "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_daily_gift_get.finish()

    all_sign_num = user_new_year_info['all_sign_num']
    if all_sign_num > 6:
        msg = f"道友已经完成全部签到啦，新春快乐！！新的一年里顺顺利利，开开心心！！\r"
        msg = three_md(msg, "查看福包奖励", "查二零二五新春福包", "\r —— 查看所有福包内含奖励！！\r",
                       "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_daily_gift_get.finish()
    user_new_year_info['all_sign_num'] += 1
    user_new_year_info['daily_sign'] = 1
    gift_today = daily_gift_list[user_new_year_info['all_sign_num']]
    item_send = gift_today['items']
    item_msg = gift_today['msg']
    await sql_message.send_item(user_id, item_send, 1)
    await update_user_new_year_info(user_id, user_new_year_info)
    msg = f"{user_name}道友新年快乐！！\r今天是道友第{all_sign_num + 1}次新春祈愿\r获取了以下奖励：\r" + item_msg
    msg = three_md(msg, "查看驱逐年兽排行", "年兽伤害排行", "\r —— 查看为驱逐年兽做出巨大贡献的玩家！！\r",
                   "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                   f"去拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
    await bot.send(event=event, message=msg)
    await new_year_daily_gift_get.finish()


@new_year_gift_get.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_gift_get_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """拆福包"""

    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']
    user_name = user_info['user_name']
    new_year_gift_info = await sql_message.get_item_by_good_id_and_user_id(user_id, 700001)
    if not new_year_gift_info:
        msg = f"道友还没有福包呢，去参与新春活动获取一些吧！！\r"
        msg = three_md(msg, "查看福包奖励", "查二零二五新春福包", "\r —— 查看所有福包内含奖励！！\r",
                       "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_gift_get.finish()
    if (gift_num := new_year_gift_info.get('goods_num')) <= 0:
        msg = f"道友的福包不够呢，去参与新春活动多获取一些吧！！\r"
        msg = three_md(msg, "查看福包奖励", "查二零二五新春福包", "\r —— 查看所有福包内含奖励！！\r",
                       "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_gift_get.finish()

    all_gift = list(gift_list.keys())
    random.shuffle(all_gift)
    msg_list = []
    item_send = {}
    for gift_type in all_gift[:3]:
        msg_per, item_dict = await gift_list[gift_type](user_id)
        item_send.update(item_dict)
        msg_list.append(msg_per)
    await sql_message.send_item(user_id, item_send, 1)
    await sql_message.update_back_j(user_id, 700001, 1, 2)
    msg = f"恭喜{user_name}道友打开福包获取了以下奖励：\r" + '\r'.join(msg_list) + '\r'
    msg = three_md(msg, "查看驱逐年兽排行", "年兽伤害排行", "\r —— 查看为驱逐年兽做出巨大贡献的玩家！！\r",
                   "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                   f"继续拆福袋(余剩{gift_num - 1})", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
    await bot.send(event=event, message=msg)
    await new_year_gift_get.finish()


@new_year_guess_answer.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_guess_answer_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """答题"""
    now_day = datetime.date.today()
    if not (datetime.date(year=2025, month=1, day=28) < now_day):
        msg = "活动尚未开始！！"
        await bot.send(event=event, message=msg)
        await new_year_guess_answer.finish()

    if not (datetime.date(year=2025, month=2, day=5) > now_day):
        msg = "活动已结束！！"
        await bot.send(event=event, message=msg)
        await new_year_guess_answer.finish()

    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']
    user_new_year_info = await get_user_new_year_info(user_id)
    user_problem = user_new_year_info['now_problem']
    user_name = user_info['user_name']
    if not user_problem:
        msg = f"{user_name}道友暂时没有谜题需要解答！！\r"
        msg = three_md(msg, "获取题目", "获取题目", "\r —— 答题成功将获得福袋奖励！！\r",
                       "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_guess_answer.finish()

    problem = json.loads(user_new_year_info['now_problem'])
    answer = args.extract_plain_text()
    if answer not in problem['答案']:
        msg = f"{user_name}道友的答案不对哦，道友再好好猜猜看吧\r"
        msg = three_md(msg, "继续答题", "答题", "\r —— 答题成功将获得福袋奖励！！\r",
                       "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_guess_answer.finish()

    user_new_year_info['now_problem'] = None
    await update_user_new_year_info(user_id, user_new_year_info)
    await sql_message.send_item(user_id, {700001: 1}, is_bind=1)
    msg = (f"恭喜{user_name}道友成功答对谜题！！\r"
           f"获得了：福袋 1个\r"
           f" —— 快去拆福袋看看里面有什么好东西吧！！\r")
    msg = three_md(msg, "继续答题", "获取题目", "\r —— 答题成功将获得福袋奖励！！\r",
                   "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                   "拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
    await bot.send(event=event, message=msg)
    await new_year_guess_answer.finish()


@new_year_guess_get.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_guess_get_(bot: Bot, event: GroupMessageEvent):
    """获取谜题"""
    now_day = datetime.date.today()
    if not (datetime.date(year=2025, month=1, day=28) < now_day):
        msg = "活动尚未开始！！"
        await bot.send(event=event, message=msg)
        await new_year_guess_get.finish()

    if not (datetime.date(year=2025, month=2, day=5) > now_day):
        msg = "活动已结束！！"
        await bot.send(event=event, message=msg)
        await new_year_guess_get.finish()

    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']
    user_new_year_info = await get_user_new_year_info(user_id)
    user_problem = user_new_year_info['now_problem']
    user_name = user_info['user_name']
    if user_problem:
        problem = json.loads(user_problem)
        msg = (f"道友已经有谜题啦！！\r"
               f"{user_name}道友的谜题：\r"
               f"{problem['题目']}\r")
        msg = three_md(msg, "答题", "答题", "\r —— 答题成功将获得福袋奖励！！\r",
                       "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_guess_get.finish()
    if user_new_year_info['today_answered'] > 2:
        msg = f"道友今天已经答了够多的谜题啦！！\r去看看别的活动吧\r"
        msg = three_md(msg, "驱逐年兽", "年兽菜单", "\r —— 驱逐年兽获得福袋奖励！！\r",
                       "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                       "拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
        await bot.send(event=event, message=msg)
        await new_year_guess_get.finish()

    problem = random.choice(all_problems)
    user_new_year_info['now_problem'] = json.dumps(problem)
    user_new_year_info['today_answered'] += 1
    await update_user_new_year_info(user_id, user_new_year_info)
    msg = (f"{user_name}道友的谜题：\r"
           f"{problem['题目']}\r")
    msg = three_md(msg, "答题", "答题", "\r —— 答题成功将获得福袋奖励！！\r",
                   "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                   "拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！")
    await bot.send(event=event, message=msg)
    await new_year_guess_get.finish()


@new_year_guess_menu.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_guess_menu_(bot: Bot, event: GroupMessageEvent):
    """猜谜活动菜单！！"""
    now_day = datetime.date.today()
    if not (datetime.date(year=2025, month=1, day=28) < now_day):
        msg = "活动尚未开始！！"
        await bot.send(event=event, message=msg)
        await new_year_guess_menu.finish()

    if not (datetime.date(year=2025, month=2, day=5) > now_day):
        msg = "活动已结束！！"
        await bot.send(event=event, message=msg)
        await new_year_guess_menu.finish()

    _, user_info, _ = await check_user(event)

    user_name = user_info['user_name']
    msg = (f"祝{user_name}道友新春快乐！！\r"
           f"新春猜谜菜单：\r")
    msg = three_md(msg, "开始猜谜", "获取谜题", "\r —— 参加答题获得福袋奖励！！\r",
                   "主菜单", "新春菜单", "\r —— 查看全部新春活动！！\r",
                   "拆福袋", "拆福袋", "\r —— 打开福袋获取丰厚奖励！！\r"
                                       "新春活动于大年初一开放，初七过后结束，祈愿签到活动额外持续七日！")
    await bot.send(event=event, message=msg)
    await new_year_guess_menu.finish()


@new_year_active_menu.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def new_year_active_menu_(bot: Bot, event: GroupMessageEvent):
    """春节活动菜单！！"""

    _, user_info, _ = await check_user(event)
    user_id = user_info['user_id']
    user_name = user_info['user_name']
    user_new_year_info = await get_user_new_year_info(user_id)
    new_year_pray_num = user_new_year_info['daily_sign']
    fight_num = user_new_year_info['fight_num']
    today_answered = user_new_year_info['today_answered']
    msg = (f"祝{user_name}道友新春快乐！！\r"
           f"进行中的新春活动：\r")
    msg = three_md(msg, f"新春猜谜(今日{today_answered}/3)", "猜谜活动菜单", "\r —— 参加答题获得福袋奖励！！\r",
                   f"驱逐年兽(今日{fight_num}/3)", "年兽菜单", "\r —— 共同击退年兽获取福袋奖励！！\r",
                   f"新春祈愿(今日{new_year_pray_num}/1)", "新春祈愿", "\r —— 每日签到获得丰厚奖励！！\r"
                                                                       "新春活动于大年初一开放，初七过后结束，祈愿签到活动额外持续七日！")
    await bot.send(event=event, message=msg)
    await new_year_active_menu.finish()
