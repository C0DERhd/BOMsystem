from flask import request, jsonify
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import bp
from app.services.material_service import MaterialService
from app.services.material_code_service import MaterialCodeService
from app.models.material import Material, MaterialCategory
from app.utils.validators import validate_material_code, validate_decimal
from app.utils.helpers import safe_int

@bp.route('/materials', methods=['GET'])
@login_required
def get_materials():
    """获取物料列表"""
    try:
        filters = {
            'keyword': request.args.get('keyword'),
            'category_id': request.args.get('category_id', type=int),
            'material_type': request.args.get('material_type'),
            'status': request.args.get('status'),
            'created_by': request.args.get('created_by', type=int),
            'sort_by': request.args.get('sort_by', 'created_at'),
            'sort_order': request.args.get('sort_order', 'desc')
        }
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        result = MaterialService.search_materials(filters, page, per_page)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取物料列表失败: {str(e)}'
        }), 500

@bp.route('/materials/<int:material_id>', methods=['GET'])
@login_required
def get_material(material_id):
    """获取物料详情"""
    try:
        material = Material.query.get(material_id)
        if not material:
            return jsonify({
                'success': False,
                'message': '物料不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': material.to_dict(include_suppliers=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取物料详情失败: {str(e)}'
        }), 500

@bp.route('/materials', methods=['POST'])
@login_required
def create_material():
    """创建物料"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证必填字段
        required_fields = ['material_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空'
                }), 400
        
        # 验证物料编码（如果提供）
        if data.get('material_code'):
            validation = validate_material_code(data['material_code'])
            if not validation['valid']:
                return jsonify({
                    'success': False,
                    'message': validation['message']
                }), 400
        
        # 验证成本
        if data.get('standard_cost'):
            validation = validate_decimal(data['standard_cost'], min_value=0)
            if not validation['valid']:
                return jsonify({
                    'success': False,
                    'message': f'标准成本{validation["message"]}'
                }), 400
        
        material = MaterialService.create_material(data, current_user.id)
        
        return jsonify({
            'success': True,
            'message': '物料创建成功',
            'data': material.to_dict(include_suppliers=True)
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'物料创建失败: {str(e)}'
        }), 500

@bp.route('/materials/<int:material_id>', methods=['PUT'])
@login_required
def update_material(material_id):
    """更新物料"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        material = MaterialService.update_material(material_id, data)
        
        return jsonify({
            'success': True,
            'message': '物料更新成功',
            'data': material.to_dict(include_suppliers=True)
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'物料更新失败: {str(e)}'
        }), 500

@bp.route('/materials/<int:material_id>', methods=['DELETE'])
@login_required
def delete_material(material_id):
    """删除物料"""
    try:
        success = MaterialService.delete_material(material_id)
        if success:
            return jsonify({
                'success': True,
                'message': '物料删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '物料不存在'
            }), 404
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'物料删除失败: {str(e)}'
        }), 500

@bp.route('/materials/categories', methods=['GET'])
@login_required
def get_material_categories():
    """获取物料分类"""
    try:
        parent_id = request.args.get('parent_id', type=int)
        categories = MaterialService.get_material_categories(parent_id)
        
        return jsonify({
            'success': True,
            'data': categories
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取物料分类失败: {str(e)}'
        }), 500

@bp.route('/materials/categories', methods=['POST'])
@login_required
def create_material_category():
    """创建物料分类"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证必填字段
        required_fields = ['category_code', 'category_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空'
                }), 400
        
        category = MaterialService.create_material_category(data)
        
        return jsonify({
            'success': True,
            'message': '物料分类创建成功',
            'data': category.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'物料分类创建失败: {str(e)}'
        }), 500

@bp.route('/materials/code/generate', methods=['POST'])
@login_required
def generate_material_code():
    """生成物料编码"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 方式1：根据分类生成
        if data.get('category_id'):
            material_code = MaterialService.generate_material_code_by_category(
                category_id=data['category_id'],
                version=data.get('version', 0)
            )
        # 方式2：根据参数生成
        else:
            material_code = MaterialCodeService.generate_material_code(
                part_type=data.get('part_type', 'custom'),
                material_type=data.get('material_type', 'custom'),
                part_category=data.get('part_category', 'mechanical'),
                classification=data.get('classification', 0),
                version=data.get('version', 0)
            )
        
        return jsonify({
            'success': True,
            'data': {
                'material_code': material_code,
                'description': MaterialCodeService.get_code_description(material_code)
            }
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'物料编码生成失败: {str(e)}'
        }), 500

@bp.route('/materials/code/validate', methods=['POST'])
@login_required
def validate_material_code_api():
    """验证物料编码"""
    try:
        data = request.get_json()
        if not data or not data.get('material_code'):
            return jsonify({
                'success': False,
                'message': '物料编码不能为空'
            }), 400
        
        material_code = data['material_code']
        is_valid, message = MaterialCodeService.validate_material_code(material_code)
        
        result = {
            'material_code': material_code,
            'is_valid': is_valid,
            'message': message
        }
        
        if is_valid:
            # 检查唯一性
            exclude_id = data.get('exclude_id')
            is_unique = MaterialCodeService.check_code_uniqueness(material_code, exclude_id)
            result['is_unique'] = is_unique
            if not is_unique:
                result['message'] = '物料编码已存在'
            
            # 获取编码解析信息
            result['description'] = MaterialCodeService.get_code_description(material_code)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'物料编码验证失败: {str(e)}'
        }), 500

@bp.route('/materials/code/rules', methods=['GET'])
@login_required
def get_material_code_rules():
    """获取物料编码规则"""
    try:
        rules = MaterialCodeService.get_coding_rules()
        
        return jsonify({
            'success': True,
            'data': rules
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取编码规则失败: {str(e)}'
        }), 500

@bp.route('/materials/code/next-version', methods=['POST'])
@login_required
def get_next_version_code():
    """获取下一版本编码"""
    try:
        data = request.get_json()
        if not data or not data.get('base_code'):
            return jsonify({
                'success': False,
                'message': '基础编码不能为空'
            }), 400
        
        next_code = MaterialCodeService.get_next_version_code(data['base_code'])
        
        return jsonify({
            'success': True,
            'data': {
                'next_version_code': next_code,
                'description': MaterialCodeService.get_code_description(next_code)
            }
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取下一版本编码失败: {str(e)}'
        }), 500

# JWT版本的API
@bp.route('/jwt/materials', methods=['GET'])
@jwt_required()
def jwt_get_materials():
    """JWT版本：获取物料列表"""
    return get_materials()

@bp.route('/jwt/materials', methods=['POST'])
@jwt_required()
def jwt_create_material():
    """JWT版本：创建物料"""
    try:
        current_user_identity = get_jwt_identity()
        user_id = current_user_identity['user_id']
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        material = MaterialService.create_material(data, user_id)
        
        return jsonify({
            'success': True,
            'message': '物料创建成功',
            'data': material.to_dict(include_suppliers=True)
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'物料创建失败: {str(e)}'
        }), 500