import json
from pathlib import Path

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GROUP, GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from ..xiuxian_utils.clean_utils import get_args_num
from ..xiuxian_utils.lay_out import Cooldown, test_user

test_mode_open = on_command("开启测试模式", priority=5, permission=GROUP, block=True)
test_mode_close = on_command("关闭测试模式", priority=5, permission=GROUP, block=True)
test_user_add = on_command("测试名单加白", priority=5, permission=SUPERUSER, block=True)
test_user_del = on_command("测试名单拉黑", priority=5, permission=SUPERUSER, block=True)

test_list_file_path = Path(__file__).parent / 'test_user.json'

with open(test_list_file_path, "r", encoding="UTF-8") as f:
    data = f.read()
test_list: list[int] = json.loads(data)


@test_user_del.handle()
async def test_user_del_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """测试模式切换"""
    global test_list
    user_id = get_args_num(args)
    if not user_id:
        msg = '请输入要拉黑的测试用户id'
        await bot.send(event=event, message=msg)
        await test_user_del.finish()

    if user_id not in test_list:
        msg = '该id未在测试名单中'
        await bot.send(event=event, message=msg)
        await test_user_del.finish()

    test_list.remove(user_id)
    msg = f'已将id{user_id}拉入测试人员黑名单'

    with open(test_list_file_path, mode='w') as file:
        # noinspection PyTypeChecker
        json.dump(test_list, file)
    await bot.send(event=event, message=msg)
    await test_user_del.finish()


@test_user_add.handle()
async def test_user_add_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """测试模式切换"""
    global test_list
    user_id = get_args_num(args)
    if not user_id:
        msg = '请输入要加白的测试用户'
        await bot.send(event=event, message=msg)
        await test_mode_open.finish()

    if user_id in test_list:
        msg = '该id已在测试名单中'
        await bot.send(event=event, message=msg)
        await test_mode_open.finish()

    test_list.append(user_id)
    msg = f'已将id{user_id}加入测试人员名单'

    with open(test_list_file_path, mode='w') as file:
        # noinspection PyTypeChecker
        json.dump(test_list, file)
    await bot.send(event=event, message=msg)
    await test_mode_open.finish()


@test_mode_open.handle(parameterless=[Cooldown(cd_time=0, pass_test_check=True)])
async def test_mode_open_(bot: Bot, event: GroupMessageEvent):
    """测试模式切换"""
    user_id = str(event.user_id)
    if int(user_id) not in test_list:
        msg = '不在测试名单内'
        await bot.send(event=event, message=msg)
        await test_mode_open.finish()
    if user_id in test_user:
        msg = '已在测试模式中'
        await bot.send(event=event, message=msg)
        await test_mode_open.finish()

    test_user.append(user_id)
    msg = '已加入测试模式'
    await bot.send(event=event, message=msg)
    await test_mode_open.finish()


@test_mode_close.handle(parameterless=[Cooldown(cd_time=0, pass_test_check=True)])
async def test_mode_close_(bot: Bot, event: GroupMessageEvent):
    """测试模式切换"""
    user_id = str(event.user_id)
    if int(user_id) not in test_list:
        msg = '不在测试名单内'
        await bot.send(event=event, message=msg)
        await test_mode_close.finish()
    if user_id in test_user:
        msg = '已退出测试模式'
        test_user.remove(user_id)
        await bot.send(event=event, message=msg)
        await test_mode_close.finish()

    msg = '未处于测试模式'
    await bot.send(event=event, message=msg)
    await test_mode_close.finish()
