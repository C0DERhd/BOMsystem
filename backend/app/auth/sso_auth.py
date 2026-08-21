import os
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs
from flask import current_app, url_for, session, request
from flask_login import login_user
from app.services.auth_service import AuthService

class SSOAuthHandler:
    """SSO认证处理器"""
    
    def __init__(self):
        self.client_id = os.environ.get('OAUTH_CLIENT_ID')
        self.client_secret = os.environ.get('OAUTH_CLIENT_SECRET')
        self.authorization_url = os.environ.get('OAUTH_AUTHORIZATION_URL')
        self.token_url = os.environ.get('OAUTH_TOKEN_URL')
        self.user_info_url = os.environ.get('OAUTH_USER_INFO_URL')
        self.redirect_uri = None  # 将在运行时设置
        
    def is_enabled(self) -> bool:
        """检查SSO是否已配置并启用"""
        sso_enabled = os.environ.get('SSO_ENABLED', 'false').lower() == 'true'
        has_oauth_config = all([
            self.client_id,
            self.client_secret,
            self.authorization_url,
            self.token_url,
            self.user_info_url
        ])
        return sso_enabled and has_oauth_config
    
    def get_authorization_url(self, state: str = None) -> str:
        """
        获取SSO授权URL
        
        Args:
            state: 状态参数，用于防止CSRF攻击
            
        Returns:
            str: 授权URL
        """
        
        if not self.is_enabled():
            raise ValueError("SSO未配置或未启用")
        
        # 设置重定向URI
        self.redirect_uri = url_for('auth.sso_callback', _external=True)
        
        # 构建授权参数
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'openid profile email',
        }
        
        if state:
            params['state'] = state
            session['oauth_state'] = state
        
        # 生成授权URL
        auth_url = f"{self.authorization_url}?{urlencode(params)}"
        return auth_url
    
    def handle_callback(self, authorization_code: str, state: str = None) -> Dict[str, Any]:
        """
        处理SSO回调
        
        Args:
            authorization_code: 授权码
            state: 状态参数
            
        Returns:
            Dict: 处理结果
        """
        
        if not self.is_enabled():
            return {
                'success': False,
                'message': 'SSO未配置或未启用'
            }
        
        # 验证state参数（防止CSRF攻击）
        if state and session.get('oauth_state') != state:
            return {
                'success': False,
                'message': '无效的state参数'
            }
        
        try:
            # 交换访问令牌
            token_data = self._exchange_code_for_token(authorization_code)
            if not token_data:
                return {
                    'success': False,
                    'message': '获取访问令牌失败'
                }
            
            # 获取用户信息
            user_info = self._get_user_info(token_data['access_token'])
            if not user_info:
                return {
                    'success': False,
                    'message': '获取用户信息失败'
                }
            
            # 创建或更新用户
            user = AuthService.create_sso_user(user_info)
            
            # 登录用户
            login_user(user, remember=True)
            
            # 生成JWT令牌
            tokens = AuthService.generate_tokens(user)
            
            # 清除session中的state
            session.pop('oauth_state', None)
            
            return {
                'success': True,
                'message': 'SSO登录成功',
                'data': {
                    'user': user.to_dict(include_roles=True),
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token'],
                    'permissions': AuthService.get_user_permissions(user)
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"SSO回调处理失败: {str(e)}")
            return {
                'success': False,
                'message': 'SSO认证失败，请稍后重试'
            }
    
    def _exchange_code_for_token(self, authorization_code: str) -> Optional[Dict[str, Any]]:
        """
        用授权码交换访问令牌
        
        Args:
            authorization_code: 授权码
            
        Returns:
            Dict: 令牌数据
        """
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(
                self.token_url,
                data=token_data,
                headers={'Accept': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"获取令牌失败: {response.text}")
                return None
                
        except requests.RequestException as e:
            current_app.logger.error(f"令牌请求异常: {str(e)}")
            return None
    
    def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        使用访问令牌获取用户信息
        
        Args:
            access_token: 访问令牌
            
        Returns:
            Dict: 用户信息
        """
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.get(
                self.user_info_url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"获取用户信息失败: {response.text}")
                return None
                
        except requests.RequestException as e:
            current_app.logger.error(f"用户信息请求异常: {str(e)}")
            return None

class SAMLAuthHandler:
    """SAML认证处理器（可选实现）"""
    
    def __init__(self):
        self.saml_settings = self._load_saml_settings()
    
    def _load_saml_settings(self) -> Dict[str, Any]:
        """加载SAML配置"""
        # 这里可以实现SAML配置加载逻辑
        # 返回SAML设置字典
        return {}
    
    def is_enabled(self) -> bool:
        """检查SAML是否已配置并启用"""
        return bool(self.saml_settings)
    
    def get_sso_url(self) -> str:
        """获取SAML SSO URL"""
        # 实现SAML SSO URL生成逻辑
        pass
    
    def handle_sso_response(self, saml_response: str) -> Dict[str, Any]:
        """处理SAML响应"""
        # 实现SAML响应处理逻辑
        pass

# 全局SSO处理器实例
sso_handler = SSOAuthHandler()
saml_handler = SAMLAuthHandler()