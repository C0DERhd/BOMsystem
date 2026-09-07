from flask import request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
import traceback

from app import db
from app.api import bp
from app.services.bom_service import BOMService
from app.models.bom import BOM
from app.utils.validators import validate_bom_code, validate_decimal
from app.utils.helpers import safe_int

@bp.route('/bom', methods=['GET'])
@login_required
def get_boms():
    """获取BOM列表"""
    try:
        # 获取查询参数
        filters = {
            'keyword': request.args.get('keyword'),
            'status': request.args.get('status'),
            'created_by': request.args.get('created_by', type=int),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'sort_by': request.args.get('sort_by', 'created_at'),
            'sort_order': request.args.get('sort_order', 'desc')
        }
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        result = BOMService.search_boms(filters, page, per_page)

        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取BOM列表失败: {str(e)}'
        }), 500

@bp.route('/bom/<int:bom_id>', methods=['GET'])
@login_required
def get_bom(bom_id):
    """获取BOM详情"""
    try:
        bom = BOM.query.get(bom_id)
        if not bom or bom.is_deleted:
            return jsonify({
                'success': False,
                'message': 'BOM不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': bom.to_dict(include_items=True, include_tree=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取BOM详情失败: {str(e)}'
        }), 500

@bp.route('/bom', methods=['POST'])
@login_required
def create_bom():
    """创建BOM"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证必填字段
        required_fields = ['product_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空'
                }), 400
        
        # 验证BOM编码
        if data.get('bom_code'):
            validation = validate_bom_code(data['bom_code'])
            if not validation['valid']:
                return jsonify({
                    'success': False,
                    'message': validation['message']
                }), 400
        
        # 验证数量
        if data.get('base_quantity'):
            validation = validate_decimal(data['base_quantity'], min_value=0)
            if not validation['valid']:
                return jsonify({
                    'success': False,
                    'message': f'基础数量{validation["message"]}'
                }), 400
        
        bom = BOMService.create_bom(data, current_user.id)
        
        return jsonify({
            'success': True,
            'message': 'BOM创建成功',
            'data': bom.to_dict(include_items=True)
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'BOM创建失败: {str(e)}'
        }), 500

@bp.route('/bom/<int:bom_id>', methods=['PUT'])
@login_required
def update_bom(bom_id):
    """更新BOM"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证数量
        if data.get('base_quantity'):
            validation = validate_decimal(data['base_quantity'], min_value=0)
            if not validation['valid']:
                return jsonify({
                    'success': False,
                    'message': f'基础数量{validation["message"]}'
                }), 400
        
        bom = BOMService.update_bom(bom_id, data)
        
        return jsonify({
            'success': True,
            'message': 'BOM更新成功',
            'data': bom.to_dict(include_items=True)
        })
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'BOM更新失败: {str(e)}'
        }), 500

@bp.route('/bom/<int:bom_id>', methods=['DELETE'])
@login_required
def delete_bom(bom_id):
    """删除BOM"""
    try:
        success = BOMService.delete_bom(bom_id, current_user.id)
        if success:
            return jsonify({
                'success': True,
                'message': 'BOM删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'BOM不存在'
            }), 404
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'BOM删除失败: {str(e)}'
        }), 500

@bp.route('/bom/import-xlsx', methods=['POST'])
@login_required
def import_boms_from_xlsx():
    """从Excel导入BOM"""
    try:
        upload_file = request.files.get('file')
        if not upload_file or not upload_file.filename:
            return jsonify({
                'success': False,
                'message': '请上传Excel文件'
            }), 400
        if not upload_file.filename.lower().endswith(('.xlsx', '.xlsm')):
            return jsonify({
                'success': False,
                'message': '仅支持 .xlsx 或 .xlsm 文件'
            }), 400

        result = BOMService.import_boms_from_excel(upload_file, current_user.id)
        return jsonify({
            'success': True,
            'message': f"BOM导入完成：新增 {result['created_count']} 个，更新 {result['updated_count']} 个，明细 {result['item_count']} 条",
            'data': result
        })

    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'BOM导入失败: {str(e)}'
        }), 500

@bp.route('/bom/<int:bom_id>/export-xlsx', methods=['GET'])
@login_required
def export_bom_to_xlsx(bom_id):
    """导出BOM Excel"""
    try:
        filename, stream = BOMService.export_bom_to_excel(bom_id)
        return send_file(
            stream,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'BOM导出失败: {str(e)}'
        }), 500

@bp.route('/bom/<int:bom_id>/tree', methods=['GET'])
@login_required
def get_bom_tree(bom_id):
    """获取BOM树形结构"""
    try:
        tree_data = BOMService.get_bom_tree(bom_id)
        
        return jsonify({
            'success': True,
            'data': tree_data
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取BOM树形结构失败: {str(e)}'
        }), 500

@bp.route('/bom/<int:bom_id>/cost', methods=['GET'])
@login_required
def get_bom_cost(bom_id):
    """获取BOM成本分析"""
    try:
        cost_data = BOMService.get_bom_cost_analysis(bom_id)
        
        return jsonify({
            'success': True,
            'data': cost_data
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取BOM成本分析失败: {str(e)}'
        }), 500

@bp.route('/bom/<int:bom_id>/shortage', methods=['GET'])
@login_required
def get_bom_shortage(bom_id):
    """按BOM展开并计算缺料清单"""
    try:
        quantity = request.args.get('quantity', type=float)
        shortage_data = BOMService.get_bom_shortage(bom_id, quantity)

        return jsonify({
            'success': True,
            'data': shortage_data
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'缺料清单计算失败: {str(e)}'
        }), 500

@bp.route('/bom/<int:bom_id>/items/<int:item_id>/supplier', methods=['PATCH'])
@login_required
def update_bom_item_supplier(bom_id, item_id):
    """更新BOM明细选中的供应商报价"""
    try:
        data = request.get_json() or {}
        supplier_price_id = data.get('selected_supplier_id')
        if not supplier_price_id:
            return jsonify({
                'success': False,
                'message': '请选择供应商报价'
            }), 400

        item = BOMService.update_item_supplier(bom_id, item_id, safe_int(supplier_price_id))

        return jsonify({
            'success': True,
            'message': '供应商已切换，BOM成本已重新计算',
            'data': {
                'item': item.to_dict(),
            }
        })
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'切换供应商失败: {str(e)}'
        }), 500

@bp.route('/bom/<int:bom_id>/items/<int:item_id>/version', methods=['PATCH'])
@login_required
def update_bom_item_version(bom_id, item_id):
    """更新BOM明细选中的零件版本，并按版本重新匹配报价。"""
    try:
        data = request.get_json() or {}
        item = BOMService.update_item_part_version(
            bom_id,
            item_id,
            safe_int(data.get('part_version_id')),
        )

        return jsonify({
            'success': True,
            'message': '零件版本已切换，报价已重新匹配',
            'data': {
                'item': item.to_dict(),
            }
        })
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'切换零件版本失败: {str(e)}'
        }), 500

@bp.route('/bom/<int:bom_id>/upgrade', methods=['POST'])
@login_required
def upgrade_bom(bom_id):
    """复制当前BOM并生成一个版本号递增的新BOM。"""
    try:
        upgraded_bom = BOMService.upgrade_bom(bom_id, current_user.id)
        return jsonify({
            'success': True,
            'message': 'BOM版本升级成功',
            # 升级已完成，前端只需要新 BOM 的 ID 即可跳转；避免在此重复生成整棵详情树。
            'data': upgraded_bom.to_dict()
        }), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'BOM版本升级失败: {str(e)}'
        }), 500

@bp.route('/bom/<int:bom_id>/version', methods=['POST'])
@login_required
def create_bom_version(bom_id):
    """创建BOM版本"""
    try:
        data = request.get_json()
        version_note = data.get('version_note', '') if data else ''
        
        version = BOMService.create_version(bom_id, version_note, current_user.id)
        
        return jsonify({
            'success': True,
            'message': 'BOM版本创建成功',
            'data': version.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'BOM版本创建失败: {str(e)}'
        }), 500

@bp.route('/bom/<int:bom_id>/versions', methods=['GET'])
@login_required
def get_bom_versions(bom_id):
    """获取BOM版本列表"""
    try:
        bom = BOM.query.get(bom_id)
        if not bom or bom.is_deleted:
            return jsonify({
                'success': False,
                'message': 'BOM不存在'
            }), 404
        
        versions = bom.versions.order_by('created_at desc').all()
        
        return jsonify({
            'success': True,
            'data': [version.to_dict() for version in versions]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取BOM版本列表失败: {str(e)}'
        }), 500

# JWT版本的API（适用于前后端分离）
@bp.route('/jwt/bom', methods=['GET'])
@jwt_required()
def jwt_get_boms():
    """JWT版本：获取BOM列表"""
    return get_boms()

@bp.route('/jwt/bom/<int:bom_id>', methods=['GET'])
@jwt_required()
def jwt_get_bom(bom_id):
    """JWT版本：获取BOM详情"""
    return get_bom(bom_id)

@bp.route('/jwt/bom', methods=['POST'])
@jwt_required()
def jwt_create_bom():
    """JWT版本：创建BOM"""
    try:
        current_user_identity = get_jwt_identity()
        user_id = current_user_identity['user_id']
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证必填字段
        required_fields = ['product_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空'
                }), 400
        
        bom = BOMService.create_bom(data, user_id)
        
        return jsonify({
            'success': True,
            'message': 'BOM创建成功',
            'data': bom.to_dict(include_items=True)
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'BOM创建失败: {str(e)}'
        }), 500
