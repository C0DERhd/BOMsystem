#!/usr/bin/env python
import os
import sys

from app import create_app, db
from app.models.user import User, Role


def assign(username: str, role_code: str) -> int:
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"用户不存在: {username}")
            return 1
        role = Role.query.filter_by(code=role_code).first()
        if not role:
            print(f"角色不存在: {role_code}")
            return 2
        if role not in user.roles:
            user.roles.append(role)
            db.session.commit()
            print(f"已将用户 {username} 加入角色 {role_code}")
        else:
            print(f"用户 {username} 已经在角色 {role_code} 中")
        # 打印用户权限摘要
        print(f"当前用户角色: {[r.code for r in user.roles]}")
        print(f"当前用户权限数量: {len(user.get_permissions())}")
        return 0


if __name__ == '__main__':
    role_code = sys.argv[1] if len(sys.argv) > 1 else 'admin'
    username = sys.argv[2] if len(sys.argv) > 2 else 'xurenjie'
    sys.exit(assign(username, role_code))

