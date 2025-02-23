from nonebot.adapters.onebot.v11 import GROUP, GroupMessageEvent, Bot
from nonebot.plugin.on import on_message

from ..xiuxian_utils.clean_utils import simple_md

tips_user = []

tips = on_message(priority=1, permission=GROUP, block=False)


@tips.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    user_id = event.user_id
    if user_id not in tips_user:
        tips_user.append(user_id)
        msg = simple_md('很抱歉凌晨的异常停机给各位带来了不好的体验，点击',
                        '领取补偿', '领取补偿501', '。')
        await bot.send(event=event, message=msg)
        await tips.finish()
    await tips.finish()
