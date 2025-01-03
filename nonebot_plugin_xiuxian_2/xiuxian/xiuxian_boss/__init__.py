from .bossconfig import CONFIG

try:
    import ujson as json
except ImportError:
    import json
import re
from pathlib import Path
import random
import os
from nonebot.rule import Rule
from nonebot import on_command, require
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    GROUP_ADMIN,
    GROUP_OWNER,
    ActionFailed,
    MessageSegment
)
from ..xiuxian_utils.lay_out import Cooldown
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from ..xiuxian_utils.xiuxian2_handle import (
    sql_message, leave_harm_time
)
from ..xiuxian_utils.other_set import OtherSet
from ..xiuxian_config import convert_rank, XiuConfig
from .makeboss import createboss, createboss_jj
from .old_boss_info import old_boss_info
from ..xiuxian_utils.player_fight import boss_fight
from ..xiuxian_utils.item_json import items

from ..xiuxian_utils.utils import (
    number_to, check_user,
    get_msg_pic, send_msg_handler
)
from .. import DRIVER

# boss定时任务
require('nonebot_plugin_apscheduler')
config = CONFIG
cache_help = {}
group_boss = {}
groups = config['open']
battle_flag = {}


# 替换模块


def check_rule_bot_boss() -> Rule:  # 消息检测，是超管，群主或者指定的qq号传入的消息就响应，其他的不响应
    async def _check_bot_(bot: Bot, event: GroupMessageEvent) -> bool:
        if (event.sender.role == "admin" or
                event.sender.role == "owner"):
            return True
        else:
            return False

    return Rule(_check_bot_)


def check_rule_bot_boss_s() -> Rule:  # 消息检测，是超管或者指定的qq号传入的消息就响应，其他的不响应
    async def _check_bot_(bot: Bot, event: GroupMessageEvent) -> bool:
        if event.get_user_id() in bot.config.superusers:
            return True
        else:
            return False

    return Rule(_check_bot_)


boss_info = on_command("查询世界boss",
                       aliases={"查询世界Boss", "查询世界BOSS", "查询boss", "世界Boss查询", "世界BOSS查询", "boss查询"},
                       priority=6, permission=GROUP, block=True)
set_group_boss = on_command("世界boss", aliases={"世界Boss", "世界BOSS"}, priority=13,
                            permission=GROUP and (SUPERUSER | GROUP_ADMIN | GROUP_OWNER), block=True)
battle = on_command("讨伐boss", aliases={"讨伐世界boss", "讨伐Boss", "讨伐BOSS", "讨伐世界Boss", "讨伐世界BOSS"},
                    priority=6,
                    permission=GROUP, block=True)
boss_help = on_command("世界boss帮助", aliases={"世界Boss帮助", "世界BOSS帮助"}, priority=5, block=True)
boss_integral_info = on_command("世界积分查看", aliases={"查看世界积分", "查询世界积分", "世界积分查询"}, priority=10,
                                permission=GROUP, block=True)
boss_integral_use = on_command("世界积分兑换", priority=6, permission=GROUP, block=True)

boss_time = config["Boss生成时间参数"]
__boss_help__ = f"""
世界Boss帮助信息:
暂未开放
指令：
查询世界boss:
>查询本群全部世界Boss,可加Boss编号查询对应Boss信息
讨伐boss:
>讨伐世界Boss,必须加Boss编号
世界积分查看:
>查看自己的世界积分,和世界积分兑换商品
世界积分兑换+编号：
>兑换对应的商品，可以批量购买
""".strip()


@DRIVER.on_startup
async def read_boss_():
    global group_boss
    group_boss.update(old_boss_info.read_boss_info())
    logger.opt(colors=True).info(f"<green>历史boss数据读取成功</green>")


@DRIVER.on_shutdown
async def save_boss_():
    old_boss_info.save_boss(group_boss)
    logger.opt(colors=True).info(f"<green>boss数据已保存</green>")


@boss_help.handle(parameterless=[Cooldown(at_sender=False)])
async def boss_help_(bot: Bot, event: GroupMessageEvent):
    msg = __boss_help__
    await bot.send(event=event, message=msg)
    await boss_help.finish()


@battle.handle(parameterless=[Cooldown(stamina_cost=60, at_sender=False)])
async def battle_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """讨伐世界boss"""
    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    await sql_message.update_last_check_info_time(user_id)  # 更新查看修仙信息时间
    msg = args.extract_plain_text().strip()
    group_id = str(event.group_id)
    boss_num = re.findall(r"\d+", msg)  # boss编号

    isInGroup = isInGroups(event)
    if not isInGroup:  # 不在配置表内
        msg = f"世界Boss暂未开放，敬请期待!"
        await sql_message.update_user_stamina(user_id, 60, 1)
        await bot.send(event=event, message=msg)
        await battle.finish()

    if boss_num:
        boss_num = int(boss_num[0])
    else:
        msg = f"请输入正确的世界Boss编号!"
        await sql_message.update_user_stamina(user_id, 60, 1)
        await bot.send(event=event, message=msg)
        await battle.finish()
    bosss = None
    try:
        bosss = group_boss[group_id]
    except:
        msg = f"本群尚未生成世界Boss,请等待世界boss刷新!"
        await sql_message.update_user_stamina(user_id, 60, 1)
        await bot.send(event=event, message=msg)
        await battle.finish()

    if not bosss:
        msg = f"本群尚未生成世界Boss,请等待世界boss刷新!"
        await sql_message.update_user_stamina(user_id, 60, 1)
        await bot.send(event=event, message=msg)
        await battle.finish()

    index = len(group_boss[group_id])

    if not (0 < boss_num <= index):
        msg = f"请输入正确的世界Boss编号!"
        await bot.send(event=event, message=msg)
        await battle.finish()

    if user_info['hp'] is None or user_info['hp'] == 0:
        # 判断用户气血是否为空
        await sql_message.update_user_hp(user_id)

    if user_info['hp'] <= user_info['exp'] / 10:
        time = leave_harm_time(user_id)
        msg = f"重伤未愈，动弹不得！距离脱离危险还需要{time}分钟！\r"
        msg += f"请道友进行闭关，或者使用药品恢复气血，不要干等，没有自动回血！！！"
        await sql_message.update_user_stamina(user_id, 60, 1)
        await bot.send(event=event, message=msg)
        await battle.finish()

    user_info = await sql_message.get_user_real_info(user_id)
    player = {'user_id': user_info['user_id'],
              '道号': user_info['user_name'],
              '气血': user_info['hp'],
              'max_hp': user_info['max_hp'],
              'hp_buff': user_info['hp_buff'],
              '攻击': user_info['atk'],
              '真元': user_info['mp'],
              'max_mp': user_info['max_mp'],
              'mp_buff': user_info['mp_buff'],
              'level': user_info['level'],
              'exp': user_info['exp']
              }

    bossinfo = group_boss[group_id][boss_num - 1]
    if bossinfo['jj'] == '零':
        boss_rank = convert_rank((bossinfo['jj']))[0]
    else:
        boss_rank = convert_rank((bossinfo['jj'] + '中期'))[0]
    user_rank = convert_rank(user_info['level'])[0]
    if user_rank - boss_rank >= 12:
        msg = f"道友已是{user_info['level']}之人，妄图抢小辈的Boss，可耻！"
        await bot.send(event=event, message=msg)
        await battle.finish()
    boss_old_hp = bossinfo['气血']  # 打之前的血量
    more_msg = ''
    battle_flag[group_id] = True
    result, victor, bossinfo_new, get_stone = await boss_fight(player, bossinfo)
    if victor == "Boss赢了":
        group_boss[group_id][boss_num - 1] = bossinfo_new
        await sql_message.update_ls(user_id, get_stone, 1)
        # 新增boss战斗积分点数
        boss_now_hp = bossinfo_new['气血']  # 打之后的血量
        boss_all_hp = bossinfo['总血量']  # 总血量
        boss_integral = int(((boss_old_hp - boss_now_hp) / boss_all_hp) * 240)
        if boss_integral < 1:  # 摸一下不给
            boss_integral = 0
        if user_info['root'] == "器师":
            boss_integral = int(boss_integral * (1 + (user_rank - boss_rank)))
            points_bonus = int(80 * (user_rank - boss_rank))
            more_msg = f"道友低boss境界{user_rank - boss_rank}层，获得{points_bonus}%积分加成！"

        user_boss_fight_info = get_user_boss_fight_info(user_id)
        user_boss_fight_info['boss_integral'] += boss_integral
        save_user_boss_fight_info(user_id, user_boss_fight_info)

        msg = f"道友不敌{bossinfo['name']}，重伤逃遁，临逃前收获灵石{get_stone}枚，{more_msg}获得世界积分：{boss_integral}点 "
        if user_info['root'] == "器师" and boss_integral < 0:
            msg += f"\r如果出现负积分，说明你境界太高了，玩器师就不要那么高境界了！！！"
        battle_flag[group_id] = False
        try:
            await send_msg_handler(bot, event, result)
        except ActionFailed:
            msg += f"Boss战消息发送错误,可能被风控!"
        await bot.send(event=event, message=msg)
        await battle.finish()

    elif victor == "群友赢了":
        # 新增boss战斗积分点数
        boss_all_hp = bossinfo['总血量']  # 总血量
        boss_integral = int((boss_old_hp / boss_all_hp) * 240)
        if user_info['root'] == "器师":
            boss_integral = int(boss_integral * (1 + (user_rank - boss_rank)))
            points_bonus = int(80 * (user_rank - boss_rank))
            more_msg = f"道友低boss境界{user_rank - boss_rank}层，获得{points_bonus}%积分加成！"

        drops_id, drops_info = boss_drops(user_rank, boss_rank, bossinfo, user_info)
        if drops_id is None:
            drops_msg = " "
        elif boss_rank < convert_rank('合道境中期')[0]:
            drops_msg = f"boss的遗骸上好像有什么东西， 凑近一看居然是{drops_info['name']}！ "
            await sql_message.send_back(user_info['user_id'], drops_info['id'], drops_info['name'], drops_info['type'],
                                        1)
        else:
            drops_msg = " "

        group_boss[group_id].remove(group_boss[group_id][boss_num - 1])
        battle_flag[group_id] = False
        await sql_message.update_ls(user_id, get_stone, 1)
        user_boss_fight_info = get_user_boss_fight_info(user_id)
        user_boss_fight_info['boss_integral'] += boss_integral
        save_user_boss_fight_info(user_id, user_boss_fight_info)
        msg = f"恭喜道友击败{bossinfo['name']}，收获灵石{get_stone}枚，{more_msg}获得世界积分：{boss_integral}点!{drops_msg}"
        if user_info['root'] == "器师" and boss_integral < 0:
            msg += f"\r如果出现负积分，说明你这器师境界太高了(如果总世界积分为负数，会帮你重置成0)，玩器师就不要那么高境界了！！！"
        try:
            await send_msg_handler(bot, event, result)
        except ActionFailed:
            msg += f"Boss战消息发送错,可能被风控!"
        await bot.send(event=event, message=msg)
        await battle.finish()


@boss_info.handle(parameterless=[Cooldown(at_sender=False)])
async def boss_info_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """查询世界boss"""
    # 这里曾经是风控模块，但是已经不再需要了
    group_id = str(event.group_id)
    isInGroup = isInGroups(event)
    if not isInGroup:  # 不在配置表内
        msg = f"世界Boss暂未开放，敬请期待!"
        await bot.send(event=event, message=msg)
        await boss_info.finish()
    bosss = None
    try:
        bosss = group_boss[group_id]
    except:
        msg = f"本群尚未生成世界Boss,请等待世界boss刷新!"
        await bot.send(event=event, message=msg)
        await boss_info.finish()

    msg = args.extract_plain_text().strip()
    boss_num = re.findall(r"\d+", msg)  # boss编号

    if not bosss:
        msg = f"本群尚未生成世界Boss,请等待世界boss刷新!"
        await bot.send(event=event, message=msg)
        await boss_info.finish()

    Flag = False  # True查对应Boss
    if boss_num:
        boss_num = int(boss_num[0])
        index = len(group_boss[group_id])
        if not (0 < boss_num <= index):
            msg = f"请输入正确的世界Boss编号!"
            await bot.send(event=event, message=msg)
            await boss_info.finish()

        Flag = True

    bossmsgs = ""
    if Flag:  # 查单个Boss信息
        boss = group_boss[group_id][boss_num - 1]
        bossmsgs = f'''
世界Boss:{boss['name']}
境界：{boss['jj']}
总血量：{number_to(boss['总血量'])}
剩余血量：{number_to(boss['气血'])}
攻击：{number_to(boss['攻击'])}
携带灵石：{number_to(boss['stone'])}
        '''
        msg = bossmsgs
        if int(boss["气血"] / boss["总血量"]) < 0.5:
            boss_name = boss["name"] + "_c"
        else:
            boss_name = boss["name"]
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\r" + msg, boss_name=boss_name)
            await bot.send(event=event, message=MessageSegment.image(pic))
        else:
            await bot.send(event=event, message=msg)
        await boss_info.finish()
    else:
        i = 1
        for boss in bosss:
            bossmsgs += f"编号{i}、{boss['jj']}Boss:{boss['name']} \r"
            i += 1
        msg = bossmsgs
        await bot.send(event=event, message=msg)
        await boss_info.finish()


@set_group_boss.handle(parameterless=[Cooldown(at_sender=False)])
async def set_group_boss_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """设置群世界boss开关"""
    # 这里曾经是风控模块，但是已经不再需要了
    mode = args.extract_plain_text().strip()
    group_id = str(event.group_id)
    isInGroup = isInGroups(event)  # True在，False不在

    if mode == '开启':
        if isInGroup:
            msg = f"本群已开启世界Boss,请勿重复开启!"
            await bot.send(event=event, message=msg)
            await set_group_boss.finish()
        else:
            info = {
                str(group_id): {
                    "hours": config['Boss生成时间参数']["hours"],
                    "minutes": config['Boss生成时间参数']["minutes"]
                }
            }
            config['open'].update(info)
            msg = f"已开启本群世界Boss!"
            await bot.send(event=event, message=msg)
            await set_group_boss.finish()

    elif mode == '关闭':
        if isInGroup:
            msg = f"已关闭本群世界Boss!"
            await bot.send(event=event, message=msg)
            await set_group_boss.finish()
        else:
            msg = f"本群未开启世界Boss!"
            await bot.send(event=event, message=msg)
            await set_group_boss.finish()

    elif mode == '':
        msg = __boss_help__
        await bot.send(event=event, message=msg)
        await set_group_boss.finish()
    else:
        msg = f"请输入正确的指令:世界boss开启或关闭!"
        await bot.send(event=event, message=msg)
        await set_group_boss.finish()


@boss_integral_info.handle(parameterless=[Cooldown(at_sender=False)])
async def boss_integral_info_(bot: Bot, event: GroupMessageEvent):
    """世界积分商店"""
    # 这里曾经是风控模块，但是已经不再需要了
    isInGroup, user_info, msg = await check_user(event)
    if not isInGroup:
        await bot.send(event=event, message=msg)
        await boss_integral_info.finish()

    user_id = user_info['user_id']
    isInGroup = isInGroups(event)
    if not isInGroup:  # 不在配置表内
        msg = f"世界Boss暂未开放，敬请期待!"
        await bot.send(event=event, message=msg)
        await boss_integral_info.finish()

    user_boss_fight_info = get_user_boss_fight_info(user_id)
    boss_integral_shop = config['世界积分商品']
    l_msg = [f"道友目前拥有的世界积分：{user_boss_fight_info['boss_integral']}点"]
    if boss_integral_shop != {}:
        for k, v in boss_integral_shop.items():
            msg = f"编号:{k}\r"
            msg += f"描述：{v['desc']}\r"
            msg += f"所需世界积分：{v['cost']}点"
            l_msg.append(msg)
    else:
        l_msg.append(f"世界积分商店内空空如也！")
    await send_msg_handler(bot, event, '世界积分商店', bot.self_id, l_msg)
    await boss_integral_info.finish()


@boss_integral_use.handle(parameterless=[Cooldown(at_sender=False)])
async def boss_integral_use_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """世界积分商店兑换"""
    # 这里曾经是风控模块，但是已经不再需要了
    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    msg = args.extract_plain_text().strip()
    shop_info = re.findall(r"(\d+)\s*(\d*)", msg)

    is_in_group = isInGroups(event)
    if not is_in_group:
        msg = f"世界Boss暂未开放，敬请期待!"
        await bot.send(event=event, message=msg)
        await boss_integral_use.finish()

    if shop_info:
        shop_id = int(shop_info[0][0])
        quantity = int(shop_info[0][1]) if shop_info[0][1] else 1
    else:
        msg = f"请输入正确的商品编号！"
        await bot.send(event=event, message=msg)
        await boss_integral_use.finish()

    boss_integral_shop = config['世界积分商品']
    is_in = False
    cost = None
    item_id = None
    if boss_integral_shop:
        for k, v in boss_integral_shop.items():
            if shop_id == int(k):
                is_in = True
                cost = v['cost']
                item_id = v['id']
                break
    else:
        msg = f"世界积分商店内空空如也！"
        await bot.send(event=event, message=msg)
        await boss_integral_use.finish()
    if is_in:
        user_boss_fight_info = get_user_boss_fight_info(user_id)
        total_cost = cost * quantity
        if user_boss_fight_info['boss_integral'] < total_cost:
            msg = f"道友的世界积分不满足兑换条件呢"
            await bot.send(event=event, message=msg)
            await boss_integral_use.finish()
        else:
            user_boss_fight_info['boss_integral'] -= total_cost
            save_user_boss_fight_info(user_id, user_boss_fight_info)
            item_info = items.get_data_by_item_id(item_id)
            await sql_message.send_back(user_id, item_id, item_info['name'], item_info['type'], quantity)  # 兑换指定数量
            msg = f"道友成功兑换获得：{item_info['name']}{quantity}个"
            await bot.send(event=event, message=msg)
            await boss_integral_use.finish()
    else:
        msg = f"该编号不在商品列表内哦，请检查后再兑换"
        await bot.send(event=event, message=msg)
        await boss_integral_use.finish()


def isInGroups(event: GroupMessageEvent):
    return str(event.group_id) in groups


PLAYERSDATA = Path() / "data" / "xiuxian" / "players"


def get_user_boss_fight_info(user_id):
    try:
        user_boss_fight_info = read_user_boss_fight_info(user_id)
    except:
        save_user_boss_fight_info(user_id, user_boss_fight_info)
    return user_boss_fight_info


def read_user_boss_fight_info(user_id):
    user_id = str(user_id)

    FILEPATH = PLAYERSDATA / user_id / "boss_fight_info.json"
    if not os.path.exists(FILEPATH):
        data = {"boss_integral": 0}
        with open(FILEPATH, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=4)
    else:
        with open(FILEPATH, "r", encoding="UTF-8") as f:
            data = json.load(f)

    # 检查 boss_integral 键值是否为负数
    if "boss_integral" in data and data["boss_integral"] < 0:
        data["boss_integral"] = 0
        with open(FILEPATH, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=4)

    return data


def save_user_boss_fight_info(user_id, data):
    user_id = str(user_id)

    if not os.path.exists(PLAYERSDATA / user_id):
        logger.opt(colors=True).info("<green>目录不存在，创建目录</green>")
        os.makedirs(PLAYERSDATA / user_id)

    FILEPATH = PLAYERSDATA / user_id / "boss_fight_info.json"
    data = json.dumps(data, ensure_ascii=False, indent=4)
    save_mode = "w" if os.path.exists(FILEPATH) else "x"
    with open(FILEPATH, mode=save_mode, encoding="UTF-8") as f:
        f.write(data)
        f.close()


def get_dict_type_rate(data_dict):
    """根据字典内概率,返回字典key"""
    temp_dict = {}
    for i, v in data_dict.items():
        try:
            temp_dict[i] = v["type_rate"]
        except:
            continue
    key = OtherSet().calculated(temp_dict)
    return key


def get_goods_type():
    data_dict = BOSSDLW['宝物']
    return get_dict_type_rate(data_dict)


def get_story_type():
    """根据概率返回事件类型"""
    data_dict = BOSSDLW
    return get_dict_type_rate(data_dict)


BOSSDLW = {"衣以候": "衣以侯布下了禁制镜花水月，",
           "金凰儿": "金凰儿使用了神通：金凰天火罩！",
           "九寒": "九寒使用了神通：寒冰八脉！",
           "莫女": "莫女使用了神通：圣灯启语诀！",
           "术方": "术方使用了神通：天罡咒！",
           "卫起": "卫起使用了神通：雷公铸骨！",
           "血枫": "血枫使用了神通：混世魔身！",
           "以向": "以向使用了神通：云床九练！",
           "砂鲛": "不说了！开鳖！",
           "神风王": "不说了！开鳖！",
           "鲲鹏": "鲲鹏使用了神通：逍遥游！",
           "天龙": "天龙使用了神通：真龙九变！",
           "历飞雨": "厉飞雨使用了神通：天煞震狱功！",
           "外道贩卖鬼": "不说了！开鳖！",
           "元磁道人": "元磁道人使用了法宝：元磁神山！",
           "散发着威压的尸体": "尸体周围爆发了出强烈的罡气！"
           }


def boss_drops(user_rank, boss_rank, boss, user_info):
    boss_dice = random.randint(0, 100)
    drops_id = None
    drops_info = None
    if boss_rank - user_rank >= 6:
        drops_id = None
        drops_info = None

    elif boss_dice >= 90:
        drops_id, drops_info = get_drops(user_info)

    return drops_id, drops_info


def get_drops(user_info):
    """
    随机获取一个boss掉落物
    :param user_info:用户信息类
    :return 法器ID, 法器信息json
    """
    drops_data = items.get_data_by_item_type(['掉落物'])
    drops_id = get_id(drops_data, user_info['level'])
    drops_info = items.get_data_by_item_id(drops_id)
    return drops_id, drops_info


def get_id(dict_data, user_level):
    """根据字典的rank、用户等级、秘境等级随机获取key"""
    l_temp = []
    final_rank = convert_rank(user_level)[0]  # 秘境等级，会提高用户的等级
    pass_rank = convert_rank('地仙境后期')[0]  # 最终等级超过此等级会抛弃
    for k, v in dict_data.items():
        if (int(v["rank"]) - 57) <= final_rank and (final_rank - abs(int(v["rank"]) - 57)) <= pass_rank:
            l_temp.append(k)
    if len(l_temp) == 0:
        return None
    else:
        return random.choice(l_temp)
