from flask import request, jsonify
from flask_login import login_required, current_user
from app.api import bp
from app.models.supplier import Supplier
from app import db
from app.utils.validators import validate_supplier_code, validate_email, validate_decimal
from app.utils.helpers import generate_code, paginate_query

@bp.route('/suppliers', methods=['GET'])
@login_required
def get_suppliers():
    """获取供应商列表"""
    try:
        query = Supplier.query
        
        # 搜索条件
        keyword = request.args.get('keyword')
        if keyword:
            search_term = f"%{keyword}%"
            query = query.filter(
                (Supplier.supplier_name.like(search_term)) |
                (Supplier.supplier_code.like(search_term))
            )
        
        supplier_type = request.args.get('supplier_type')
        if supplier_type:
            query = query.filter(Supplier.supplier_type == supplier_type)
        
        status = request.args.get('status')
        if status:
            query = query.filter(Supplier.status == status)
        
        # 排序
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if hasattr(Supplier, sort_by):
            order_field = getattr(Supplier, sort_by)
            if sort_order == 'desc':
                order_field = order_field.desc()
            query = query.order_by(order_field)
        
        # 分页
        result = paginate_query(query)
        result['items'] = [supplier.to_dict() for supplier in result['items']]
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取供应商列表失败: {str(e)}'
        }), 500

@bp.route('/suppliers/<int:supplier_id>', methods=['GET'])
@login_required
def get_supplier(supplier_id):
    """获取供应商详情"""
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({
                'success': False,
                'message': '供应商不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': supplier.to_dict(include_materials=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取供应商详情失败: {str(e)}'
        }), 500

@bp.route('/suppliers', methods=['POST'])
@login_required
def create_supplier():
    """创建供应商"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证必填字段
        required_fields = ['supplier_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空'
                }), 400
        
        # 生成供应商编码
        if not data.get('supplier_code'):
            data['supplier_code'] = generate_code('SUP', 6)
        
        # 验证供应商编码
        validation = validate_supplier_code(data['supplier_code'])
        if not validation['valid']:
            return jsonify({
                'success': False,
                'message': validation['message']
            }), 400
        
        # 检查编码唯一性
        if Supplier.query.filter_by(supplier_code=data['supplier_code']).first():
            return jsonify({
                'success': False,
                'message': f'供应商编码 {data["supplier_code"]} 已存在'
            }), 400
        
        # 验证邮箱
        if data.get('email') and not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': '邮箱格式不正确'
            }), 400
        
        # 创建供应商
        supplier = Supplier(
            supplier_code=data['supplier_code'],
            supplier_name=data['supplier_name'],
            supplier_name_en=data.get('supplier_name_en'),
            contact_person=data.get('contact_person'),
            phone=data.get('phone'),
            mobile=data.get('mobile'),
            fax=data.get('fax'),
            email=data.get('email'),
            website=data.get('website'),
            country=data.get('country'),
            province=data.get('province'),
            city=data.get('city'),
            address=data.get('address'),
            postal_code=data.get('postal_code'),
            legal_person=data.get('legal_person'),
            registered_capital=data.get('registered_capital'),
            business_license=data.get('business_license'),
            tax_number=data.get('tax_number'),
            supplier_type=data.get('supplier_type', 'material'),
            supplier_level=data.get('supplier_level', 'C'),
            iso_certification=data.get('iso_certification'),
            quality_certification=data.get('quality_certification'),
            payment_terms=data.get('payment_terms'),
            currency=data.get('currency', 'CNY'),
            credit_limit=data.get('credit_limit'),
            lead_time=data.get('lead_time'),
            delivery_terms=data.get('delivery_terms'),
            remark=data.get('remark'),
            created_by=current_user.id
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '供应商创建成功',
            'data': supplier.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'供应商创建失败: {str(e)}'
        }), 500

@bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
@login_required
def update_supplier(supplier_id):
    """更新供应商"""
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({
                'success': False,
                'message': '供应商不存在'
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
        
        # 可更新字段
        updatable_fields = [
            'supplier_name', 'supplier_name_en', 'contact_person',
            'phone', 'mobile', 'fax', 'email', 'website',
            'country', 'province', 'city', 'address', 'postal_code',
            'legal_person', 'registered_capital', 'business_license', 'tax_number',
            'supplier_type', 'supplier_level', 'iso_certification', 'quality_certification',
            'payment_terms', 'currency', 'credit_limit', 'lead_time', 'delivery_terms',
            'quality_rating', 'delivery_rating', 'service_rating',
            'status', 'cooperation_status', 'remark'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(supplier, field, data[field])
        
        # 计算综合评分
        supplier.calculate_overall_rating()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '供应商更新成功',
            'data': supplier.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'供应商更新失败: {str(e)}'
        }), 500

@bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
@login_required
def delete_supplier(supplier_id):
    """删除供应商"""
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({
                'success': False,
                'message': '供应商不存在'
            }), 404
        
        # 检查是否有关联的物料
        if supplier.material_suppliers.filter_by(status='active').first():
            return jsonify({
                'success': False,
                'message': '供应商有关联的物料，无法删除'
            }), 400
        
        db.session.delete(supplier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '供应商删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'供应商删除失败: {str(e)}'
        }), 500

@bp.route('/suppliers/<int:supplier_id>/materials', methods=['GET'])
@login_required
def get_supplier_materials(supplier_id):
    """获取供应商物料列表"""
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({
                'success': False,
                'message': '供应商不存在'
            }), 404
        
        materials = supplier.material_suppliers.filter_by(status='active').all()
        
        return jsonify({
            'success': True,
            'data': [ms.to_dict() for ms in materials]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取供应商物料失败: {str(e)}'
        }), 500