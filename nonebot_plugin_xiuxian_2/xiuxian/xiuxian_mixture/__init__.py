from ..xiuxian_utils.lay_out import Cooldown
from nonebot.params import CommandArg
from nonebot import on_command
from ..xiuxian_utils.xiuxian2_handle import sql_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent
)
from ..xiuxian_utils.utils import check_user


mixture = on_command('合成', priority=15, permission=GROUP, block=True)


@mixture.handle(parameterless=[Cooldown(at_sender=False)])
async def use_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    _, user_info, _ = await check_user(event)

    user_id = user_info['user_id']
    back_msg = await sql_message.get_back_msg(user_id)
    if back_msg is None:
        msg = "道友的背包空空如也！"
        await bot.send(event=event, message=msg)
        await mixture.finish()
