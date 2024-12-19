#!usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from pkgutil import iter_modules

from nonebot import get_driver
from nonebot import require, load_all_plugins, get_plugin_by_module_name
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from .xiuxian_config import XiuConfig
from .xiuxian_utils.config import config as _config
from .xiuxian_utils.download_xiuxian_data import download_xiuxian_data

DRIVER = get_driver()

try:
    NICKNAME: str = list(DRIVER.config.nickname)[0]
except Exception as e:
    logger.opt(colors=True).info(f"<red>缺少超级用户配置文件，{e}!</red>")
    logger.opt(colors=True).info(f"<red>请去.env.dev文件中设置超级用户QQ号以及nickname!</red>")
    NICKNAME = 'bot'

require('nonebot_plugin_apscheduler')

if get_plugin_by_module_name("xiuxian"):
    logger.opt(colors=True).info(f"<green>推荐直接加载 xiuxian 仓库文件夹</green>")
    load_all_plugins(
        [
            f"xiuxian.{module.name}"
            for module in iter_modules([str(Path(__file__).parent)])
            if module.ispkg
               and (
                       (name := module.name[11:]) == "meta"
                       or name not in _config.disabled_plugins
               )
            # module.name[:11] == xiuxian_
        ],
        [],
    )

__plugin_meta__ = PluginMetadata(
    name='修仙模拟器',
    description='',
    usage=(
        "必死之境机逢仙缘，修仙之路波澜壮阔！\r"
        " 输入 < 修仙帮助 > 获取仙界信息"
    ),
    extra={
        "show": True,
        "priority": 15
    }
)
