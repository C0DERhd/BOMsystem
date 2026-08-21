from typing import Optional, Dict, Any
from flask import request, jsonify, current_app
from flask_login import login_user, logout_user, current_user
from app.models.user import User
from app.services.auth_service import AuthService

class LocalAuthHandler:
    """本地认证处理器"""
    
    @staticmethod
    def login(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        本地登录处理
        
        Args:
            data: 登录数据，包含username和password
            
        Returns:
            Dict: 登录结果
        """
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not username or not password:
            return {
                'success': False,
                'message': '用户名和密码不能为空'
            }
        
        # 认证用户
        user = AuthService.authenticate_user(username, password)
        if not user:
            return {
                'success': False,
                'message': '账户或密码错误'
            }
        
        # 检查用户状态
        if not user.is_active:
            return {
                'success': False,
                'message': '账户已被禁用，请联系管理员'
            }
        
        # 登录用户（Flask-Login会话）
        login_user(user, remember=remember_me)
        
        # 生成JWT令牌
        tokens = AuthService.generate_tokens(user)
        
        return {
            'success': True,
            'message': '登录成功',
            'data': {
                'user': user.to_dict(include_roles=True),
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'permissions': AuthService.get_user_permissions(user)
            }
        }
    
    @staticmethod
    def register(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        用户注册处理
        
        Args:
            data: 注册数据
            
        Returns:
            Dict: 注册结果
        """
        
        required_fields = ['username', 'email', 'name', 'password']
        for field in required_fields:
            if not data.get(field):
                return {
                    'success': False,
                    'message': f'{field}不能为空'
                }
        
        try:
            # 创建用户
            user = AuthService.create_user(
                username=data['username'],
                email=data['email'],
                name=data['name'],
                password=data['password'],
                phone=data.get('phone'),
                department=data.get('department'),
                position=data.get('position')
            )
            
            return {
                'success': True,
                'message': '注册成功',
                'data': {
                    'user': user.to_dict()
                }
            }
            
        except ValueError as e:
            return {
                'success': False,
                'message': str(e)
            }
        except Exception as e:
            current_app.logger.error(f"用户注册失败: {str(e)}")
            return {
                'success': False,
                'message': '注册失败，请稍后重试'
            }
    
    @staticmethod
    def logout() -> Dict[str, Any]:
        """
        用户登出处理
        
        Returns:
            Dict: 登出结果
        """
        
        try:
            if current_user.is_authenticated:
                logout_user()
            
            return {
                'success': True,
                'message': '登出成功'
            }
            
        except Exception as e:
            current_app.logger.error(f"用户登出失败: {str(e)}")
            return {
                'success': False,
                'message': '登出失败'
            }
    
    @staticmethod
    def change_password(data: Dict[str, Any], user: User) -> Dict[str, Any]:
        """
        修改密码处理
        
        Args:
            data: 包含old_password和new_password的数据
            user: 当前用户
            
        Returns:
            Dict: 修改结果
        """
        
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            return {
                'success': False,
                'message': '旧密码和新密码不能为空'
            }
        
        if len(new_password) < 6:
            return {
                'success': False,
                'message': '新密码长度不能少于6位'
            }
        
        try:
            success = AuthService.change_password(user, old_password, new_password)
            if success:
                return {
                    'success': True,
                    'message': '密码修改成功'
                }
            else:
                return {
                    'success': False,
                    'message': '旧密码不正确'
                }
                
        except ValueError as e:
            return {
                'success': False,
                'message': str(e)
            }
        except Exception as e:
            current_app.logger.error(f"密码修改失败: {str(e)}")
            return {
                'success': False,
                'message': '密码修改失败，请稍后重试'
            }
    
    @staticmethod
    def refresh_token() -> Dict[str, Any]:
        """
        刷新访问令牌
        
        Returns:
            Dict: 刷新结果
        """
        
        try:
            access_token = AuthService.refresh_access_token()
            
            return {
                'success': True,
                'message': '令牌刷新成功',
                'data': {
                    'access_token': access_token
                }
            }
            
        except ValueError as e:
            return {
                'success': False,
                'message': str(e)
            }
        except Exception as e:
            current_app.logger.error(f"令牌刷新失败: {str(e)}")
            return {
                'success': False,
                'message': '令牌刷新失败'
            }
    
    @staticmethod
    def get_current_user() -> Dict[str, Any]:
        """
        获取当前用户信息
        
        Returns:
            Dict: 用户信息
        """
        
        if not current_user.is_authenticated:
            return {
                'success': False,
                'message': '用户未登录'
            }
        
        return {
            'success': True,
            'data': {
                'user': current_user.to_dict(include_roles=True),
                'permissions': AuthService.get_user_permissions(current_user)
            }
        }