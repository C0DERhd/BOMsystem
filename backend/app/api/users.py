from flask import request, jsonify
from flask_login import login_required, current_user
from app.api import bp
from app.models.user import User, Role
from app.services.auth_service import AuthService
from app import db
from app.utils.validators import validate_email, validate_password
from app.utils.helpers import paginate_query

@bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """获取用户列表"""
    try:
        # 权限检查
        if not current_user.has_permission('user_read'):
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403
        
        query = User.query
        
        # 搜索条件
        keyword = request.args.get('keyword')
        if keyword:
            search_term = f"%{keyword}%"
            query = query.filter(
                (User.username.like(search_term)) |
                (User.name.like(search_term)) |
                (User.email.like(search_term))
            )
        
        department = request.args.get('department')
        if department:
            query = query.filter(User.department == department)
        
        is_active = request.args.get('is_active')
        if is_active is not None:
            query = query.filter(User.is_active == (is_active.lower() == 'true'))
        
        # 排序
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if hasattr(User, sort_by):
            order_field = getattr(User, sort_by)
            if sort_order == 'desc':
                order_field = order_field.desc()
            query = query.order_by(order_field)
        
        # 分页
        result = paginate_query(query)
        result['items'] = [user.to_dict() for user in result['items']]
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500

@bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """获取用户详情"""
    try:
        # 权限检查
        if not (current_user.has_permission('user_read') or current_user.id == user_id):
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': user.to_dict(include_roles=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户详情失败: {str(e)}'
        }), 500

@bp.route('/users', methods=['POST'])
@login_required
def create_user():
    """创建用户"""
    try:
        # 权限检查
        if not current_user.has_permission('user_create'):
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证必填字段
        required_fields = ['username', 'email', 'name', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空'
                }), 400
        
        # 验证邮箱
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': '邮箱格式不正确'
            }), 400
        
        # 验证密码
        password_validation = validate_password(data['password'])
        if not password_validation['valid']:
            return jsonify({
                'success': False,
                'message': password_validation['message']
            }), 400
        
        user = AuthService.create_user(
            username=data['username'],
            email=data['email'],
            name=data['name'],
            password=data['password'],
            roles=data.get('roles', ['user']),
            phone=data.get('phone'),
            department=data.get('department'),
            position=data.get('position')
        )
        
        return jsonify({
            'success': True,
            'message': '用户创建成功',
            'data': user.to_dict(include_roles=True)
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'用户创建失败: {str(e)}'
        }), 500

@bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """更新用户"""
    try:
        # 权限检查
        if not (current_user.has_permission('user_update') or current_user.id == user_id):
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证邮箱
        if data.get('email') and not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': '邮箱格式不正确'
            }), 400
        
        user = AuthService.update_user(user, **data)
        
        return jsonify({
            'success': True,
            'message': '用户更新成功',
            'data': user.to_dict(include_roles=True)
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'用户更新失败: {str(e)}'
        }), 500

@bp.route('/users/<int:user_id>/roles', methods=['POST'])
@login_required
def assign_user_roles(user_id):
    """分配用户角色"""
    try:
        # 权限检查
        if not current_user.has_permission('user_role_assign'):
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        data = request.get_json()
        if not data or 'role_codes' not in data:
            return jsonify({
                'success': False,
                'message': '角色列表不能为空'
            }), 400
        
        AuthService.assign_roles(user, data['role_codes'])
        
        return jsonify({
            'success': True,
            'message': '角色分配成功',
            'data': user.to_dict(include_roles=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'角色分配失败: {str(e)}'
        }), 500

@bp.route('/roles', methods=['GET'])
@login_required
def get_roles():
    """获取角色列表"""
    try:
        roles = Role.query.filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'data': [role.to_dict() for role in roles]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取角色列表失败: {str(e)}'
        }), 500