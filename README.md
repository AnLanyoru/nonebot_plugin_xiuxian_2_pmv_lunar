<div align="center">
  <br>
</div>

<div align="center">

# 🎉 修仙2.2魔改版 lunar

_✨ QQ群聊修仙文字游戏✨_

🧬 主要是青木猫画饼3.0期间少姜做的一些魔改和优化上再魔改但是没优化！🎉

改用了异步数据库asyncpg，大幅提升并发场景下的数据处理能力

<p align="center">
</p>
</div>

# 📖 介绍

一款适用于QQ群的修仙插件,设定征集中，有好的想法可以推送给少姜哦~~~

修仙2原版件地址：https://github.com/QingMuCat/nonebot_plugin_xiuxian_2

修仙2魔改版地址：https://github.com/MyXiaoNan/nonebot_plugin_xiuxian_2_pmv

修仙3.0地址在这，欢迎pr：https://github.com/MyXiaoNan/nonebot-plugin-ascension

# 🎉 和原版有什么区别？

1、将原版的sqlite模块更改为异步模块asyncpg，避免了读写数据时的异步阻塞。

2、修复了少许Bug，又加了更更更多bug：报错与原版相比多很多，有少许功能优化

3、删除了很多指令，例如：合成系统，拍卖系统，世界boss等等

4、不支持图片发送，全文字发送

5、新增少量物品类型

6、使用本fork代码需要完善部分data下json定义

7、部分物品随机名称需要安装node.js

# 💿 建议安装原版

1、手动安装

```
git clone --depth=1 https://github.com/wsdtl/nonebot_plugin_xiuxian_2_pmv

dev分支可选(所有改动都会在dev稳定后合并到master)

git clone -b dev --depth=1 https://github.com/wsdtl/nonebot_plugin_xiuxian_2_pmv
```

2、将git下来的data文件夹移动到bot根目录

3、安装依赖

如果没有虚拟环境：
```
pip install -r requirements.txt
```

如果有选择虚拟环境请进入虚拟环境安装依赖

4、在.env.dev文件中设置超管与机器人昵称

```
LOG_LEVEL=INFO # 日志等级INFO就行

SUPERUSERS = [""] # 超管id 野生bot填自己QQ号(不是机器人的QQ)，官方bot下的用户id自行获取，填的不对的话会出现指令无响应的情况

COMMAND_START = [""] # 指令前缀，默认空
NICKNAME = [""] # 机器人昵称

DEBUG = False
HOST = 127.0.0.1
PORT = 8080 # 反代的8080端口，有需要自己改
```

5、.env文件配置

```
ENVIRONMENT=dev
DRIVER=~fastapi+~websockets+~httpx # 这里用的是反代+http正向调试
```

6、在xiuxian_config.py中配置好各种选项,官方bot仅试过使用 [Gensokyo](https://github.com/Hoshinonyaruko/Gensokyo) 正常运行，野生机器人推荐使用[NapCat](https://github.com/NapNeko/NapCatQQ)，[LLOneBot](https://github.com/LLOneBot/LLOneBot) ,[Lagrange](https://github.com/LagrangeDev/Lagrange.Core) 等

```
一般来说，只需要关注下面几项：
self.merge_forward_send = False # 消息转发类型,True是合并转发，False是长图发送，建议长图  
self.img_compression_limit = 80 # 图片压缩率，0为不压缩，最高100
self.img_type = "webp" # 图片类型，webp或者jpeg，如果机器人的图片消息不显示请使用jpeg
self.img_send_type = "io" # 图片发送类型,默认io,官方bot建议base64
self.put_bot = []  # 接收消息qq,主qq,框架将只处理此qq的消息，不配置将默认设置第一个链接的qq为主qq
self.main_bo = []  # 负责发送消息的qq,调用lay_out.py 下range_bot函数的情况下需要填写
self.shield_group = []  # 屏蔽的群聊
self.layout_bot_dict = {{}}  # QQ所负责的群聊{{群 :bot}}   其中 bot类型 []或str
示例：
{
    "群123群号" : "对应发送消息的qq号"
    "群456群号" ： ["对应发送消息的qq号1","对应发送消息的qq号2"]
}
当后面qq号为一个字符串时为一对一，为列表时为多对一
```

7、如解决不了进交流群：[760517008](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=zIKrPPqNStgZnRtuLhiOv9woBQSMQurq&authKey=Nrqm0zDxYKP2Fon2MskbNRmZ588Rqm79lJvQyVYWtkh9vDFK1RGBK0UhqzehVyDw&noverify=0&group_code=760517008) 提问，提问请贴上完整的日志

# 💿 使用

群聊发送 `启用修仙功能` 后根据引导来即可，不支持私聊
如果你使用的是官方机器人记得改配置

# 🎉 特别感谢

- [NoneBot2](https://github.com/nonebot/nonebot2)：本插件实装的开发框架，NB天下第一可爱。
- [nonebot_plugin_xiuxian](https://github.com/s52047qwas/nonebot_plugin_xiuxian)：原版修仙
- [nonebot_plugin_xiuxian_2](https://github.com/QingMuCat/nonebot_plugin_xiuxian_2)：原版修仙2
- [nonebot_plugin_xiuxian_2_pmv](https://github.com/MyXiaoNan/nonebot_plugin_xiuxian_2_pmv)：原版修仙2魔改版
- [random_chinese_fantasy_names](https://github.com/hythl0day/random_chinese_fantasy_names)：仙侠小说专有名词随机生成器 本插件使用的随机名词生成器

# 🎉 支持

- 大家喜欢的话可以给少姜的项目点个star
- 有bug、意见和建议都欢迎提交给少姜 [Issues](https://github.com/wsdtl/nonebot_plugin_xiuxian_2_pmv/issues)
- 3.0版本正在路上，敬请期待(日常拷打青木猫)

# 🎉 许可证

本项目使用 [MIT](https://choosealicense.com/licenses/mit/) 作为开源许可证，并且没有cc限制
