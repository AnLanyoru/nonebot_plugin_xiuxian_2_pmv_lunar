from time import time

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent
)
from nonebot.permission import SUPERUSER

from ..xiuxian_config import XiuConfig
from ..xiuxian_database.database_connect import database
from ..xiuxian_sect import sect_config
from ..xiuxian_store import STORE_BUTTON
from ..xiuxian_utils.clean_utils import help_md, simple_md, main_md, many_md
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.lay_out import Cooldown

config = sect_config
LEVLECOST = config["LEVLECOST"]
userstask = {}

help_in = on_command("修仙帮助", aliases={"/菜单", "/修仙帮助"}, priority=12, permission=GROUP, block=True)
help_newer = on_command("新手", aliases={"怎么玩", "教", "玩法", "不明白", "教程", "修仙新手", "刚玩",
                                         "怎么弄", "干什么", "玩什么", "新手", "有什么", "玩不来", "/新手教程",
                                         "不会", "不懂", "帮助"}, priority=12, permission=GROUP, block=True)
sect_help = on_command("宗门帮助", aliases={"宗门", "工会"}, priority=21, permission=GROUP, block=True)
sect_help_control = on_command("管理宗门", aliases={"宗门管理"}, priority=6, permission=GROUP, block=True)
sect_help_owner = on_command("宗主必看", aliases={"宗主"}, priority=20, permission=GROUP, block=True)
sect_help_member = on_command("成员必看", aliases={"宗门指令"}, priority=20, permission=GROUP, block=True)
buff_help = on_command("功法帮助", aliases={"功法", "技能", "神通"}, priority=2, permission=GROUP, block=True)
buff_home = on_command("洞天福地帮助", aliases={"灵田帮助", "灵田", "洞天福地"}, priority=20, permission=GROUP,
                       block=True)
store_help = on_command("灵宝楼帮助", aliases={"灵宝楼", "个人摊位", "个人摊位帮助"}, priority=20, permission=GROUP,
                        block=True)
tower_help = on_command("位面挑战帮助", aliases={'挑战'}, priority=21, permission=GROUP, block=True)
items_reload = on_command("重载物品", priority=21, permission=SUPERUSER, block=True)
db_ping = on_command("ping", priority=21, permission=SUPERUSER, block=True)
get_test_data = on_command("ts", priority=21, permission=SUPERUSER, block=True)


@get_test_data.handle()
async def get_test_data_(bot: Bot, event: GroupMessageEvent):
    real_user_id = event.real_user_id
    msg = many_md(f'qqbot-at-user id="{real_user_id}" />\r***\r>'
                  f'测试数据\r'
                  f'<qqbot-cmd-input text="ts测试" show="测试按钮" /',
                  'ts测试" show="测试按钮" />\r<qqbot-cmd-input text="ts测试" show="测试按钮',
                  'ts测试" show="测试按钮" />\r<qqbot-cmd-input text="ts测试" show="测试按钮',
                  'ts测试" show="测试按钮" />\r<qqbot-cmd-input text="ts测试" show="测试按钮',
                  'ts测试" show="测试按钮" />\r<qqbot-cmd-input text="ts测试" show="测试按钮',
                  'ts测试" show="测试按钮" />\r<qqbot-cmd-input text="ts测试" show="测试按钮',
                  'ts测试" show="测试按钮" />\r<qqbot-cmd-input text="ts测试" show="测试按钮',
                  'ts测试" show="测试按钮" />\r<qqbot-cmd-input text="ts测试" show="测试按钮',
                  'ts测试" show="测试按钮" />\r<qqbot-cmd-input text="ts测试" show="测试按钮',
                  'ts测试" show="测试按钮" />\r<qqbot-cmd-input text="ts测试" show="测试按钮', )
    await bot.send(event=event, message=msg)
    await get_test_data.finish()


@items_reload.handle()
async def items_reload_(bot: Bot, event: GroupMessageEvent):
    """运行时数据热重载"""
    msg = "开始重载物品数据"
    await bot.send(event=event, message=msg)
    items.load_items()
    msg = "成功重新载入物品数据"
    await bot.send(event=event, message=msg)
    await items_reload.finish()


@db_ping.handle()
async def db_ping_(bot: Bot, event: GroupMessageEvent):
    """运行时数据热重载"""
    start_time = time()
    await database.get_version()
    end_time = time()
    ping_ms = end_time - start_time
    ping_ms = float(ping_ms)
    msg = f"数据库延迟 {ping_ms * 1000} ms"
    await bot.send(event=event, message=msg)
    await db_ping.finish()


__xiuxian_notes__ = f"""
————修仙帮助————
新手教程：
 - 获取修仙新手教程
重入仙途:
 - 更换灵根,每次{XiuConfig().remake}灵石
改头换面:
 - 修改你的道号
突破:
 - 修为足够后,可突破境界
灵石修炼：
 - 使用灵石进行快速修炼，不要贪多哦
排行榜:
 - 查看诸天万界修仙排行榜
日志记录
 - 获取最近10次重要日常操作的记录
我的状态:
 -查看当前状态
————更多玩法帮助
灵宝楼帮助|
灵庄帮助|宗门帮助|背包帮助|
灵田帮助|功法帮助|传承帮助|
——tips——
官方群914556251
""".strip()

__sect_help__ = (f"\r"
                  f"————宗门帮助————\r"
                  f"1：我的宗门\r"
                  f" 🔹 查看当前所处宗门信息\r"
                  f"2：宗门列表\r"
                  f" 🔹 查看所有宗门列表\r"
                  f"3：创建宗门\r"
                  f" 🔹 创建宗门，需求：{XiuConfig().sect_create_cost}灵石，需求境界{XiuConfig().sect_min_level}\r"
                  f"4：加入宗门\r"
                  f" 🔹 加入一个宗门,需要带上宗门id\r"
                  f"5：管理宗门\r"
                  f" 🔹 获取所有宗门管理指令\r"
                  f"6：宗门指令\r"
                  f" 🔹 查看所有宗门普通成员指令\r"
                  f"7：宗主指令\r"
                  f" 🔹 查看所有宗主指令\r").strip()

__buff_help__ = (f"\r"
                  f"——功法帮助——\r"
                  f"1：我的功法:\r"
                  f" 🔹 查看自身功法详情\r"
                  f"2：切磋:\r"
                  f" 🔹 切磋加玩家名称,不会消耗气血\r"
                  f"3：抑制黑暗动乱:\r"
                  f" 🔹 清除修为浮点数\r"
                  f"4：我的双修次数:\r"
                  f" 🔹 查看剩余双修次数\r").strip()

__home_help__ = (f"\r"
                  f"——洞天福地帮助——\r"
                  f"1：洞天福地购买\r"
                  f" 🔹 购买洞天福地\r"
                  f"2：洞天福地查看\r"
                  f" 🔹 查看自己的洞天福地\r"
                  f"3：洞天福地改名\r"
                  f" 🔹 随机修改自己洞天福地的名字\r"
                  f"4：灵田开垦\r"
                  f" 🔹 提升灵田的等级,提高灵田药材数量\r"
                  f"5：灵田收取\r"
                  f" 🔹 收取灵田内生长的药材\r").strip()

__store_help__ = (f"\r"
                  f"——灵宝楼指令大全——\r"
                  f"1：灵宝楼求购 物品 价格 数量\r"
                  f" 🔹 向灵宝楼提交求购物品申请\r"
                  f"2：灵宝楼出售 物品 道号\r"
                  f" 🔹 向有求购的玩家出售对应物品\r"
                  f" 🔹 不输 道号 会按市场最高价出售\r"
                  f"3：灵宝楼求购查看 物品\r"
                  f" 🔹 查看对应物品的最高求购价\r"
                  f"4：我的灵宝楼求购\r"
                  f" 🔹 查看自身灵宝楼求购\r"
                  f"5：灵宝楼取灵石 数量\r"
                  f" 🔹 从灵宝楼中取出灵石，收取20%手续费\r"
                  f"6：取消求购 物品名称\r"
                  f" 🔹 下架你的求购物品\r"
                  f"——tips——\r"
                  f"官方群914556251\r").strip()

__tower_help__ = (f"\r"
                  f"——位面挑战指令帮助——\r"
                  f"1：进入挑战之地\r"
                  f" 🔹 凡界：灵虚古境(前往3)\r"
                  f" 🔹 灵界：紫霄神渊(前往19)\r"
                  f" 🔹 仙界：域外试炼(前往33)\r"
                  f"2：查看挑战\r"
                  f" 🔹 查看当前挑战信息\r"
                  f"3：开始挑战\r"
                  f" 🔹 进行本层次挑战\r"
                  f"4：离开挑战之地\r"
                  f" 🔹 停止对挑战之地的探索\r"
                  f"5：挑战商店\r"
                  f" 🔹 消耗挑战积分兑换物品\r"
                  f"6：挑战之地规则详情\r"
                  f" 🔹 获取位面挑战的详情规则\r"
                      ).strip()


@help_in.handle(parameterless=[Cooldown()])
async def help_in_(bot: Bot, event: GroupMessageEvent):
    """修仙帮助"""
    msg = help_md("102368631_1740931741", "\r小月官服唯一群914556251", "102368631_1740931181")
    await bot.send(event=event, message=msg)
    await help_in.finish()


@help_newer.handle(parameterless=[Cooldown()])
async def help_in_(bot: Bot, event: GroupMessageEvent):
    """修仙新手帮助"""
    msg = help_md("102368631_1743534743", "小月官服唯一群914556251", "102368631_1740930682")
    await bot.send(event=event, message=msg)
    await help_newer.finish()


@sect_help.handle(parameterless=[Cooldown()])
async def sect_help_(bot: Bot, event: GroupMessageEvent):
    """宗门帮助"""
    msg = main_md(__sect_help__,
                  f"小月唯一官方群914556251"
                  f"",
                  "创建宗门", "创建宗门",
                  "加入宗门", "加入宗门",
                  "宗门排行", "宗门排行榜",
                  "我的宗门", "我的宗门",
                  "102368631_1742751063")
    await bot.send(event=event, message=msg)
    await sect_help.finish()


@sect_help_control.handle(parameterless=[Cooldown()])
async def sect_help_control_(bot: Bot, event: GroupMessageEvent):
    """宗门管理帮助"""
    msg = main_md("""宗门管理帮助""",
                  f"1：宗门职位变更\r  🔹 长老以上职位可以改变宗门成员的职位等级\r  🔹 (外门弟子无法获得宗门修炼资源)\r "
                  f"2：踢出宗门\r  🔹 踢出对应宗门成员,需要输入正确的道号\r",
                  "职位变更", "宗门职位变更",
                  "踢出宗门", "踢出宗门",
                  "虚神闭关", "虚神界闭关",
                  "检查周贡", "宗门周贡检查" )
    await bot.send(event=event, message=msg)
    await sect_help_control.finish()


@sect_help_owner.handle(parameterless=[Cooldown()])
async def sect_help_owner_(bot: Bot, event: GroupMessageEvent):
    """宗主帮助"""
    msg = main_md("""宗主菜单""",
                  f"1：宗门职位变更\r  🔹 长老以上职位可以改变宗门成员的职位等级\r  🔹 【0 1 2 3 4】分别对应【宗主 长老 亲传 内门 外门】\r2：踢出宗门\r  🔹 踢出对应宗门成员,需要输入正确的道号\r3：建设宗门丹房\r  🔹 建设宗门丹房每日领取丹药\r"
                  f"4：宗门搜寻功法|神通\r  🔹 宗主消耗宗门资材和宗门灵石搜寻100次功法或者神通\r5：宗门成员查看\r  🔹 查看所在宗门的成员信息\r6：宗主传位\r  🔹 宗主可以传位宗门成员\r7：宗门改名\r  🔹 宗主可以消耗宗门资源改变宗门名称\r8：宗门周贡检查\r  🔹 检查宗门成员周贡",
                  "职位变更", "宗门职位变更",
                  "踢出宗门", "踢出宗门",
                  "宗门成员", "宗门成员查看",
                  "检查周贡", "宗门周贡检查" )
    await bot.send(event=event, message=msg)
    await sect_help_owner.finish()


@sect_help_member.handle(parameterless=[Cooldown()])
async def sect_help_member_(bot: Bot, event: GroupMessageEvent):
    """宗门管理帮助"""
    msg = main_md("""宗门管理帮助""",
                  f"1：我的宗门\r  🔹 查看当前所处宗门信息\r2：升级攻击修炼\r  🔹 每级提升4%攻击力,后可以接升级等级\r3：宗门捐献\r  🔹 建设宗门，提高宗门建设度\r4：学习宗门功法|神通\r  🔹 亲传弟子消耗宗门资材来学习宗门功法或者神通\r"
                  f"5：宗门功法查看\r  🔹 查看当前宗门已有的功法\r6：宗门成员查看\r  🔹 查看所在宗门的成员信息\r7：宗门丹药领取\r  🔹 领取宗门丹药，需内门弟子且1000万宗门贡献\r8：退出宗门\r  🔹 退出当前宗门\r9：宗门BOSS\r  🔹 集体挑战宗门BOSS\r",
                  "退出宗门", "退出宗门",
                  "宗门排行", "宗门排行榜",
                  "宗门丹药", "宗门丹药领取",
                  "宗门任务接取", "宗门任务接取" )
    await bot.send(event=event, message=msg)
    await sect_help_member.finish()


@buff_help.handle(parameterless=[Cooldown()])
async def buff_help_(bot: Bot, event: GroupMessageEvent):
    """功法帮助"""
    msg =  main_md(__buff_help__,
                  f"小月唯一官方群914556251"
                  f"",
                  "我的功法", "我的功法",
                  "双修次数", "我的双修次数",
                  "黑暗动乱", "抑制黑暗动乱",
                  "切磋", "切磋" )
    await bot.send(event=event, message=msg)
    await buff_help.finish()


@buff_home.handle(parameterless=[Cooldown()])
async def buff_home_(bot: Bot, event: GroupMessageEvent):
    """灵田帮助"""
    msg = main_md(__home_help__,
                  f"小月唯一官方群914556251"
                  f"",
                  "灵田收取", "灵田收取",
                  "灵田开垦", "灵田开垦",
                  "洞天福地查看", "洞天福地查看",
                  "洞天福地购买", "洞天福地购买" )
    await bot.send(event=event, message=msg)
    await buff_home.finish()


@store_help.handle(parameterless=[Cooldown()])
async def store_help_(bot: Bot, event: GroupMessageEvent):
    """帮助"""
    msg = simple_md(__store_help__,
                  "查看日常", "日常", "！",
                  STORE_BUTTON)
    await bot.send(event=event, message=msg)
    await store_help.finish()


@tower_help.handle(parameterless=[Cooldown()])
async def tower_help_(bot: Bot, event: GroupMessageEvent):
    """帮助"""
    msg = main_md(__tower_help__,
                  f"小月唯一官方群914556251"
                  f"",
                  "修仙帮助", "修仙帮助",
                  "挑战商店", "挑战商店",
                  "挑战排行", "挑战排行榜",
                  "进入挑战之地", "进入挑战之地" )
    await bot.send(event=event, message=msg)
    await tower_help.finish()
