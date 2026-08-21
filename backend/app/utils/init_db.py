# python
# 文件: `backend/app/scripts/init_db.py`
# 用法示例：
#   python backend/app/scripts/init_db.py
# 或在激活虚拟环境后：
#   set FLASK_CONFIG=development && python backend/app/scripts/init_db.py

import os
import sys

# 添加backend目录到Python路径
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, backend_dir)

from app import create_app, db

# 根据项目实际的配置键名调整 'FLASK_CONFIG' 或直接传入配置名
config_name = os.getenv('FLASK_CONFIG', 'development')
app = create_app(config_name)

with app.app_context():
    # 如果你使用 Alembic/Flask-Migrate，优先使用迁移： `flask db upgrade`
    # 这里作为快速创建表的方式（开发环境谨慎使用）
    db.create_all()
    print("所有模型对应的表已在数据库中创建（如果尚不存在）。")
    # 若需要，也可以在这里插入初始数据或检查表名：
    # from app.models.user import User
    # print(User.__tablename__)