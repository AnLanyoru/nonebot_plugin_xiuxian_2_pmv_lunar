## 数据库转移指南

本层目录下配置pgsql登录配置文件 database.ini:

```
[postgresql]
host=127.0.0.1  # 你的数据库地址
post=1234  # 你的数据库端口
database=your_database_name  # 要登录的数据库名称
user=your_user_name  # 要登录的用户名(需要管理员权限)
password=your_password  # 密码
```

使用迁移工具

```python
from .database_util import data_move
from .database_connect import database


async def move_func():
    sqlite_database_path = Path() / ... / "your_database.db"
    await data_move(database, "target_table", sqlite_database_path)
```