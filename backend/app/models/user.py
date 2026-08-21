from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

# 用户角色关联表
user_roles = db.Table('user_roles',
    db.Column('user_id', db.BigInteger, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.BigInteger, db.ForeignKey('roles.id'), primary_key=True)
)

# 角色权限关联表
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.BigInteger, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.BigInteger, db.ForeignKey('permissions.id'), primary_key=True)
)

class Permission(db.Model):
    """权限模型"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False, comment='权限名称')
    code = db.Column(db.String(64), unique=True, nullable=False, comment='权限代码')
    description = db.Column(db.String(255), comment='权限描述')
    resource = db.Column(db.String(64), comment='资源类型')
    action = db.Column(db.String(64), comment='操作类型')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    roles = db.relationship('Role', secondary=role_permissions, back_populates='permissions')
    
    def __repr__(self):
        return f'<Permission {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'resource': self.resource,
            'action': self.action
        }

class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'
    
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, comment='角色名称')
    code = db.Column(db.String(64), unique=True, nullable=False, comment='角色代码')
    description = db.Column(db.String(255), comment='角色描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    users = db.relationship('User', secondary=user_roles, back_populates='roles')
    permissions = db.relationship('Permission', secondary=role_permissions, back_populates='roles')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def has_permission(self, permission_code):
        """检查角色是否有指定权限"""
        return any(p.code == permission_code for p in self.permissions)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'is_active': self.is_active,
            'permissions': [p.to_dict() for p in self.permissions]
        }

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, comment='用户名')
    email = db.Column(db.String(120), unique=True, nullable=False, comment='邮箱')
    name = db.Column(db.String(64), nullable=False, comment='姓名')
    password_hash = db.Column(db.String(255), comment='密码哈希')
    phone = db.Column(db.String(20), comment='电话')
    department = db.Column(db.String(64), comment='部门')
    position = db.Column(db.String(64), comment='职位')
    
    # 账户状态
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    is_verified = db.Column(db.Boolean, default=False, comment='是否验证')
    
    # SSO相关字段
    sso_id = db.Column(db.String(128), unique=True, comment='SSO用户ID')
    auth_type = db.Column(db.Enum('local', 'sso', name='auth_type'), default='local', comment='认证类型')
    
    # 时间戳
    last_login = db.Column(db.DateTime, comment='最后登录时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')
    created_boms = db.relationship('BOM', foreign_keys='BOM.created_by', backref='creator')
    created_materials = db.relationship('Material', foreign_keys='Material.created_by', backref='creator')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission_code):
        """检查用户是否有指定权限"""
        return any(role.has_permission(permission_code) for role in self.roles if role.is_active)
    
    def has_role(self, role_code):
        """检查用户是否有指定角色"""
        return any(role.code == role_code for role in self.roles if role.is_active)
    
    def get_permissions(self):
        """获取用户所有权限"""
        permissions = set()
        for role in self.roles:
            if role.is_active:
                permissions.update(p.code for p in role.permissions)
        return list(permissions)
    
    def to_dict(self, include_roles=False):
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'department': self.department,
            'position': self.position,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'auth_type': self.auth_type,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }
        if include_roles:
            data['roles'] = [role.to_dict() for role in self.roles]
            data['permissions'] = self.get_permissions()
        return data

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login用户加载回调"""
    return User.query.get(int(user_id))