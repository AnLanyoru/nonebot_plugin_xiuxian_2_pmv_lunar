from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GROUP, GroupMessageEvent

from ..xiuxian_utils.lay_out import Cooldown, test_user

test_mode_open = on_command("测试调试模式", priority=14, permission=GROUP, block=True)

test_list = [992551767, 35597641]


@test_mode_open.handle(parameterless=[Cooldown(cd_time=0, pass_test_check=True)])
async def test_mode_open_(bot: Bot, event: GroupMessageEvent):
    """测试模式切换"""
    user_id = str(event.user_id)
    if int(user_id) not in test_list:
        msg = '不在测试名单内'
        await bot.send(event=event, message=msg)
        await test_mode_open.finish()
    if user_id in test_user:
        msg = '已退出测试模式'
        test_user.remove(user_id)
        await bot.send(event=event, message=msg)
        await test_mode_open.finish()

    test_user.append(user_id)
    msg = '已加入测试模式'
    await bot.send(event=event, message=msg)
    await test_mode_open.finish()
