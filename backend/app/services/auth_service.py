from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from app import db
from app.models.user import User, Role, Permission

class AuthService:
    """认证服务类"""
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """
        本地用户认证
        
        Args:
            username: 用户名或邮箱
            password: 密码
            
        Returns:
            User: 认证成功的用户对象，失败返回None
        """
        
        # 支持用户名或邮箱登录
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password) and user.is_active:
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            db.session.commit()
            return user
        
        return None
    
    @staticmethod
    def create_sso_user(sso_data: Dict[str, Any]) -> User:
        """
        创建或更新SSO用户
        
        Args:
            sso_data: SSO返回的用户信息
            
        Returns:
            User: 用户对象
        """
        
        sso_id = sso_data.get('id') or sso_data.get('sub')
        email = sso_data.get('email')
        username = sso_data.get('username') or sso_data.get('preferred_username') or email
        name = sso_data.get('name') or sso_data.get('displayName')
        
        if not sso_id:
            raise ValueError("SSO用户ID不能为空")
        
        # 查找现有用户
        user = User.query.filter_by(sso_id=sso_id).first()
        
        if user:
            # 更新用户信息
            user.email = email or user.email
            user.name = name or user.name
            user.last_login = datetime.utcnow()
        else:
            # 创建新用户
            user = User(
                username=username,
                email=email,
                name=name,
                sso_id=sso_id,
                auth_type='sso',
                is_active=True,
                is_verified=True,
                last_login=datetime.utcnow()
            )
            
            # 分配默认角色
            default_role = Role.query.filter_by(code='user').first()
            if default_role:
                user.roles.append(default_role)
            
            db.session.add(user)
        
        db.session.commit()
        return user
    
    @staticmethod
    def generate_tokens(user: User) -> Dict[str, str]:
        """
        生成访问令牌和刷新令牌
        
        Args:
            user: 用户对象
            
        Returns:
            Dict: 包含access_token和refresh_token的字典
        """
        
        # 使用用户ID作为身份，附加必要的声明，确保跨版本兼容
        identity = str(user.id)
        claims = {
            'username': user.username,
            'auth_type': user.auth_type
        }
        
        # 生成令牌
        access_token = create_access_token(
            identity=identity,
            additional_claims=claims,
            expires_delta=timedelta(hours=1)
        )
        
        refresh_token = create_refresh_token(
            identity=identity,
            additional_claims=claims,
            expires_delta=timedelta(days=30)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    
    @staticmethod
    def refresh_access_token() -> str:
        """
        刷新访问令牌
        
        Returns:
            str: 新的访问令牌
        """
        
        current_user_identity = get_jwt_identity()
        user_id = int(current_user_identity)
        
        # 验证用户仍然有效
        user = User.query.get(user_id)
        if not user or not user.is_active:
            raise ValueError("用户无效或已被禁用")
        
        # 生成新的访问令牌
        claims = {
            'username': user.username,
            'auth_type': user.auth_type
        }
        return create_access_token(
            identity=str(user_id),
            additional_claims=claims,
            expires_delta=timedelta(hours=1)
        )
    
    @staticmethod
    def get_user_permissions(user: User) -> list:
        """
        获取用户所有权限
        
        Args:
            user: 用户对象
            
        Returns:
            list: 权限代码列表
        """
        
        permissions = set()
        for role in user.roles:
            if role.is_active:
                for permission in role.permissions:
                    permissions.add(permission.code)
        
        return list(permissions)
    
    @staticmethod
    def check_permission(user: User, permission_code: str) -> bool:
        """
        检查用户权限
        
        Args:
            user: 用户对象
            permission_code: 权限代码
            
        Returns:
            bool: 是否有权限
        """
        
        return user.has_permission(permission_code)
    
    @staticmethod
    def create_user(username: str, email: str, name: str, password: str,
                   roles: list = None, **kwargs) -> User:
        """
        创建本地用户
        
        Args:
            username: 用户名
            email: 邮箱
            name: 姓名
            password: 密码
            roles: 角色列表
            **kwargs: 其他用户属性
            
        Returns:
            User: 创建的用户对象
        """
        
        # 检查用户名和邮箱唯一性
        if User.query.filter_by(username=username).first():
            raise ValueError("用户名已存在")
        
        if User.query.filter_by(email=email).first():
            raise ValueError("邮箱已存在")
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            name=name,
            auth_type='local',
            is_active=True,
            **kwargs
        )
        user.set_password(password)
        
        # 分配角色
        if roles:
            for role_code in roles:
                role = Role.query.filter_by(code=role_code).first()
                if role:
                    user.roles.append(role)
        else:
            # 默认用户角色
            default_role = Role.query.filter_by(code='user').first()
            if default_role:
                user.roles.append(default_role)
        
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def update_user(user: User, **kwargs) -> User:
        """
        更新用户信息
        
        Args:
            user: 用户对象
            **kwargs: 要更新的属性
            
        Returns:
            User: 更新后的用户对象
        """
        
        # 可更新的字段
        allowed_fields = [
            'email', 'name', 'phone', 'department', 'position',
            'is_active', 'is_verified'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        # 如果更新密码
        if 'password' in kwargs:
            user.set_password(kwargs['password'])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        return user
    
    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> bool:
        """
        修改用户密码
        
        Args:
            user: 用户对象
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            bool: 是否修改成功
        """
        
        # 本地认证用户才能修改密码
        if user.auth_type != 'local':
            raise ValueError("SSO用户不能修改密码")
        
        # 验证旧密码
        if not user.check_password(old_password):
            return False
        
        # 设置新密码
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    
    @staticmethod
    def reset_password(user: User, new_password: str) -> None:
        """
        重置用户密码（管理员操作）
        
        Args:
            user: 用户对象
            new_password: 新密码
        """
        
        if user.auth_type != 'local':
            raise ValueError("SSO用户不能重置密码")
        
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def assign_roles(user: User, role_codes: list) -> None:
        """
        分配用户角色
        
        Args:
            user: 用户对象
            role_codes: 角色代码列表
        """
        
        # 清除现有角色
        user.roles.clear()
        
        # 分配新角色
        for role_code in role_codes:
            role = Role.query.filter_by(code=role_code, is_active=True).first()
            if role:
                user.roles.append(role)
        
        db.session.commit()
