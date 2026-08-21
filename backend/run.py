#!/usr/bin/env python
import os
import subprocess
from flask.cli import FlaskGroup
from app import create_app, db
from app.models import User, Material, BOM, Supplier

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
cli = FlaskGroup(create_app=lambda: app)

@app.shell_context_processor
def make_shell_context():
    """注册shell上下文"""
    return {
        'db': db,
        'User': User,
        'Material': Material,
        'BOM': BOM,
        'Supplier': Supplier
    }

@app.cli.command()
def init_db():
    """初始化数据库"""
    db.create_all()
    print('数据库初始化完成')

@app.cli.command()
def create_admin():
    """创建管理员用户"""
    from app.models.user import User, Role
    
    try:
        # 创建管理员角色
        admin_role = Role.query.filter_by(code='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                code='admin',
                description='系统管理员'
            )
            db.session.add(admin_role)
            db.session.flush()  # 确保角色ID可用
        
        # 创建管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                name='系统管理员',
                is_active=True,
                auth_type='local'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.flush()  # 确保用户ID可用
            
            # 关联角色
            if admin_role not in admin.roles:
                admin.roles.append(admin_role)
        
        db.session.commit()
        print('管理员用户创建成功 - 用户名: admin, 密码: admin123')
    except Exception as e:
        db.session.rollback()
        print(f'创建管理员用户失败: {str(e)}')

if __name__ == '__main__':
    frontend_proc = None
    try:
        frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
        if os.path.isdir(frontend_dir):
            try:
                if os.name == 'nt':
                    frontend_proc = subprocess.Popen(['cmd', '/c', 'npm', 'start'], cwd=frontend_dir)
                else:
                    frontend_proc = subprocess.Popen(['npm', 'start'], cwd=frontend_dir)
            except Exception:
                frontend_proc = None
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    finally:
        if frontend_proc and frontend_proc.poll() is None:
            try:
                frontend_proc.terminate()
            except Exception:
                pass
