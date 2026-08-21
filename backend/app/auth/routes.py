import secrets
from flask import request, jsonify, redirect, url_for, session
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.auth import bp
from app.auth.local_auth import LocalAuthHandler
from app.auth.sso_auth import sso_handler
from app.models.user import User
from app.utils.validators import validate_email, validate_password

@bp.route('/login', methods=['POST'])
def login():
    """本地登录"""
    try:

        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        result = LocalAuthHandler.login(data)
        print(result)
        status_code = 200 if result['success'] else 401
        return jsonify(result), status_code
        
    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': '登录失败，请稍后重试'
        }), 500

@bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        # 验证邮箱格式
        if not validate_email(data.get('email', '')):
            return jsonify({'success': False, 'message': '邮箱格式不正确'}), 400
        
        # 验证密码强度
        password_validation = validate_password(data.get('password', ''))
        if not password_validation['valid']:
            return jsonify({
                'success': False, 
                'message': password_validation['message']
            }), 400
        
        result = LocalAuthHandler.register(data)
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '注册失败，请稍后重试'
        }), 500

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    try:
        result = LocalAuthHandler.logout()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '登出失败，请稍后重试'
        }), 500

@bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """获取当前用户信息"""
    try:
        result = LocalAuthHandler.get_current_user()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '获取用户信息失败'
        }), 500

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        result = LocalAuthHandler.refresh_token()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '令牌刷新失败'
        }), 500

@bp.route('/password/change', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        # 验证新密码强度
        new_password = data.get('new_password', '')
        password_validation = validate_password(new_password)
        if not password_validation['valid']:
            return jsonify({
                'success': False,
                'message': password_validation['message']
            }), 400
        
        result = LocalAuthHandler.change_password(data, current_user)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '密码修改失败，请稍后重试'
        }), 500

# SSO认证路由
@bp.route('/sso/redirect', methods=['GET'])
def sso_redirect():
    """SSO登录重定向"""
    try:
        if not sso_handler.is_enabled():
            return jsonify({
                'success': False,
                'message': 'SSO未配置或未启用'
            }), 400
        
        # 生成随机state参数
        state = secrets.token_urlsafe(32)
        
        # 获取授权URL
        auth_url = sso_handler.get_authorization_url(state)
        
        return jsonify({
            'success': True,
            'data': {
                'redirect_url': auth_url
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'SSO重定向失败'
        }), 500

@bp.route('/sso/callback', methods=['GET'])
def sso_callback():
    """SSO回调处理"""
    try:
        if not sso_handler.is_enabled():
            return jsonify({
                'success': False,
                'message': 'SSO未配置或未启用'
            }), 400
        
        # 获取授权码和state
        authorization_code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return jsonify({
                'success': False,
                'message': f'SSO认证失败: {error}'
            }), 400
        
        if not authorization_code:
            return jsonify({
                'success': False,
                'message': '缺少授权码'
            }), 400
        
        # 处理SSO回调
        result = sso_handler.handle_callback(authorization_code, state)
        
        if result['success']:
            # 重定向到前端应用
            frontend_url = request.args.get('redirect_to', 'http://localhost:3000')
            return redirect(f"{frontend_url}?sso_success=true")
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'SSO回调处理失败'
        }), 500

@bp.route('/sso/status', methods=['GET'])
def sso_status():
    """获取SSO配置状态"""
    return jsonify({
        'success': True,
        'data': {
            'sso_enabled': sso_handler.is_enabled(),
            'providers': ['oauth2'] if sso_handler.is_enabled() else []
        }
    })

# JWT认证的用户信息端点
@bp.route('/jwt/me', methods=['GET'])
@jwt_required()
def jwt_get_current_user():
    """通过JWT获取当前用户信息"""
    try:
        current_user_identity = get_jwt_identity()
        user_id = int(current_user_identity)
        
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'message': '用户不存在或已被禁用'
            }), 401
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(include_roles=True),
                'permissions': user.get_permissions()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '获取用户信息失败'
        }), 500

# 权限验证辅助路由
@bp.route('/permissions', methods=['GET'])
@login_required
def get_user_permissions():
    """获取当前用户权限列表"""
    try:
        from app.services.auth_service import AuthService
        permissions = AuthService.get_user_permissions(current_user)
        
        return jsonify({
            'success': True,
            'data': {
                'permissions': permissions
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '获取权限信息失败'
        }), 500
