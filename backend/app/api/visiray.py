from flask import request, jsonify, current_app, Response, session
from types import SimpleNamespace
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import bp
from app.models.visiray import (
    VisirayInventory, 
    VisirayStockInRecord, 
    VisirayStockOutRecord, 
    VisirayPurchaseReceivingVoucher,
    VisirayPurchaseAttachment,
    VisiraySupplierInformation,
    VisirayPartNumber,
    VisirayPartNumberVersion,
    VisirayVersionInventory,
    VisirayPartNumberRule,
    VisirayContractNumberRecord,
    VisirayUserAccount
)
from app.models.user import User
from app.models.material import Material
from app.models.material import MaterialSupplier
from app.models.supplier import Supplier
from app import db
from app.services.bom_service import BOMService
from app.services.material_code_service import MaterialCodeService
from app.services.part_number_rule_service import PartNumberRuleService
from app.utils.helpers import generate_code, paginate_query
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_file
from sqlalchemy import String, cast, or_, func
import uuid
from datetime import datetime
import re
import os
from werkzeug.utils import secure_filename
import json
from urllib.parse import urlparse

# xyh: 零件号开头标识。以前使用 VSR4，后来改为 VISB，现在仍旧使用 VSR4
PN_HEAD = 'VSR4'

LEGACY_PART_PREFIXES = ('VSR4', 'VISB')

def _strip_part_prefix(value) -> str:
    text = str(value or '').strip()
    upper = text.upper()
    for prefix in LEGACY_PART_PREFIXES:
        if upper.startswith(prefix):
            return text[len(prefix):]
    return text

def _clean_part_number_input(value) -> str:
    text = str(value or '').strip()
    if ' - ' in text:
        text = text.split(' - ', 1)[0].strip()
    return text

def _part_number_candidates(value) -> list[str]:
    raw = _clean_part_number_input(value)
    stripped = _strip_part_prefix(raw)
    candidates: list[str] = []
    for item in (raw, stripped):
        if item and item not in candidates:
            candidates.append(item)

    digits = re.sub(r'\D', '', stripped)
    if digits:
        if digits not in candidates:
            candidates.append(digits)
        try:
            code_length = int(PartNumberRuleService.get_active_rule().get_config().get('code_length') or 0)
        except Exception:
            code_length = 0
        if code_length > 0 and len(digits) < code_length:
            padded = digits.zfill(code_length)
            if padded not in candidates:
                candidates.append(padded)

    return candidates


def _find_part_number(value):
    for candidate in _part_number_candidates(value):
        part = VisirayPartNumber.query.get(candidate)
        if part is not None:
            return part
    digits = re.sub(r'\D', '', _clean_part_number_input(value))
    if digits:
        try:
            inventory_key = _inventory_key(value)
        except Exception:
            inventory_key = None
        possible_parts = VisirayPartNumber.query.filter(
            VisirayPartNumber.part_id.like(f"%{digits}")
        ).limit(50).all()
        for part in possible_parts:
            if inventory_key is not None and _inventory_key(part.part_id) == inventory_key:
                return part
    return None

def _get_part_version(part_version_id, part_id=None):
    if part_version_id in (None, ''):
        return None
    try:
        version = VisirayPartNumberVersion.query.get(int(part_version_id))
    except (TypeError, ValueError):
        version = None
    if not version:
        raise ValueError('零件版本不存在')
    if part_id:
        part = _find_part_number(part_id)
        if not part or version.part_id != part.part_id:
            raise ValueError('零件版本不属于当前零件号')
    return version

def _validate_version_no(value):
    version_no = str(value or '').strip()
    if not re.fullmatch(r'\d{4}', version_no):
        raise ValueError('版本号必须是四位数字字符串，例如 0001')
    return version_no

def _version_to_dict(version):
    data = version.to_dict()
    part = VisirayPartNumber.query.get(version.part_id)
    data.update({
        'part_name': part.part_name if part else None,
        'unit': part.unit if part else None,
        'part_category': part.category if part else None,
    })
    return data

def _get_version_info(part_version_id):
    if part_version_id in (None, ''):
        return None
    try:
        return VisirayPartNumberVersion.query.get(int(part_version_id))
    except Exception:
        return None

def _resolve_part_version_id(value, part_id=None, require_active=False, allow_obsolete=False):
    if value in (None, ''):
        return None
    version = _get_part_version(value, part_id)
    if require_active and (version.status or 'active') != 'active':
        raise ValueError('该零件版本已废弃，不能用于此操作')
    if not allow_obsolete and (version.status or 'active') == 'obsolete':
        raise ValueError('该零件版本已废弃')
    return version.id

def _attach_version_data(item_dict, part_version_id=None):
    version_id = part_version_id if part_version_id is not None else item_dict.get('part_version_id')
    item_dict['part_version_id'] = version_id
    if version_id:
        version = VisirayPartNumberVersion.query.get(version_id)
        if version:
            item_dict['version_no'] = version.version_no
            item_dict['version_status'] = version.status or 'active'
            item_dict['version_is_current'] = bool(version.is_current)
            item_dict['part_id'] = version.part_id
            item_dict['display_goods_id'] = version.part_id
    else:
        item_dict.setdefault('version_no', None)
        item_dict.setdefault('version_status', None)
        item_dict.setdefault('version_is_current', False)
    return item_dict

def _versioned_inventory_display(item_dict: dict) -> dict:
    version = _get_version_info(item_dict.get('part_version_id'))
    if version:
        item_dict['version_no'] = version.version_no
        item_dict['version_status'] = version.status
        item_dict['version_is_current'] = bool(version.is_current)
        item_dict['part_id'] = version.part_id
        item_dict['display_goods_id'] = version.part_id
    item_dict['inventory_type'] = item_dict.get('inventory_type') or 'versioned'
    return item_dict

def _versioned_inventory_query():
    return VisirayVersionInventory.query

def _find_versioned_inventory(part_id, part_version_id):
    if part_version_id in (None, ''):
        return None
    inventory_key = _inventory_key(part_id)
    if inventory_key is None:
        return None
    return VisirayVersionInventory.query.filter_by(
        goods_id=inventory_key,
        part_version_id=int(part_version_id)
    ).first()

def _load_inventory_for_part(part_id, part_version_id=None):
    if part_version_id not in (None, ''):
        inventory = _find_versioned_inventory(part_id, part_version_id)
        if inventory:
            return inventory, 'versioned'
        return None, 'versioned'
    inventory_key = _inventory_key(part_id)
    if inventory_key is None:
        return None, 'legacy'
    return VisirayInventory.query.get(inventory_key), 'legacy'

def _part_number_for_inventory_key(value):
    part = _find_part_number(value)
    return part.part_id if part else str(value) if value is not None else None

def _with_display_part_number(item_dict: dict) -> dict:
    goods_id = item_dict.get('goods_id')
    display_part_id = _part_number_for_inventory_key(goods_id)
    item_dict['part_id'] = display_part_id
    item_dict['display_goods_id'] = display_part_id
    if item_dict.get('part_version_id') is not None:
        item_dict = _versioned_inventory_display(item_dict)
    return item_dict

def _inventory_matches_for_keyword(keyword: str):
    keyword = (keyword or '').strip()
    if not keyword:
        return []

    search_term = f"%{keyword}%"
    parts = VisirayPartNumber.query.filter(
        (VisirayPartNumber.part_id.like(search_term)) |
        (VisirayPartNumber.part_name.like(search_term)) |
        (VisirayPartNumber.category.like(search_term)) |
        (VisirayPartNumber.main_type.like(search_term)) |
        (VisirayPartNumber.sub_type.like(search_term))
    ).limit(50).all()

    keys = []
    for part in parts:
        key = _inventory_key(part.part_id)
        if isinstance(key, int) and key not in keys:
            keys.append(key)
    return keys

def _inventory_key(value):
    stripped = _strip_part_prefix(_clean_part_number_input(value))
    digits = re.sub(r'\D', '', stripped)
    return int(digits) if digits else stripped

def _int_value(value, default=0):
    if value is None or value == '':
        return default
    return int(value)

def _int_or_none(value):
    if value is None or value == '':
        return None
    text = str(value).strip()
    return int(text) if text.isdigit() else None

def _to_float(value, default=0.0):
    if value is None or value == '':
        return default
    return float(value)

def _normalize_outbound_type(value):
    text = str(value or '').strip()
    legacy_types = {
        '\u9351\u54c4\u7c31': '出库',
        '\u95b8\u621d\u642b\u7ee8?': '出库',
        '\u95b8\u621d\u642b\u7ee8': '出库',
        '\u93b6\u30e5\u7c3e': '报废',
        '\u95b9\u8eb2\u5131\u7ee8?': '报废',
        '\u95b9\u8eb2\u5131\u7ee8': '报废',
    }
    return legacy_types.get(text, text or '出库')

def _generate_record_stamp():
    timestamp = datetime.now().strftime('%y%m%d%H%M%S')
    random_num = f"{uuid.uuid4().int % 10000:04d}"
    return f"{timestamp}{random_num}"

def _generate_unique_out_record_id():
    for _ in range(20):
        record_id = int(_generate_record_stamp())
        if not VisirayStockOutRecord.query.get(record_id):
            return record_id
    raise ValueError('出库记录号生成失败，请重试')

def _part_material_marker(part_id: str) -> str:
    return f"VISIRAY_PART_ID:{part_id}"

def _generate_part_material_code(part):
    material_type = 'purchase' if part.category == 'purchased' else 'custom'
    part_category = part.main_type if part.main_type in {'mechanical', 'optical', 'electrical'} else 'mechanical'
    for classification in range(0, 100):
        code = MaterialCodeService.generate_material_code(
            part_type=material_type,
            material_type=material_type,
            part_category=part_category,
            classification=classification,
            version=0,
        )
        if not Material.query.filter_by(material_code=code).first():
            return code
    raise ValueError("Unable to generate material code for part number")

def _sync_material_from_part_number(part, created_by=None):
    material = Material.query.filter_by(visiray_part_id=part.part_id).first()
    if not material:
        material = Material.query.filter_by(remark=_part_material_marker(part.part_id)).first()

    unit = part.unit or 'pcs'
    standard_cost = _to_float(part.standard_cost)
    specification = ' / '.join(filter(None, [part.category, part.main_type, part.sub_type]))

    if material:
        material.visiray_part_id = part.part_id
        material.material_name = part.part_name or part.sub_type or part.part_id
        material.specification = specification
        material.unit = unit
        material.standard_cost = standard_cost
        material.remark = _part_material_marker(part.part_id)
        return material

    material = Material(
        material_code=_generate_part_material_code(part),
        visiray_part_id=part.part_id,
        material_name=part.part_name or part.sub_type or part.part_id,
        specification=specification,
        unit=unit,
        standard_cost=standard_cost,
        currency='CNY',
        material_type='purchase' if part.category == 'purchased' else 'custom',
        status='active',
        created_by=created_by,
        remark=_part_material_marker(part.part_id),
    )
    material.parse_material_code()
    db.session.add(material)
    return material

def _part_supplier_payload(part):
    material = Material.query.filter_by(visiray_part_id=part.part_id).first()
    if not material:
        material = Material.query.filter_by(remark=_part_material_marker(part.part_id)).first()
    if not material:
        return {
            'material_id': None,
            'supplier_options': [],
            'version_supplier_options': {},
            'current_version_id': None,
            'supplier_count': 0,
            'has_multiple_suppliers': False
        }

    version_supplier_options = {}
    versions = VisirayPartNumberVersion.query.filter_by(part_id=part.part_id).all()
    for version in versions:
        version_supplier_options[str(version.id)] = [supplier.to_dict() for supplier in material.get_supplier_options(version.id)]

    current_version_id = part.current_version_id
    current_supplier_options = [supplier.to_dict() for supplier in material.get_supplier_options(current_version_id)]
    suppliers = (
        MaterialSupplier.query
        .filter_by(material_id=material.id, status='active')
        .order_by(MaterialSupplier.is_primary.desc(), MaterialSupplier.id.asc())
        .all()
    )
    return {
        'material_id': material.id,
        'supplier_options': current_supplier_options,
        'version_supplier_options': version_supplier_options,
        'current_version_id': current_version_id,
        'supplier_count': len(current_supplier_options),
        'has_multiple_suppliers': len(current_supplier_options) > 1
    }

def _supplier_payload_from_material(material, part, versions):
    if not material:
        return {
            'material_id': None,
            'supplier_options': [],
            'version_supplier_options': {},
            'current_version_id': None,
            'supplier_count': 0,
            'has_multiple_suppliers': False
        }

    active_suppliers = [
        supplier
        for supplier in sorted(
            list(material.suppliers),
            key=lambda item: (not bool(item.is_primary), item.id or 0)
        )
        if supplier.status == 'active'
    ]
    generic_suppliers = [supplier for supplier in active_suppliers if supplier.part_version_id is None]
    suppliers_by_version = {}
    for supplier in active_suppliers:
        if supplier.part_version_id is not None:
            suppliers_by_version.setdefault(supplier.part_version_id, []).append(supplier)

    version_supplier_options = {}
    for version in versions:
        exact = suppliers_by_version.get(version.id, [])
        version_supplier_options[str(version.id)] = [supplier.to_dict() for supplier in exact + generic_suppliers]

    current_version_id = part.current_version_id
    if current_version_id:
        current_supplier_records = suppliers_by_version.get(current_version_id, []) + generic_suppliers
    else:
        current_supplier_records = generic_suppliers
    current_supplier_options = [supplier.to_dict() for supplier in current_supplier_records]

    return {
        'material_id': material.id,
        'supplier_options': current_supplier_options,
        'version_supplier_options': version_supplier_options,
        'current_version_id': current_version_id,
        'supplier_count': len(current_supplier_options),
        'has_multiple_suppliers': len(current_supplier_options) > 1
    }

def _parse_date_value(value):
    if value in (None, ''):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError('日期格式错误，应为 YYYY-MM-DD')

def _supplier_display_dict(supplier):
    return {
        'id': supplier.id,
        'supplier_code': supplier.supplier_code,
        'supplier_name': supplier.supplier_name,
        'phone': supplier.phone,
        'email': supplier.email,
        'source': 'suppliers'
    }

def _visiray_supplier_display_dict(supplier):
    return {
        'id': supplier.id,
        'supplier_code': supplier.supplier_code,
        'supplier_name': supplier.supplier_name,
        'phone': supplier.phone,
        'email': supplier.email,
        'source': 'supplier_information'
    }

def _ensure_supplier_for_quote(supplier_code, created_by=None):
    code = (supplier_code or '').strip()
    if not code:
        raise ValueError('请选择供应商')

    supplier = Supplier.query.filter_by(supplier_code=code).first()
    if supplier:
        return supplier

    source = VisiraySupplierInformation.query.filter_by(supplier_code=code).first()
    if not source:
        raise ValueError('供应商不存在')

    supplier = Supplier(
        supplier_code=source.supplier_code,
        supplier_name=source.supplier_name or source.supplier_code,
        contact_person=source.contact_person,
        phone=source.phone,
        email=source.email,
        address=source.address,
        supplier_type='material',
        supplier_level='C',
        status='active',
        cooperation_status='cooperation',
        remark=source.remarks,
        is_active=True,
        created_by=created_by,
    )
    db.session.add(supplier)
    db.session.flush()
    return supplier

def _ensure_material_for_quote(part_id, created_by=None):
    part = VisirayPartNumber.query.get(part_id)
    if not part:
        part = _find_part_number(part_id)
    if not part:
        raise ValueError('零件号不存在，请先在零件号申请中创建')
    material = _sync_material_from_part_number(part, created_by)
    db.session.flush()
    return material, part

def _supplier_price_to_dict(item):
    material = item.material
    supplier = item.supplier
    version = VisirayPartNumberVersion.query.get(item.part_version_id) if item.part_version_id else None
    return {
        **item.to_dict(),
        'material_code': material.material_code if material else None,
        'material_name': material.material_name if material else None,
        'part_id': material.visiray_part_id if material else None,
        'supplier_code': supplier.supplier_code if supplier else None,
        'supplier_name': supplier.supplier_name if supplier else None,
        'version_no': version.version_no if version else None,
        'version_status': version.status if version else None,
        'version_is_current': bool(version.is_current) if version else False,
    }

# 闄勪欢涓婁紶閰嶇疆
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif', 'txt', 'csv',
    'ppt', 'pptx', 'zip', 'rar', '7z'
}
MAX_ATTACHMENTS_PER_ORDER = 100
MAX_FILE_SIZE_MB = 120

def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _get_attachment_folder():
    folder = current_app.config.get('ATTACHMENT_UPLOAD_FOLDER') or os.path.join(current_app.root_path, '..', 'uploads', 'attachments')
    os.makedirs(folder, exist_ok=True)
    return folder

def _safe_filename(filename: str) -> str:
    import re
    name = os.path.basename(filename or '')
    name = name.strip().replace('\x00', '')
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', name)
    root, ext = os.path.splitext(name)
    if not ext:
        ext = ''
    if not root:
        root = datetime.now().strftime('%Y%m%d%H%M%S') + '_' + uuid.uuid4().hex[:6]
    return f"{root}{ext}"

def _get_request_user():
    try:
        identity = get_jwt_identity()
    except Exception:
        identity = None
    if identity is not None:
        try:
            return User.query.get(int(identity))
        except Exception:
            pass
    if current_user.is_authenticated:
        return current_user
    try:
        acc = session.get('visiray_account')
        uname = session.get('visiray_username')
        if acc:
            return SimpleNamespace(
                id=None,
                name=uname,
                username=acc,
                email=None,
                is_active=True,
                has_role=lambda code: False,
            )
    except Exception:
        pass
    return None

def _is_admin_user(user) -> bool:
    if not user:
        return False
    try:
        if callable(getattr(user, 'has_role', None)) and user.has_role('admin'):
            return True
    except Exception:
        pass
    try:
        return any(getattr(role, 'code', None) == 'admin' for role in getattr(user, 'roles', []) if getattr(role, 'is_active', True))
    except Exception:
        return False

def _require_admin():
    user = _get_request_user()
    if not user or not getattr(user, 'is_active', True):
        return None, (jsonify({'success': False, 'message': '请先登录'}), 401)
    if not _is_admin_user(user):
        return None, (jsonify({'success': False, 'message': '仅管理员可以管理零件号规则'}), 403)
    return user, None

@bp.route('/visiray/inventory', methods=['GET'])
def get_visiray_inventory():
    """鑾峰彇Visiray搴撳瓨鏁版嵁"""
    try:
        query = VisirayInventory.query

        def get_filter_arg(name):
            return (request.args.get(name) or '').strip()
        
        # 鎼滅储鏉′欢
        keyword = get_filter_arg('keyword')
        if keyword:
            search_term = f"%{keyword}%"
            normalized_keyword = re.sub(r'^0+', '', keyword)
            conditions = (
                cast(VisirayInventory.goods_id, String).like(search_term) |
                (VisirayInventory.goods_name.like(search_term)) |
                (VisirayInventory.supplier.like(search_term)) |
                (VisirayInventory.product_model.like(search_term)) |
                (VisirayInventory.goods_type.like(search_term)) |
                (VisirayInventory.shelf_location.like(search_term))
            )
            if normalized_keyword and normalized_keyword != keyword:
                conditions = conditions | cast(VisirayInventory.goods_id, String).like(f"%{normalized_keyword}%")
            if keyword.isdigit():
                conditions = conditions | (VisirayInventory.goods_id == int(keyword))
            matching_inventory_ids = _inventory_matches_for_keyword(keyword)
            if matching_inventory_ids:
                conditions = conditions | VisirayInventory.goods_id.in_(matching_inventory_ids)
            query = query.filter(conditions)

        supplier = get_filter_arg('supplier')
        if supplier:
            query = query.filter(VisirayInventory.supplier.like(f"%{supplier}%"))

        goods_type = get_filter_arg('goods_type')
        if goods_type:
            query = query.filter(VisirayInventory.goods_type.like(f"%{goods_type}%"))

        shelf_location = get_filter_arg('shelf_location')
        if shelf_location:
            query = query.filter(VisirayInventory.shelf_location.like(f"%{shelf_location}%"))

        stock_status = get_filter_arg('stock_status')
        if stock_status == 'in_stock':
            query = query.filter(VisirayInventory.stock_quantity > 0)
        elif stock_status == 'out_of_stock':
            query = query.filter((VisirayInventory.stock_quantity == 0) | (VisirayInventory.stock_quantity.is_(None)))
        
        # 鍒嗛〉
        result = paginate_query(query)
        result['items'] = [_with_display_part_number(item.to_dict()) for item in result['items']]
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取库存数据失败: {str(e)}'
        }), 500

@bp.route('/visiray/inventory', methods=['POST'])
def create_visiray_inventory():
    """鍒涘缓Visiray搴撳瓨璁板綍"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        goods_id = data.get('goods_id')
        if not goods_id:
            return jsonify({'success': False, 'message': '零件号不能为空'}), 400

        inventory_goods_id = _inventory_key(goods_id)
        part = _find_part_number(goods_id)
        if part is None:
            return jsonify({'success': False, 'message': '零件号不存在，请先在零件号申请中创建'}), 400
        if VisirayInventory.query.get(inventory_goods_id):
            return jsonify({'success': False, 'message': '零件号已存在'}), 400
        
        # 鍒涘缓搴撳瓨璁板綍
        inventory = VisirayInventory(
            goods_id=inventory_goods_id,
            goods_name=data.get('goods_name') or part.part_name or part.sub_type or part.part_id,
            supplier=data.get('supplier'),
            product_model=data.get('product_model'),
            goods_type=data.get('goods_type') or part.main_type,
            in_quantity=_int_value(data.get('in_quantity'), 0),
            out_quantity=_int_value(data.get('out_quantity'), 0),
            stock_quantity=_int_value(data.get('stock_quantity'), 0),
            unit=data.get('unit') or part.unit,
            shelf_location=data.get('shelf_location'),
            in_record=data.get('in_record'),
            out_record=data.get('out_record'),
            attachments=data.get('attachments'),
            purchase_invoice=data.get('purchase_invoice'),
            invoice_info=data.get('invoice_info'),
            parent_record=data.get('parent_record')
        )
        
        db.session.add(inventory)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '库存记录创建成功',
            'data': _with_display_part_number(inventory.to_dict())
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建库存记录失败: {str(e)}'
        }), 500

@bp.route('/visiray/inventory/<int:goods_id>', methods=['PUT'])
def update_visiray_inventory(goods_id):
    """鏇存柊Visiray搴撳瓨璁板綍"""
    try:
        inventory = VisirayInventory.query.get(goods_id)
        if not inventory:
            return jsonify({
                'success': False,
                'message': '库存记录不存在'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 鏇存柊搴撳瓨璁板綍瀛楁
        updatable_fields = [
            'goods_name', 'supplier', 'product_model', 'goods_type',
            'in_quantity', 'out_quantity', 'stock_quantity', 'unit',
            'shelf_location', 'in_record', 'out_record', 'attachments',
            'purchase_invoice', 'invoice_info', 'parent_record'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(inventory, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '库存记录更新成功',
            'data': _with_display_part_number(inventory.to_dict())
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新库存记录失败: {str(e)}'
        }), 500

@bp.route('/visiray/inventory/<int:goods_id>', methods=['DELETE'])
def delete_visiray_inventory(goods_id):
    """鍒犻櫎Visiray搴撳瓨璁板綍"""
    try:
        inventory = VisirayInventory.query.get(goods_id)
        if not inventory:
            return jsonify({
                'success': False,
                'message': '库存记录不存在'
            }), 404
        
        db.session.delete(inventory)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '库存记录删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除库存记录失败: {str(e)}'
        }), 500

@bp.route('/visiray/versioned-inventory', methods=['GET'])
def get_visiray_versioned_inventory():
    try:
        query = VisirayVersionInventory.query

        keyword = (request.args.get('keyword') or '').strip()
        if keyword:
            search_term = f"%{keyword}%"
            normalized_keyword = re.sub(r'^0+', '', keyword)
            conditions = (
                cast(VisirayVersionInventory.goods_id, String).like(search_term) |
                cast(VisirayVersionInventory.part_version_id, String).like(search_term) |
                VisirayVersionInventory.goods_name.like(search_term) |
                VisirayVersionInventory.supplier.like(search_term) |
                VisirayVersionInventory.product_model.like(search_term) |
                VisirayVersionInventory.goods_type.like(search_term) |
                VisirayVersionInventory.shelf_location.like(search_term)
            )
            if normalized_keyword and normalized_keyword != keyword:
                conditions = conditions | cast(VisirayVersionInventory.goods_id, String).like(f"%{normalized_keyword}%")
            query = query.filter(conditions)

        part_version_id = (request.args.get('part_version_id') or '').strip()
        if part_version_id:
            query = query.filter(VisirayVersionInventory.part_version_id == int(part_version_id))

        result = paginate_query(query)
        result['items'] = [_versioned_inventory_display(item.to_dict()) for item in result['items']]
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取版本库存失败: {str(e)}'}), 500

@bp.route('/visiray/versioned-inventory', methods=['POST'])
def create_visiray_versioned_inventory():
    try:
        data = request.get_json() or {}
        part_id = data.get('goods_id') or data.get('part_id')
        part_version_id = _resolve_part_version_id(data.get('part_version_id'), part_id=part_id, require_active=False, allow_obsolete=True)
        if not part_id:
            return jsonify({'success': False, 'message': '零件号不能为空'}), 400
        if part_version_id is None:
            return jsonify({'success': False, 'message': '版本号不能为空'}), 400

        inventory_key = _inventory_key(part_id)
        version = _get_version_info(part_version_id)
        if not version:
            return jsonify({'success': False, 'message': '零件版本不存在'}), 404
        if VisirayVersionInventory.query.filter_by(goods_id=inventory_key, part_version_id=part_version_id).first():
            return jsonify({'success': False, 'message': '该零件版本库存已存在'}), 400

        inventory = VisirayVersionInventory(
            goods_id=inventory_key,
            part_version_id=part_version_id,
            goods_name=data.get('goods_name') or version.part_id,
            supplier=data.get('supplier'),
            product_model=data.get('product_model'),
            goods_type=data.get('goods_type'),
            in_quantity=_int_value(data.get('in_quantity'), 0),
            out_quantity=_int_value(data.get('out_quantity'), 0),
            stock_quantity=_int_value(data.get('stock_quantity'), 0),
            unit=data.get('unit'),
            shelf_location=data.get('shelf_location'),
            in_record=data.get('in_record'),
            out_record=data.get('out_record'),
            attachments=data.get('attachments'),
            purchase_invoice=data.get('purchase_invoice'),
            invoice_info=data.get('invoice_info'),
            parent_record=data.get('parent_record'),
        )
        db.session.add(inventory)
        db.session.commit()
        return jsonify({'success': True, 'message': '版本库存创建成功', 'data': _versioned_inventory_display(inventory.to_dict())}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建版本库存失败: {str(e)}'}), 500

@bp.route('/visiray/versioned-inventory/<int:inventory_id>', methods=['PUT'])
def update_visiray_versioned_inventory(inventory_id):
    try:
        inventory = VisirayVersionInventory.query.get(inventory_id)
        if not inventory:
            return jsonify({'success': False, 'message': '版本库存记录不存在'}), 404
        data = request.get_json() or {}
        updatable_fields = [
            'goods_name', 'supplier', 'product_model', 'goods_type',
            'in_quantity', 'out_quantity', 'stock_quantity', 'unit',
            'shelf_location', 'in_record', 'out_record', 'attachments',
            'purchase_invoice', 'invoice_info', 'parent_record'
        ]
        for field in updatable_fields:
            if field in data:
                setattr(inventory, field, data[field])
        db.session.commit()
        return jsonify({'success': True, 'message': '版本库存更新成功', 'data': _versioned_inventory_display(inventory.to_dict())})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新版本库存失败: {str(e)}'}), 500

@bp.route('/visiray/versioned-inventory/<int:inventory_id>', methods=['DELETE'])
def delete_visiray_versioned_inventory(inventory_id):
    try:
        inventory = VisirayVersionInventory.query.get(inventory_id)
        if not inventory:
            return jsonify({'success': False, 'message': '版本库存记录不存在'}), 404
        db.session.delete(inventory)
        db.session.commit()
        return jsonify({'success': True, 'message': '版本库存删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除版本库存失败: {str(e)}'}), 500

@bp.route('/visiray/inbound', methods=['GET'])
def get_visiray_inbound_records():
    """鑾峰彇Visiray鍏ュ簱璁板綍"""
    try:
        query = VisirayStockInRecord.query
        
        # 鎼滅储鏉′欢
        keyword = request.args.get('keyword')
        if keyword:
            search_term = f"%{keyword}%"
            normalized_keyword = re.sub(r'^0+', '', keyword)
            conditions = (
                (cast(VisirayStockInRecord.goods_id, String).like(search_term)) |
                (VisirayStockInRecord.in_record.like(search_term)) |
                (VisirayStockInRecord.supplier_name.like(search_term)) |
                (VisirayStockInRecord.product_model.like(search_term))
            )
            if normalized_keyword and normalized_keyword != keyword:
                conditions = conditions | cast(VisirayStockInRecord.goods_id, String).like(f"%{normalized_keyword}%")
            matching_inventory_ids = _inventory_matches_for_keyword(keyword)
            if matching_inventory_ids:
                conditions = conditions | VisirayStockInRecord.goods_id.in_(matching_inventory_ids)
            query = query.filter(conditions)
        
        query = query.order_by(
            VisirayStockInRecord.in_date.desc(),
            VisirayStockInRecord.in_record.desc(),
        )

        # 鍒嗛〉
        result = paginate_query(query)
        result['items'] = [_with_display_part_number(item.to_dict()) for item in result['items']]
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取入库记录失败: {str(e)}'
        }), 500

@bp.route('/visiray/inbound', methods=['POST'])
def create_visiray_inbound_record():
    """鍒涘缓Visiray鍏ュ簱璁板綍"""
    try:
        # 鑾峰彇鏁版嵁
        if request.is_json:
            data = request.get_json()
        else:
            # 濡傛灉鏄〃鍗曟暟鎹?
            data = request.form.to_dict()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 鐢熸垚鍏ュ簱璁板綍鍙凤紙濡傛灉鏈彁渚涳級
        in_record = data.get('in_record')
        if not in_record:
            # 鐢熸垚鍞竴鐨勫叆搴撹褰曞彿
            in_record = _generate_record_stamp()
        
        # 澶勭悊鍏ュ簱鏃ユ湡
        in_date_value = data.get('in_date')
        in_date = None
        if in_date_value:
            in_date = datetime.strptime(in_date_value, '%Y-%m-%d').date()
        else:
            in_date = datetime.now().date()
        
        goods_id_val = data.get('goods_id')
        if not goods_id_val:
            return jsonify({'success': False, 'message': '零件号不能为空'}), 400

        part = _find_part_number(goods_id_val)
        if part is None:
            return jsonify({'success': False, 'message': '零件号不存在，请先在零件号申请中创建'}), 400
        inventory_goods_id = _inventory_key(part.part_id)
        part_version_id = _resolve_part_version_id(
            data.get('part_version_id'),
            part_id=part.part_id,
            require_active=True,
        )

        inbound_type = data.get('inbound_type') or '入库'
        if inbound_type != '入库':
            return jsonify({'success': False, 'message': '入库操作只允许选择入库，报废请走出库或库存调整流程'}), 400
        supplier_value = data.get('supplier') or data.get('supplier_name')
        
        # 鍒涘缓鍏ュ簱璁板綍
        inbound_record = VisirayStockInRecord(
            in_record=in_record,
            goods_id=inventory_goods_id,
            supplier_name=supplier_value,
            quantity=_int_value(data.get('quantity'), 0),
            unit=data.get('unit'),
            in_date=in_date,
            operator=data.get('operator'),
            shelf_location=data.get('shelf_location'),
            goods_type=data.get('goods_type') or part.main_type,
            supplier=supplier_value,
            product_model=data.get('product_model'),
            parent_record=data.get('parent_record'),
            inbound_type=inbound_type,
            related_voucher=data.get('related_voucher'),
            part_version_id=part_version_id,
        )
        
        db.session.add(inbound_record)

        quantity = _int_value(data.get('quantity'), 0)
        if part_version_id is not None:
            inventory = _find_versioned_inventory(part.part_id, part_version_id)
            if not inventory:
                inventory = VisirayVersionInventory(
                    goods_id=inventory_goods_id,
                    part_version_id=part_version_id,
                    goods_name=data.get('goods_name') or part.part_name or part.sub_type or part.part_id,
                    supplier=supplier_value,
                    product_model=data.get('product_model'),
                    goods_type=data.get('goods_type') or part.main_type,
                    in_quantity=0,
                    out_quantity=0,
                    stock_quantity=0,
                    unit=data.get('unit') or part.unit,
                    shelf_location=data.get('shelf_location'),
                    in_record=None,
                    out_record=None,
                    parent_record=_int_or_none(data.get('parent_record'))
                )
                db.session.add(inventory)
            if inventory.in_quantity is None:
                inventory.in_quantity = 0
            if inventory.stock_quantity is None:
                inventory.stock_quantity = 0
            inventory.in_quantity += quantity
            inventory.stock_quantity += quantity
            inventory.goods_name = inventory.goods_name or data.get('goods_name') or part.part_name or part.sub_type or part.part_id
            inventory.unit = inventory.unit or data.get('unit') or part.unit
            inventory.shelf_location = data.get('shelf_location') or inventory.shelf_location
            inventory.goods_type = inventory.goods_type or data.get('goods_type') or part.main_type
            inventory.supplier = inventory.supplier or supplier_value
            inventory.product_model = inventory.product_model or data.get('product_model')
            if inventory.in_record:
                if in_record not in inventory.in_record:
                    inventory.in_record += f";{in_record}"
            else:
                inventory.in_record = in_record
        else:
            inventory = VisirayInventory.query.get(inventory_goods_id)
            if not inventory:
                inventory = VisirayInventory(
                    goods_id=inventory_goods_id,
                    goods_name=data.get('goods_name') or part.part_name or part.sub_type or part.part_id,
                    supplier=supplier_value,
                    product_model=data.get('product_model'),
                    goods_type=data.get('goods_type') or part.main_type,
                    in_quantity=0,
                    out_quantity=0,
                    stock_quantity=0,
                    unit=data.get('unit') or part.unit,
                    shelf_location=data.get('shelf_location'),
                    in_record=None,
                    out_record=None,
                    parent_record=_int_or_none(data.get('parent_record'))
                )
                db.session.add(inventory)

            if inventory.in_quantity is None:
                inventory.in_quantity = 0
            inventory.in_quantity += quantity
            if inventory.stock_quantity is None:
                inventory.stock_quantity = 0
            inventory.stock_quantity += quantity
            inventory.goods_name = inventory.goods_name or data.get('goods_name') or part.part_name or part.sub_type or part.part_id
            inventory.unit = inventory.unit or data.get('unit') or part.unit
            inventory.shelf_location = data.get('shelf_location') or inventory.shelf_location
            inventory.goods_type = inventory.goods_type or data.get('goods_type') or part.main_type
            inventory.supplier = inventory.supplier or supplier_value
            inventory.product_model = inventory.product_model or data.get('product_model')
            if inventory.in_record:
                if in_record not in inventory.in_record:
                    inventory.in_record += f";{in_record}"
            else:
                inventory.in_record = in_record

        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '入库记录创建成功',
            'data': _with_display_part_number(
                _versioned_inventory_display(inbound_record.to_dict()) if part_version_id is not None else inbound_record.to_dict()
            )
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建入库记录失败: {str(e)}'
        }), 500

@bp.route('/visiray/inbound/<string:in_record>', methods=['PUT'])
def update_visiray_inbound_record(in_record):
    """鏇存柊Visiray鍏ュ簱璁板綍"""
    try:
        inbound_record = VisirayStockInRecord.query.get(in_record)
        if not inbound_record:
            return jsonify({
                'success': False,
                'message': '入库记录不存在'
            }), 404
        old_quantity = _int_value(inbound_record.quantity, 0)
        old_goods_id = inbound_record.goods_id
        old_part_version_id = inbound_record.part_version_id
        old_inventory, old_inventory_kind = _load_inventory_for_part(old_goods_id, old_part_version_id)
        
        # 鑾峰彇鏁版嵁
        if request.is_json:
            data = request.get_json()
        else:
            # 濡傛灉鏄〃鍗曟暟鎹?
            data = request.form.to_dict()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        if data.get('inbound_type') and data.get('inbound_type') != '入库':
            return jsonify({'success': False, 'message': '入库操作只允许选择入库，报废请走出库或库存调整流程'}), 400
        if 'supplier_name' in data and 'supplier' not in data:
            data['supplier'] = data.get('supplier_name')
        
        # 鏇存柊鍏ュ簱璁板綍瀛楁
        updatable_fields = [
            'goods_id', 'supplier_name', 'quantity', 'unit',
            'in_date', 'operator', 'shelf_location', 'goods_type',
            'supplier', 'product_model', 'parent_record', 'inbound_type',
            'related_voucher'  # 娣诲姞related_voucher瀛楁
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'in_date' and data[field]:
                    setattr(inbound_record, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                else:
                    setattr(inbound_record, field, data[field])
        gid = data.get('goods_id')
        if gid is not None:
            normalized_gid = _inventory_key(gid)
            part = _find_part_number(gid)
            if part is None:
                return jsonify({'success': False, 'message': '零件号不存在，请先在零件号申请中创建'}), 400
            inbound_record.goods_id = normalized_gid
        if 'part_version_id' in data:
            inbound_record.part_version_id = _resolve_part_version_id(
                data.get('part_version_id'),
                part_id=inbound_record.goods_id,
                require_active=True,
            )
        
        new_part = _find_part_number(inbound_record.goods_id)
        new_quantity = _int_value(inbound_record.quantity, 0)
        new_part_version_id = inbound_record.part_version_id
        new_inventory, new_inventory_kind = _load_inventory_for_part(inbound_record.goods_id, new_part_version_id)
        if old_inventory:
            old_inventory.in_quantity = max(0, _int_value(old_inventory.in_quantity, 0) - old_quantity)
            old_inventory.stock_quantity = max(0, _int_value(old_inventory.stock_quantity, 0) - old_quantity)
            if old_inventory.in_record:
                records = [item for item in re.split(r'[;,；，]', old_inventory.in_record) if item and item != in_record]
                old_inventory.in_record = ';'.join(records) if records else None
        if new_part_version_id is not None and not new_inventory:
            version = _get_version_info(new_part_version_id)
            if not version:
                return jsonify({'success': False, 'message': '零件版本不存在'}), 400
            new_inventory = VisirayVersionInventory(
                goods_id=inbound_record.goods_id,
                part_version_id=new_part_version_id,
                goods_name=inbound_record.goods_name or new_part.part_name or new_part.sub_type or str(inbound_record.goods_id),
                supplier=inbound_record.supplier,
                product_model=inbound_record.product_model,
                goods_type=inbound_record.goods_type,
                in_quantity=0,
                out_quantity=0,
                stock_quantity=0,
                unit=inbound_record.unit,
                shelf_location=inbound_record.shelf_location,
                in_record=None,
                out_record=None,
                parent_record=_int_or_none(inbound_record.parent_record),
            )
            db.session.add(new_inventory)
        if new_part_version_id is None and not new_inventory:
            new_inventory = VisirayInventory.query.get(inbound_record.goods_id)
            if not new_inventory:
                return jsonify({'success': False, 'message': '库存中不存在该零件，请先入库'}), 400
        if new_inventory:
            new_inventory.in_quantity = _int_value(new_inventory.in_quantity, 0) + new_quantity
            new_inventory.stock_quantity = _int_value(new_inventory.stock_quantity, 0) + new_quantity
            if new_inventory.in_record:
                if in_record not in new_inventory.in_record:
                    new_inventory.in_record += f";{in_record}"
            else:
                new_inventory.in_record = in_record
            new_inventory.goods_name = new_inventory.goods_name or inbound_record.goods_name
            new_inventory.unit = new_inventory.unit or inbound_record.unit
            new_inventory.shelf_location = inbound_record.shelf_location or new_inventory.shelf_location
            new_inventory.goods_type = new_inventory.goods_type or inbound_record.goods_type
            new_inventory.supplier = new_inventory.supplier or inbound_record.supplier
            new_inventory.product_model = new_inventory.product_model or inbound_record.product_model
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '入库记录更新成功',
            'data': _with_display_part_number(
                _versioned_inventory_display(inbound_record.to_dict()) if inbound_record.part_version_id is not None else inbound_record.to_dict()
            )
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新入库记录失败: {str(e)}'
        }), 500

@bp.route('/visiray/inbound/<string:in_record>', methods=['DELETE'])
def delete_visiray_inbound_record(in_record):
    """鍒犻櫎Visiray鍏ュ簱璁板綍"""
    try:
        inbound_record = VisirayStockInRecord.query.get(in_record)
        if not inbound_record:
            return jsonify({
                'success': False,
                'message': '入库记录不存在'
            }), 404
        
        # 濡傛灉鍏宠仈浜嗗簱瀛橈紝闇€瑕佹洿鏂板簱瀛樻暟閲?
        if inbound_record.goods_id:
            inventory, inventory_kind = _load_inventory_for_part(inbound_record.goods_id, inbound_record.part_version_id)
            if inventory:
                if inventory.in_quantity is not None:
                    inventory.in_quantity = max(0, _int_value(inventory.in_quantity, 0) - _int_value(inbound_record.quantity, 0))
                if inventory.stock_quantity is not None:
                    inventory.stock_quantity = max(0, _int_value(inventory.stock_quantity, 0) - _int_value(inbound_record.quantity, 0))
                    
                # 鏇存柊鍏ュ簱璁板綍瀛楁
                if inventory.in_record:
                    in_records = re.split(r'[;,；，]', inventory.in_record)
                    if in_record in in_records:
                        in_records.remove(in_record)
                        inventory.in_record = ';'.join([item for item in in_records if item]) if in_records else None
                        
                db.session.commit()
        
        db.session.delete(inbound_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '入库记录删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除入库记录失败: {str(e)}'
        }), 500

@bp.route('/visiray/inbound/<string:in_record>/voucher', methods=['GET'])
def get_visiray_inbound_voucher(in_record):
    """鑾峰彇Visiray鍏ュ簱璁板綍鍏宠仈鍑瘉"""
    try:
        inbound_record = VisirayStockInRecord.query.get(in_record)
        if not inbound_record or not inbound_record.related_voucher:
            return jsonify({
                'success': False,
                'message': '关联凭证不存在'
            }), 404
        
        # 杩斿洖閲囪喘鍗曞彿浣滀负鍏宠仈鍑瘉
        return jsonify({
            'success': True,
            'data': {
                'purchase_order_no': inbound_record.related_voucher
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取关联凭证失败: {str(e)}'
        }), 500

@bp.route('/visiray/outbound', methods=['GET'])
def get_visiray_outbound_records():
    """鑾峰彇Visiray鍑哄簱璁板綍"""
    try:
        query = VisirayStockOutRecord.query
        
        # 鎼滅储鏉′欢
        keyword = request.args.get('keyword')
        if keyword:
            search_term = f"%{keyword}%"
            normalized_keyword = re.sub(r'^0+', '', keyword)
            conditions = (
                (cast(VisirayStockOutRecord.out_record_id, String).like(search_term)) |
                (cast(VisirayStockOutRecord.goods_id, String).like(search_term)) |
                (VisirayStockOutRecord.goods_name.like(search_term)) |
                (VisirayStockOutRecord.operator.like(search_term))
            )
            if normalized_keyword and normalized_keyword != keyword:
                conditions = conditions | cast(VisirayStockOutRecord.goods_id, String).like(f"%{normalized_keyword}%")
            matching_inventory_ids = _inventory_matches_for_keyword(keyword)
            if matching_inventory_ids:
                conditions = conditions | VisirayStockOutRecord.goods_id.in_(matching_inventory_ids)
            query = query.filter(conditions)
        
        query = query.order_by(
            VisirayStockOutRecord.out_date.desc(),
            VisirayStockOutRecord.out_record_id.desc(),
        )

        # 鍒嗛〉
        result = paginate_query(query)
        items = []
        for item in result['items']:
            item_dict = _with_display_part_number(item.to_dict())
            item_dict['outbound_type'] = _normalize_outbound_type(item_dict.get('outbound_type'))
            items.append(item_dict)
        result['items'] = items
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取出库记录失败: {str(e)}'
        }), 500

@bp.route('/visiray/outbound', methods=['POST'])
def create_visiray_outbound_record():
    """鍒涘缓Visiray鍑哄簱璁板綍"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 鐢熸垚鍑哄簱璁板綍ID
        out_record_id = _generate_unique_out_record_id()
        
        goods_id_val = data.get('goods_id')
        if not goods_id_val:
            return jsonify({'success': False, 'message': '零件号不能为空'}), 400

        part = _find_part_number(goods_id_val)
        if part is None:
            return jsonify({'success': False, 'message': '零件号不存在，请先在零件号申请中创建'}), 400
        part_version_id = _resolve_part_version_id(
            data.get('part_version_id'),
            part_id=part.part_id,
            require_active=False,
            allow_obsolete=True,
        )
        
        # 鍒涘缓鍑哄簱璁板綍
        # 闆朵欢蹇呴』瀛樺湪浜庡簱瀛樹腑锛屽悕绉颁粠搴撳瓨璇诲彇
        inventory, inventory_kind = _load_inventory_for_part(part.part_id, part_version_id)
        if not inventory:
            return jsonify({'success': False, 'message': '库存中不存在该零件，请先入库'}), 400

        quantity = _int_value(data.get('quantity'), 0)
        current_stock = _int_value(inventory.stock_quantity, 0)
        if quantity <= 0:
            return jsonify({'success': False, 'message': '出库数量必须大于0'}), 400
        if quantity > current_stock:
            return jsonify({
                'success': False,
                'message': f'库存不足，当前库存为{current_stock}，本次出库数量为{quantity}'
            }), 400

        outbound_record = VisirayStockOutRecord(
            out_record_id=out_record_id,
            goods_id=_inventory_key(part.part_id),
            goods_name=inventory.goods_name,
            quantity=quantity,
            out_date=datetime.strptime(data.get('out_date'), '%Y-%m-%d').date() if data.get('out_date') else datetime.now().date(),
            operator=data.get('operator'),
            shelf_location=data.get('shelf_location'),
            outbound_type=_normalize_outbound_type(data.get('outbound_type')),
            part_version_id=part_version_id,
        )
        
        db.session.add(outbound_record)
        
        if inventory.out_quantity is None:
            inventory.out_quantity = 0
        inventory.out_quantity += quantity
        inventory.stock_quantity = current_stock - quantity

        if inventory.out_record:
            inventory.out_record += f",{out_record_id}"
        else:
            inventory.out_record = str(out_record_id)

        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '出库记录创建成功',
            'data': _versioned_inventory_display(_with_display_part_number(outbound_record.to_dict())) if part_version_id is not None else _with_display_part_number(outbound_record.to_dict())
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建出库记录失败: {str(e)}'
        }), 500

@bp.route('/visiray/outbound/by-bom', methods=['POST'])
def create_visiray_outbound_records_by_bom():
    """按BOM一次性出库多个零件"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400

        bom_id = data.get('bom_id')
        if not bom_id:
            return jsonify({'success': False, 'message': '请选择BOM'}), 400

        production_quantity = _to_float(data.get('quantity'), 0)
        if production_quantity <= 0:
            return jsonify({'success': False, 'message': '生产数量必须大于0'}), 400

        outbound_type = _normalize_outbound_type(data.get('outbound_type'))
        operator = data.get('operator')
        out_date = datetime.strptime(data.get('out_date'), '%Y-%m-%d').date() if data.get('out_date') else datetime.now().date()

        shortage_report = BOMService.get_bom_shortage(int(bom_id), production_quantity)
        requirement_items = [item for item in shortage_report.get('items', []) if _to_float(item.get('required_quantity'), 0) > 0]
        if not requirement_items:
            return jsonify({'success': False, 'message': '该BOM没有可出库零件'}), 400

        invalid_items = []
        outbound_plan = []
        for item in requirement_items:
            required_quantity = _to_float(item.get('required_quantity'), 0)
            rounded_quantity = round(required_quantity)
            if abs(required_quantity - rounded_quantity) > 0.0001:
                invalid_items.append({
                    'part_id': item.get('part_id') or item.get('material_code'),
                    'version_no': item.get('version_no'),
                    'material_name': item.get('material_name'),
                    'required_quantity': required_quantity,
                    'reason': '出库记录数量字段只支持整数'
                })
                continue

            inventory_goods_id = item.get('inventory_goods_id')
            part_version_id = item.get('part_version_id')
            inventory = None
            if inventory_goods_id is not None:
                if part_version_id is not None:
                    inventory = VisirayVersionInventory.query.filter_by(
                        goods_id=inventory_goods_id,
                        part_version_id=part_version_id
                    ).first()
                else:
                    inventory = VisirayInventory.query.get(inventory_goods_id)
            stock_quantity = _int_value(inventory.stock_quantity, 0) if inventory else 0
            quantity = int(rounded_quantity)
            if not inventory:
                invalid_items.append({
                    'part_id': item.get('part_id') or item.get('material_code'),
                    'version_no': item.get('version_no'),
                    'material_name': item.get('material_name'),
                    'required_quantity': quantity,
                    'reason': '库存中不存在该零件，请先入库'
                })
                continue
            if quantity > stock_quantity:
                invalid_items.append({
                    'part_id': item.get('part_id') or item.get('material_code'),
                    'version_no': item.get('version_no'),
                    'material_name': item.get('material_name'),
                    'required_quantity': quantity,
                    'stock_quantity': stock_quantity,
                    'reason': '库存不足'
                })
                continue

            outbound_plan.append((item, inventory, quantity))

        if invalid_items:
            return jsonify({
                'success': False,
                'message': f'BOM出库校验失败，共{len(invalid_items)}项不能出库',
                'data': {
                    'invalid_items': invalid_items
                }
            }), 400

        created_records = []
        for item, inventory, quantity in outbound_plan:
            out_record_id = _generate_unique_out_record_id()
            outbound_record = VisirayStockOutRecord(
                out_record_id=out_record_id,
                goods_id=inventory.goods_id,
                goods_name=inventory.goods_name,
                quantity=quantity,
                out_date=out_date,
                operator=operator,
                shelf_location=inventory.shelf_location,
                outbound_type=outbound_type,
                part_version_id=item.get('part_version_id'),
            )
            db.session.add(outbound_record)

            inventory.out_quantity = _int_value(inventory.out_quantity, 0) + quantity
            inventory.stock_quantity = _int_value(inventory.stock_quantity, 0) - quantity
            if inventory.out_record:
                inventory.out_record += f",{out_record_id}"
            else:
                inventory.out_record = str(out_record_id)

            created_records.append(outbound_record)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'BOM出库成功，共生成{len(created_records)}条出库记录',
                'data': {
                    'bom_id': int(bom_id),
                    'bom_code': shortage_report.get('bom_code'),
                    'product_name': shortage_report.get('product_name'),
                    'production_quantity': production_quantity,
                    'records': [_versioned_inventory_display(_with_display_part_number(record.to_dict())) if record.part_version_id is not None else _with_display_part_number(record.to_dict()) for record in created_records]
                }
            }), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'按BOM出库失败: {str(e)}'
        }), 500

@bp.route('/visiray/outbound/<int:out_record_id>', methods=['PUT'])
def update_visiray_outbound_record(out_record_id):
    """鏇存柊Visiray鍑哄簱璁板綍"""
    try:
        outbound_record = VisirayStockOutRecord.query.get(out_record_id)
        if not outbound_record:
            return jsonify({
                'success': False,
                'message': '出库记录不存在'
            }), 404
        old_goods_id = outbound_record.goods_id
        old_quantity = _int_value(outbound_record.quantity, 0)
        old_part_version_id = outbound_record.part_version_id
        old_inventory, old_inventory_kind = _load_inventory_for_part(old_goods_id, old_part_version_id)
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400

        new_goods_id = _inventory_key(data.get('goods_id')) if data.get('goods_id') is not None else old_goods_id
        new_quantity = _int_value(data.get('quantity'), old_quantity)

        if new_quantity <= 0:
            return jsonify({'success': False, 'message': '出库数量必须大于0'}), 400

        if data.get('goods_id') is not None and _find_part_number(data.get('goods_id')) is None:
            return jsonify({'success': False, 'message': '零件号不存在，请先在零件号申请中创建'}), 400

        part_for_new = _find_part_number(data.get('goods_id')) if data.get('goods_id') is not None else _find_part_number(old_goods_id)
        new_part_version_id = outbound_record.part_version_id
        if 'part_version_id' in data:
            new_part_version_id = _resolve_part_version_id(
                data.get('part_version_id'),
                part_id=(part_for_new.part_id if part_for_new else None),
                require_active=False,
                allow_obsolete=True,
            )
        new_inventory, new_inventory_kind = _load_inventory_for_part(new_goods_id, new_part_version_id)
        if not new_inventory:
            return jsonify({'success': False, 'message': '库存中不存在该零件，请先入库'}), 400

        if new_goods_id == old_goods_id and new_part_version_id == old_part_version_id:
            available_stock = _int_value(new_inventory.stock_quantity, 0) + old_quantity
            if new_quantity > available_stock:
                return jsonify({
                    'success': False,
                    'message': f'库存不足，当前可用库存为{available_stock}，本次出库数量为{new_quantity}'
                }), 400
            new_inventory.stock_quantity = available_stock - new_quantity
            new_inventory.out_quantity = max(0, _int_value(new_inventory.out_quantity, 0) - old_quantity + new_quantity)
        else:
            available_stock = _int_value(new_inventory.stock_quantity, 0)
            if new_quantity > available_stock:
                return jsonify({
                    'success': False,
                    'message': f'库存不足，当前库存为{available_stock}，本次出库数量为{new_quantity}'
                }), 400

            if old_inventory:
                old_inventory.stock_quantity = _int_value(old_inventory.stock_quantity, 0) + old_quantity
                old_inventory.out_quantity = max(0, _int_value(old_inventory.out_quantity, 0) - old_quantity)
                if old_inventory.out_record:
                    record_ids = [item for item in old_inventory.out_record.split(',') if item != str(out_record_id)]
                    old_inventory.out_record = ','.join(record_ids) if record_ids else None

            new_inventory.stock_quantity = available_stock - new_quantity
            new_inventory.out_quantity = _int_value(new_inventory.out_quantity, 0) + new_quantity
            if new_inventory.out_record:
                if str(out_record_id) not in new_inventory.out_record.split(','):
                    new_inventory.out_record += f",{out_record_id}"
            else:
                new_inventory.out_record = str(out_record_id)

        outbound_record.goods_id = new_goods_id
        outbound_record.goods_name = new_inventory.goods_name
        outbound_record.quantity = new_quantity
        outbound_record.part_version_id = new_part_version_id
        if data.get('out_date'):
            outbound_record.out_date = datetime.strptime(data.get('out_date'), '%Y-%m-%d').date()
        if 'operator' in data:
            outbound_record.operator = data.get('operator')
        if 'shelf_location' in data:
            outbound_record.shelf_location = data.get('shelf_location')
        if 'outbound_type' in data:
            outbound_record.outbound_type = _normalize_outbound_type(data.get('outbound_type'))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '出库记录更新成功',
            'data': _versioned_inventory_display(_with_display_part_number(outbound_record.to_dict())) if outbound_record.part_version_id is not None else _with_display_part_number(outbound_record.to_dict())
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新出库记录失败: {str(e)}'
        }), 500

@bp.route('/visiray/outbound/<int:out_record_id>', methods=['DELETE'])
def delete_visiray_outbound_record(out_record_id):
    """鍒犻櫎Visiray鍑哄簱璁板綍"""
    try:
        outbound_record = VisirayStockOutRecord.query.get(out_record_id)
        if not outbound_record:
            return jsonify({
                'success': False,
                'message': '出库记录不存在'
            }), 404
        
        # 濡傛灉鍏宠仈浜嗗簱瀛橈紝闇€瑕佹洿鏂板簱瀛樻暟閲?
        if outbound_record.goods_id:
            inventory, inventory_kind = _load_inventory_for_part(outbound_record.goods_id, outbound_record.part_version_id)
            if inventory:
                if inventory.out_quantity is not None:
                    inventory.out_quantity = max(0, _int_value(inventory.out_quantity, 0) - _int_value(outbound_record.quantity, 0))
                if inventory.stock_quantity is not None:
                    inventory.stock_quantity += _int_value(outbound_record.quantity, 0)
                if inventory.stock_quantity < 0:
                    inventory.stock_quantity = 0
                    
                # 鏇存柊鍑哄簱璁板綍瀛楁
                if inventory.out_record:
                    out_records = inventory.out_record.split(',')
                    out_record_str = str(out_record_id)
                    if out_record_str in out_records:
                        out_records.remove(out_record_str)
                        inventory.out_record = ','.join(out_records) if out_records else None
                        
                db.session.commit()
        
        db.session.delete(outbound_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '出库记录删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除出库记录失败: {str(e)}'
        }), 500

@bp.route('/visiray/purchase-orders', methods=['GET'])
def get_visiray_purchase_orders():
    """鑾峰彇Visiray閲囪喘鍏ュ簱鍗曟暟鎹?"""
    try:
        query = VisirayPurchaseReceivingVoucher.query
        
        # 鎼滅储鏉′欢
        keyword = request.args.get('keyword')
        if keyword:
            search_term = f"%{keyword}%"
            query = query.filter(
                (VisirayPurchaseReceivingVoucher.purchase_order_no.like(search_term)) |
                (VisirayPurchaseReceivingVoucher.supplier.like(search_term)) |
                (VisirayPurchaseReceivingVoucher.product_name.like(search_term))
            )
        
        # 鍒嗛〉
        result = paginate_query(query)

        # 涓虹‘淇濆噯纭€э紝閫愭潯璁＄畻闄勪欢鏁帮紙姣忛〉涓嶅ぇ锛屾€ц兘鍙帴鍙楋級
        items_with_counts = []
        for item in result['items']:
            cnt = VisirayPurchaseAttachment.query.filter_by(purchase_order_no=item.purchase_order_no).count()
            items_with_counts.append({**item.to_dict(), 'attachment_count': int(cnt)})
        result['items'] = items_with_counts
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取采购入库单数据失败: {str(e)}'
        }), 500

@bp.route('/visiray/purchase-orders', methods=['POST'])
def create_visiray_purchase_order():
    """鍒涘缓Visiray閲囪喘鍏ュ簱鍗?"""
    try:
        # 纭繚涓婁紶鏂囦欢澶瑰瓨鍦?
        invoice_folder = os.path.join(current_app.root_path, '..', 'uploads', 'invoices')
        contract_folder = os.path.join(current_app.root_path, '..', 'uploads', 'contracts')
        
        # 鍒涘缓鏂囦欢澶癸紙濡傛灉涓嶅瓨鍦級
        os.makedirs(invoice_folder, exist_ok=True)
        os.makedirs(contract_folder, exist_ok=True)
        
        # 澶勭悊鏂囦欢涓婁紶
        invoice_filename = None
        contract_filename = None
        
        if 'invoice_no' in request.files:
            invoice_file = request.files['invoice_no']
            if invoice_file and invoice_file.filename:
                filename = _safe_filename(invoice_file.filename)
                file_path = os.path.join(invoice_folder, filename)
                invoice_file.save(file_path)
                invoice_filename = filename
                
        if 'contract_pdf' in request.files:
            contract_file = request.files['contract_pdf']
            if contract_file and contract_file.filename:
                filename = _safe_filename(contract_file.filename)
                file_path = os.path.join(contract_folder, filename)
                contract_file.save(file_path)
                contract_filename = filename
        
        # 鑾峰彇鍏朵粬鏁版嵁
        if request.is_json:
            data = request.get_json()
        else:
            # 濡傛灉鏄〃鍗曟暟鎹?
            data = request.form.to_dict()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 鐢熸垚閲囪喘鍗曞彿锛堝鏋滄湭鎻愪緵鎴栦负绌猴級
        purchase_order_no = data.get('purchase_order_no')
        if not purchase_order_no:
            # 鐢熸垚鍞竴鐨勯噰璐崟鍙凤紝鏍煎紡锛歅O + YYYYMMDD + HHMMSS + 4浣嶉殢鏈烘暟
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_num = str(uuid.uuid4().int)[:4]
            purchase_order_no = f"PO{timestamp}{random_num}"
        
        # 澶勭悊鍏ュ簱鏃堕棿
        receiving_time_value = data.get('receiving_time')
        receiving_time = None
        if receiving_time_value:
            receiving_time = datetime.strptime(receiving_time_value, '%Y-%m-%d').date()
        else:
            receiving_time = datetime.now().date()
        
        pc = (data.get('product_code') or '').strip()
        if not pc:
            return jsonify({'success': False, 'message': '零件号不能为空'}), 400
        if not VisirayPartNumber.query.get(pc):
            return jsonify({'success': False, 'message': '零件号不存在，请先在零件号申请中创建'}), 400
        
        # 鍒涘缓閲囪喘鍏ュ簱鍗?
        purchase_order = VisirayPurchaseReceivingVoucher(
            purchase_order_no=purchase_order_no,
            product_code=data.get('product_code'),
            product_name=data.get('product_name'),
            quantity=data.get('quantity'),
            unit=data.get('unit'),
            product_type=data.get('product_type'),
            unit_price=data.get('unit_price'),
            receiving_time=receiving_time,
            status=data.get('status', '待入库'),
            supplier=data.get('supplier'),
            invoice_no=invoice_filename,  # 浠呭瓨鍌ㄦ枃浠跺悕
            contract_pdf=contract_filename  # 浠呭瓨鍌ㄦ枃浠跺悕
        )
        
        db.session.add(purchase_order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '采购单创建成功',
            'data': purchase_order.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建采购单失败: {str(e)}'
        }), 500


@bp.route('/visiray/purchase-orders/<string:purchase_order_no>/attachments', methods=['GET'])
@jwt_required(optional=True)
def list_purchase_attachments(purchase_order_no):
    try:
        user = _get_request_user()
        if not user or not user.is_active:
            return jsonify({'success': False, 'message': '用户无效'}), 401
        if not (user.has_permission('purchase_attachment_read') or user.has_role('admin')):
            return jsonify({'success': False, 'message': '权限不足'}), 403
        items = VisirayPurchaseAttachment.query.filter_by(purchase_order_no=purchase_order_no).order_by(VisirayPurchaseAttachment.id.desc()).all()
        return jsonify({'success': True, 'data': [i.to_dict() for i in items]})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取附件失败: {str(e)}'}), 500


@bp.route('/visiray/purchase-orders/<string:purchase_order_no>/attachments', methods=['POST'])
@jwt_required(optional=True)
def upload_purchase_attachments(purchase_order_no):
    try:
        user = _get_request_user()
        if not user or not user.is_active:
            return jsonify({'success': False, 'message': '用户无效'}), 401
        if not (user.has_permission('purchase_attachment_create') or user.has_role('admin')):
            return jsonify({'success': False, 'message': '权限不足'}), 403
        order = VisirayPurchaseReceivingVoucher.query.filter_by(purchase_order_no=purchase_order_no).first()
        if not order:
            return jsonify({'success': False, 'message': '采购单不存在'}), 404

        existing_count = VisirayPurchaseAttachment.query.filter_by(purchase_order_no=purchase_order_no).count()
        files = request.files.getlist('files') or []
        if not files:
            return jsonify({'success': False, 'message': '未选择文件'}), 400

        if existing_count + len(files) > MAX_ATTACHMENTS_PER_ORDER:
            return jsonify({'success': False, 'message': f'附件数量超限，每个采购单最多{MAX_ATTACHMENTS_PER_ORDER}个'}), 400

        saved = []
        folder = _get_attachment_folder()
        for f in files:
            original = f.filename
            if not original:
                continue
            if not _allowed_file(original):
                return jsonify({'success': False, 'message': f'文件格式不支持: {original}'}), 400

            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(0)
            if size > MAX_FILE_SIZE_MB * 1024 * 1024:
                return jsonify({'success': False, 'message': f'文件过大(>{MAX_FILE_SIZE_MB}MB): {original}'}), 400

            safe_name = secure_filename(original)
            unique_name = f"{purchase_order_no}_{uuid.uuid4().hex}_{safe_name}"
            path = os.path.join(folder, unique_name)
            f.save(path)

            att = VisirayPurchaseAttachment(
                purchase_order_no=purchase_order_no,
                stored_filename=unique_name,
                original_filename=original,
                content_type=f.mimetype,
                file_size=size,
                uploaded_by=getattr(user, 'id', None)
            )
            db.session.add(att)
            saved.append(att)

        db.session.commit()
        current_app.logger.info(f"附件上传: {purchase_order_no}, 数量={len(saved)}, 用户={getattr(user, 'id', None)}")
        return jsonify({'success': True, 'message': '附件上传成功', 'data': [a.to_dict() for a in saved]}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'附件上传失败: {str(e)}'}), 500


@bp.route('/visiray/purchase-orders/<string:purchase_order_no>/attachments/<int:attachment_id>', methods=['GET'])
@jwt_required(optional=True)
def download_purchase_attachment(purchase_order_no, attachment_id):
    try:
        user = _get_request_user()
        if not user or not user.is_active:
            return jsonify({'success': False, 'message': '用户无效'}), 401
        if not (user.has_permission('purchase_attachment_download') or user.has_permission('purchase_attachment_read') or user.has_role('admin')):
            return jsonify({'success': False, 'message': '权限不足'}), 403
        att = VisirayPurchaseAttachment.query.filter_by(id=attachment_id, purchase_order_no=purchase_order_no).first()
        if not att:
            return jsonify({'success': False, 'message': '附件不存在'}), 404
        path = os.path.join(_get_attachment_folder(), att.stored_filename)
        if not os.path.exists(path):
            return jsonify({'success': False, 'message': '文件不存在'}), 404
        return Response(
            open(path, 'rb').read(),
            mimetype=att.content_type or 'application/octet-stream',
            headers={'Content-Disposition': f'attachment; filename={att.original_filename}'}
        )
    except Exception as e:
        return jsonify({'success': False, 'message': f'下载失败: {str(e)}'}), 500


@bp.route('/visiray/purchase-orders/<string:purchase_order_no>/attachments/<int:attachment_id>/preview', methods=['GET'])
@jwt_required(optional=True)
def preview_purchase_attachment(purchase_order_no, attachment_id):
    try:
        user = _get_request_user()
        if not user or not user.is_active:
            return jsonify({'success': False, 'message': '用户无效'}), 401
        if not (user.has_permission('purchase_attachment_read') or user.has_role('admin')):
            return jsonify({'success': False, 'message': '权限不足'}), 403
        att = VisirayPurchaseAttachment.query.filter_by(id=attachment_id, purchase_order_no=purchase_order_no).first()
        if not att:
            return jsonify({'success': False, 'message': '附件不存在'}), 404
        path = os.path.join(_get_attachment_folder(), att.stored_filename)
        if not os.path.exists(path):
            return jsonify({'success': False, 'message': '文件不存在'}), 404
        return Response(
            open(path, 'rb').read(),
            mimetype=att.content_type or 'application/octet-stream',
            headers={'Content-Disposition': f'inline; filename={att.original_filename}'}
        )
    except Exception as e:
        return jsonify({'success': False, 'message': f'预览失败: {str(e)}'}), 500


@bp.route('/visiray/purchase-orders/<string:purchase_order_no>/attachments/<int:attachment_id>', methods=['DELETE'])
@jwt_required(optional=True)
def delete_purchase_attachment(purchase_order_no, attachment_id):
    try:
        user = _get_request_user()
        if not user or not user.is_active:
            return jsonify({'success': False, 'message': '用户无效'}), 401
        if not (user.has_permission('purchase_attachment_delete') or user.has_role('admin')):
            return jsonify({'success': False, 'message': '权限不足'}), 403
        att = VisirayPurchaseAttachment.query.filter_by(id=attachment_id, purchase_order_no=purchase_order_no).first()
        if not att:
            return jsonify({'success': False, 'message': '附件不存在'}), 404
        path = os.path.join(_get_attachment_folder(), att.stored_filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
        db.session.delete(att)
        db.session.commit()
        current_app.logger.info(f"附件删除: {purchase_order_no}, 附件ID={attachment_id}, 用户={getattr(user, 'id', None)}")
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

@bp.route('/visiray/purchase-orders/<string:purchase_order_no>', methods=['PUT'])
def update_visiray_purchase_order(purchase_order_no):
    """鏇存柊Visiray閲囪喘鍏ュ簱鍗?"""
    try:
        import os
        from werkzeug.utils import secure_filename
        
        # 纭繚涓婁紶鏂囦欢澶瑰瓨鍦?
        invoice_folder = os.path.join(current_app.root_path, '..', 'uploads', 'invoices')
        contract_folder = os.path.join(current_app.root_path, '..', 'uploads', 'contracts')
        
        # 鍒涘缓鏂囦欢澶癸紙濡傛灉涓嶅瓨鍦級
        os.makedirs(invoice_folder, exist_ok=True)
        os.makedirs(contract_folder, exist_ok=True)
        
        purchase_order = VisirayPurchaseReceivingVoucher.query.filter_by(purchase_order_no=purchase_order_no).first()
        if not purchase_order:
            return jsonify({
                'success': False,
                'message': '采购单不存在'
            }), 404
        
        # 澶勭悊鏂囦欢涓婁紶
        invoice_filename = purchase_order.invoice_no  # 淇濇寔鍘熸湁鏂囦欢鍚?
        contract_filename = purchase_order.contract_pdf  # 淇濇寔鍘熸湁鏂囦欢鍚?
        
        if 'invoice_no' in request.files:
            invoice_file = request.files['invoice_no']
            if invoice_file and invoice_file.filename:
                filename = _safe_filename(invoice_file.filename)
                file_path = os.path.join(invoice_folder, filename)
                invoice_file.save(file_path)
                invoice_filename = filename
                
        if 'contract_pdf' in request.files:
            contract_file = request.files['contract_pdf']
            if contract_file and contract_file.filename:
                filename = _safe_filename(contract_file.filename)
                file_path = os.path.join(contract_folder, filename)
                contract_file.save(file_path)
                contract_filename = filename
        
        # 鑾峰彇鍏朵粬鏁版嵁
        if request.is_json:
            data = request.get_json()
        else:
            # 濡傛灉鏄〃鍗曟暟鎹?
            data = request.form.to_dict()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 鏇存柊閲囪喘鍏ュ簱鍗曞瓧娈?
        updatable_fields = [
            'product_code', 'product_name', 'quantity', 'unit',
            'product_type', 'unit_price', 'status', 'supplier'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(purchase_order, field, data[field])
        
        # 鐗瑰埆澶勭悊鏃堕棿瀛楁
        if 'receiving_time' in data and data['receiving_time']:
            receiving_time = datetime.strptime(data['receiving_time'], '%Y-%m-%d').date()
            setattr(purchase_order, 'receiving_time', receiving_time)
        
        # 鐗瑰埆澶勭悊鏂囦欢瀛楁
        setattr(purchase_order, 'invoice_no', invoice_filename)
        setattr(purchase_order, 'contract_pdf', contract_filename)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '采购单更新成功',
            'data': purchase_order.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新采购单失败: {str(e)}'
        }), 500

@bp.route('/visiray/purchase-orders/<string:purchase_order_no>', methods=['DELETE'])
def delete_visiray_purchase_order(purchase_order_no):
    """鍒犻櫎Visiray閲囪喘鍏ュ簱鍗?"""
    try:
        purchase_order = VisirayPurchaseReceivingVoucher.query.filter_by(purchase_order_no=purchase_order_no).first()
        if not purchase_order:
            return jsonify({
                'success': False,
                'message': '采购单不存在'
            }), 404
        
        db.session.delete(purchase_order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '采购单删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除采购单失败: {str(e)}'
        }), 500

@bp.route('/visiray/purchase-orders/<string:purchase_order_no>/invoice', methods=['GET'])
def get_visiray_purchase_invoice(purchase_order_no):
    """鑾峰彇Visiray閲囪喘鍙戠エPDF"""
    try:
        import os
        
        purchase_order = VisirayPurchaseReceivingVoucher.query.filter_by(purchase_order_no=purchase_order_no).first()
        if not purchase_order or not purchase_order.invoice_no:
            return jsonify({
                'success': False,
                'message': '采购发票文件不存在'
            }), 404
        
        # 浠庢枃浠剁郴缁熶腑璇诲彇鏂囦欢
        invoice_folder = os.path.join(current_app.root_path, '..', 'uploads', 'invoices')
        file_path = os.path.join(invoice_folder, purchase_order.invoice_no)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': '采购发票文件不存在'
            }), 404
        
        # 杩斿洖PDF鏂囦欢
        return Response(
            open(file_path, 'rb').read(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'inline; filename={purchase_order.invoice_no}'
            }
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取采购发票文件失败: {str(e)}'
        }), 500

@bp.route('/visiray/purchase-orders/<string:purchase_order_no>/invoice', methods=['DELETE'])
@jwt_required(optional=True)
def delete_visiray_purchase_invoice(purchase_order_no):
    try:
        user = _get_request_user()
        if not user or not user.is_active:
            return jsonify({'success': False, 'message': '用户无效'}), 401
        if not (user.has_role('admin') or user.has_permission('purchase_attachment_delete')):
            return jsonify({'success': False, 'message': '权限不足'}), 403
        purchase_order = VisirayPurchaseReceivingVoucher.query.filter_by(purchase_order_no=purchase_order_no).first()
        if not purchase_order or not purchase_order.invoice_no:
            return jsonify({'success': False, 'message': '采购发票文件不存在'}), 404
        invoice_folder = os.path.join(current_app.root_path, '..', 'uploads', 'invoices')
        file_path = os.path.join(invoice_folder, purchase_order.invoice_no)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        purchase_order.invoice_no = None
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除采购发票失败: {str(e)}'}), 500

@bp.route('/visiray/purchase-orders/<string:purchase_order_no>/contract', methods=['GET'])
def get_visiray_purchase_contract(purchase_order_no):
    """鑾峰彇Visiray鍏ュ簱鍚堝悓PDF"""
    try:
        import os
        
        purchase_order = VisirayPurchaseReceivingVoucher.query.filter_by(purchase_order_no=purchase_order_no).first()
        if not purchase_order or not purchase_order.contract_pdf:
            return jsonify({
                'success': False,
                'message': '入库合同文件不存在'
            }), 404
        
        # 浠庢枃浠剁郴缁熶腑璇诲彇鏂囦欢
        contract_folder = os.path.join(current_app.root_path, '..', 'uploads', 'contracts')
        file_path = os.path.join(contract_folder, purchase_order.contract_pdf)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': '入库合同文件不存在'
            }), 404
        
        # 杩斿洖PDF鏂囦欢
        return Response(
            open(file_path, 'rb').read(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'inline; filename={purchase_order.contract_pdf}'
            }
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取入库合同文件失败: {str(e)}'
        }), 500

@bp.route('/visiray/purchase-orders/<string:purchase_order_no>/contract', methods=['DELETE'])
@jwt_required(optional=True)
def delete_visiray_purchase_contract(purchase_order_no):
    try:
        user = _get_request_user()
        if not user or not user.is_active:
            return jsonify({'success': False, 'message': '用户无效'}), 401
        if not (user.has_role('admin') or user.has_permission('purchase_attachment_delete')):
            return jsonify({'success': False, 'message': '权限不足'}), 403
        purchase_order = VisirayPurchaseReceivingVoucher.query.filter_by(purchase_order_no=purchase_order_no).first()
        if not purchase_order or not purchase_order.contract_pdf:
            return jsonify({'success': False, 'message': '入库合同文件不存在'}), 404
        contract_folder = os.path.join(current_app.root_path, '..', 'uploads', 'contracts')
        file_path = os.path.join(contract_folder, purchase_order.contract_pdf)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        purchase_order.contract_pdf = None
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除入库合同失败: {str(e)}'}), 500

@bp.route('/visiray/suppliers', methods=['GET'])
def get_visiray_suppliers():
    """获取供应商信息，合并正式供应商表和旧供应商信息表。"""
    try:
        keyword = (request.args.get('keyword') or '').strip()
        page = max(1, request.args.get('page', 1, type=int))
        per_page = max(1, min(request.args.get('per_page', 20, type=int), 100))
        supplier_map = {}

        supplier_query = Supplier.query.order_by(Supplier.supplier_code.asc())
        if keyword:
            search_term = f"%{keyword}%"
            supplier_query = supplier_query.filter(
                (Supplier.supplier_code.like(search_term)) |
                (Supplier.supplier_name.like(search_term)) |
                (Supplier.contact_person.like(search_term)) |
                (Supplier.phone.like(search_term)) |
                (Supplier.email.like(search_term))
            )
        for supplier in supplier_query.all():
            if not supplier.supplier_code:
                continue
            item = {
                'id': supplier.id,
                'supplier_code': supplier.supplier_code,
                'supplier_name': supplier.supplier_name,
                'phone': supplier.phone,
                'email': supplier.email,
                'address': supplier.address,
                'contact_person': supplier.contact_person,
                'position': None,
                'source': 'suppliers',
                'liaison': supplier.contact_person,
                'purchase_orders': None,
                'inbound_records': None,
                'remark': supplier.remark,
                'status': supplier.status,
                'is_active': supplier.is_active,
            }
            supplier_map[supplier.supplier_code] = item

        visiray_query = VisiraySupplierInformation.query.order_by(VisiraySupplierInformation.supplier_code.asc())
        if keyword:
            search_term = f"%{keyword}%"
            visiray_query = visiray_query.filter(
                (VisiraySupplierInformation.supplier_code.like(search_term)) |
                (VisiraySupplierInformation.supplier_name.like(search_term)) |
                (VisiraySupplierInformation.contact_person.like(search_term)) |
                (VisiraySupplierInformation.phone.like(search_term)) |
                (VisiraySupplierInformation.email.like(search_term))
            )
        for supplier in visiray_query.all():
            if supplier.supplier_code and supplier.supplier_code not in supplier_map:
                item = supplier.to_dict()
                item['source'] = 'supplier_information'
                supplier_map[supplier.supplier_code] = item

        items = list(supplier_map.values())
        total = len(items)
        start = (page - 1) * per_page
        pages = (total + per_page - 1) // per_page if total else 0

        return jsonify({
            'success': True,
            'data': {
                'items': items[start:start + per_page],
                'total': total,
                'pages': pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': page < pages,
                'has_prev': page > 1,
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取供应商信息失败: {str(e)}'
        }), 500

@bp.route('/visiray/suppliers', methods=['POST'])
def create_visiray_supplier():
    """创建供应商信息。"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        supplier_code = (data.get('supplier_code') or '').strip()
        if not supplier_code:
            return jsonify({
                'success': False,
                'message': '供应商编号不能为空'
            }), 400
        if (
            Supplier.query.filter_by(supplier_code=supplier_code).first() or
            VisiraySupplierInformation.query.filter_by(supplier_code=supplier_code).first()
        ):
            return jsonify({
                'success': False,
                'message': '供应商编号已存在'
            }), 400
        
        supplier = VisiraySupplierInformation(
            supplier_code=supplier_code,
            supplier_name=data.get('supplier_name'),
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address'),
            contact_person=data.get('contact_person'),
            position=data.get('position'),
            coordinator=data.get('coordinator'),
            purchase_voucher_ref=data.get('purchase_voucher_ref'),
            stock_in_record=data.get('stock_in_record'),
            remarks=data.get('remarks'),
            operator_name=data.get('operator_name')
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '供应商信息创建成功',
            'data': supplier.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建供应商信息失败: {str(e)}'
        }), 500


@bp.route('/visiray/supplier-price-options', methods=['GET'])
def get_supplier_price_options():
    """Options used by supplier price management."""
    try:
        part_keyword = (request.args.get('part_keyword') or '').strip()
        supplier_keyword = (request.args.get('supplier_keyword') or '').strip()

        parts = []
        try:
            part_query = VisirayPartNumber.query.order_by(VisirayPartNumber.created_at.desc())
            if part_keyword:
                search_term = f"%{part_keyword}%"
                part_query = part_query.filter(
                    (VisirayPartNumber.part_id.like(search_term)) |
                    (VisirayPartNumber.part_name.like(search_term)) |
                    (VisirayPartNumber.main_type.like(search_term)) |
                    (VisirayPartNumber.sub_type.like(search_term))
                )
            parts = part_query.limit(100).all()
        except Exception as e:
            current_app.logger.warning(f"Load part number options failed: {e}")

        supplier_map = {}
        try:
            supplier_query = Supplier.query.order_by(Supplier.supplier_code.asc())
            if supplier_keyword:
                search_term = f"%{supplier_keyword}%"
                supplier_query = supplier_query.filter(
                    (Supplier.supplier_code.like(search_term)) |
                    (Supplier.supplier_name.like(search_term))
                )
            for supplier in supplier_query.limit(100).all():
                if supplier.supplier_code:
                    supplier_map[supplier.supplier_code] = _supplier_display_dict(supplier)
        except Exception as e:
            current_app.logger.warning(f"Load standard supplier options failed: {e}")

        try:
            visiray_supplier_query = VisiraySupplierInformation.query.order_by(VisiraySupplierInformation.supplier_code.asc())
            if supplier_keyword:
                search_term = f"%{supplier_keyword}%"
                visiray_supplier_query = visiray_supplier_query.filter(
                    (VisiraySupplierInformation.supplier_code.like(search_term)) |
                    (VisiraySupplierInformation.supplier_name.like(search_term))
                )
            for supplier in visiray_supplier_query.limit(100).all():
                if supplier.supplier_code and supplier.supplier_code not in supplier_map:
                    supplier_map[supplier.supplier_code] = _visiray_supplier_display_dict(supplier)
        except Exception as e:
            current_app.logger.warning(f"Load visiray supplier options failed: {e}")

        return jsonify({
            'success': True,
            'data': {
                'parts': [
                    {
                        **part.to_dict(),
                        'versions': [
                            _version_to_dict(version)
                            for version in VisirayPartNumberVersion.query.filter_by(
                                part_id=part.part_id
                            ).order_by(
                                VisirayPartNumberVersion.is_current.desc(),
                                VisirayPartNumberVersion.version_no.desc(),
                            ).all()
                        ],
                    }
                    for part in parts
                ],
                'suppliers': list(supplier_map.values())
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取报价选项失败: {str(e)}'}), 500


@bp.route('/visiray/supplier-prices', methods=['GET'])
def get_supplier_prices():
    """List supplier prices for BOM costing."""
    try:
        query = (
            MaterialSupplier.query
            .join(Material, MaterialSupplier.material_id == Material.id)
            .join(Supplier, MaterialSupplier.supplier_id == Supplier.id)
        )

        keyword = (request.args.get('keyword') or '').strip()
        if keyword:
            search_term = f"%{keyword}%"
            query = query.filter(or_(
                Material.visiray_part_id.like(search_term),
                Material.material_code.like(search_term),
                Material.material_name.like(search_term),
                Supplier.supplier_code.like(search_term),
                Supplier.supplier_name.like(search_term),
                MaterialSupplier.supplier_part_no.like(search_term),
            ))

        status = (request.args.get('status') or '').strip()
        if status:
            query = query.filter(MaterialSupplier.status == status)

        part_id = (request.args.get('part_id') or '').strip()
        if part_id:
            query = query.filter(Material.visiray_part_id == part_id)

        query = query.order_by(MaterialSupplier.updated_at.desc(), MaterialSupplier.id.desc())
        result = paginate_query(query)
        result['items'] = [_supplier_price_to_dict(item) for item in result['items']]
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取供应商报价失败: {str(e)}'}), 500


@bp.route('/visiray/supplier-prices', methods=['POST'])
def create_supplier_price():
    """Create supplier price for a part number."""
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401

        data = request.get_json() or {}
        part_id = (data.get('part_id') or '').strip()
        supplier_code = (data.get('supplier_code') or '').strip()
        if not part_id:
            return jsonify({'success': False, 'message': '请选择零件号'}), 400
        if not supplier_code:
            return jsonify({'success': False, 'message': '请选择供应商'}), 400
        if data.get('price') in (None, ''):
            return jsonify({'success': False, 'message': '请输入价格'}), 400

        price = _to_float(data.get('price'))
        if price < 0:
            return jsonify({'success': False, 'message': '价格不能小于0'}), 400

        material, _part = _ensure_material_for_quote(part_id, getattr(user, 'id', None))
        supplier = _ensure_supplier_for_quote(supplier_code, getattr(user, 'id', None))

        part_version_id = _resolve_part_version_id(
            data.get('part_version_id'),
            part_id=part_id,
            require_active=True,
        )
        exists = MaterialSupplier.query.filter(
            MaterialSupplier.material_id == material.id,
            MaterialSupplier.supplier_id == supplier.id,
            MaterialSupplier.part_version_id == part_version_id
            if part_version_id is not None
            else MaterialSupplier.part_version_id.is_(None),
        ).first()
        if exists:
            return jsonify({'success': False, 'message': '该零件、版本和供应商已经存在报价，请直接编辑原报价'}), 400

        is_primary = bool(data.get('is_primary'))
        if is_primary:
            primary_query = MaterialSupplier.query.filter_by(material_id=material.id, is_primary=True)
            primary_query = primary_query.filter(
                MaterialSupplier.part_version_id == part_version_id
                if part_version_id is not None
                else MaterialSupplier.part_version_id.is_(None)
            )
            primary_query.update({'is_primary': False}, synchronize_session=False)

        item = MaterialSupplier(
            material_id=material.id,
            supplier_id=supplier.id,
            part_version_id=part_version_id,
            price=price,
            currency=data.get('currency') or 'CNY',
            price_date=_parse_date_value(data.get('price_date')) or datetime.utcnow(),
            valid_from=_parse_date_value(data.get('valid_from')),
            valid_to=_parse_date_value(data.get('valid_to')),
            is_primary=is_primary,
            lead_time=_int_or_none(data.get('lead_time')),
            min_order_qty=_to_float(data.get('min_order_qty')) if data.get('min_order_qty') not in (None, '') else None,
            supplier_part_no=data.get('supplier_part_no'),
            status=data.get('status') or 'active',
            remark=data.get('remark'),
        )
        db.session.add(item)
        db.session.flush()
        BOMService.recalculate_boms_for_material(
            material.id,
            selected_supplier_id=item.id,
        )
        db.session.commit()
        return jsonify({'success': True, 'message': '供应商报价创建成功', 'data': _supplier_price_to_dict(item)}), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建供应商报价失败: {str(e)}'}), 500


@bp.route('/visiray/supplier-prices/<int:price_id>', methods=['PUT'])
def update_supplier_price(price_id):
    """Update supplier price for a part number."""
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401

        item = MaterialSupplier.query.get(price_id)
        if not item:
            return jsonify({'success': False, 'message': '供应商报价不存在'}), 404

        original_material_id = item.material_id
        data = request.get_json() or {}
        target_part_id = data.get('part_id') or (item.material.visiray_part_id if item.material else None)
        if data.get('part_id'):
            material, _part = _ensure_material_for_quote(data.get('part_id'), getattr(user, 'id', None))
            item.material_id = material.id
        if data.get('supplier_code'):
            supplier = _ensure_supplier_for_quote(data.get('supplier_code'), getattr(user, 'id', None))
            item.supplier_id = supplier.id
        if 'part_version_id' in data:
            item.part_version_id = _resolve_part_version_id(
                data.get('part_version_id'),
                part_id=target_part_id,
                require_active=True,
            )

        exists = (
            MaterialSupplier.query
            .filter(
                MaterialSupplier.material_id == item.material_id,
                MaterialSupplier.supplier_id == item.supplier_id,
                (
                    MaterialSupplier.part_version_id == item.part_version_id
                    if item.part_version_id is not None
                    else MaterialSupplier.part_version_id.is_(None)
                ),
                MaterialSupplier.id != item.id
            )
            .first()
        )
        if exists:
            return jsonify({'success': False, 'message': '该零件、版本和供应商已经存在其他报价'}), 400

        if data.get('price') not in (None, ''):
            price = _to_float(data.get('price'))
            if price < 0:
                return jsonify({'success': False, 'message': '价格不能小于0'}), 400
            item.price = price
        if 'currency' in data:
            item.currency = data.get('currency') or 'CNY'
        if 'price_date' in data:
            item.price_date = _parse_date_value(data.get('price_date')) or datetime.utcnow()
        if 'valid_from' in data:
            item.valid_from = _parse_date_value(data.get('valid_from'))
        if 'valid_to' in data:
            item.valid_to = _parse_date_value(data.get('valid_to'))
        if 'lead_time' in data:
            item.lead_time = _int_or_none(data.get('lead_time'))
        if 'min_order_qty' in data:
            item.min_order_qty = _to_float(data.get('min_order_qty')) if data.get('min_order_qty') not in (None, '') else None
        for field in ['supplier_part_no', 'status', 'remark']:
            if field in data:
                setattr(item, field, data.get(field))
        if 'is_primary' in data:
            item.is_primary = bool(data.get('is_primary'))
            if item.is_primary:
                MaterialSupplier.query.filter(
                    MaterialSupplier.material_id == item.material_id,
                    (
                        MaterialSupplier.part_version_id == item.part_version_id
                        if item.part_version_id is not None
                        else MaterialSupplier.part_version_id.is_(None)
                    ),
                    MaterialSupplier.id != item.id
                ).update({'is_primary': False}, synchronize_session=False)

        db.session.flush()
        BOMService.recalculate_boms_for_material(
            original_material_id,
            selected_supplier_id=item.id,
        )
        if item.material_id != original_material_id:
            BOMService.recalculate_boms_for_material(
                item.material_id,
                selected_supplier_id=item.id,
            )
        db.session.commit()
        return jsonify({'success': True, 'message': '供应商报价更新成功', 'data': _supplier_price_to_dict(item)})
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新供应商报价失败: {str(e)}'}), 500


@bp.route('/visiray/supplier-prices/<int:price_id>', methods=['DELETE'])
def delete_supplier_price(price_id):
    """Disable supplier price to avoid breaking BOM history."""
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401

        item = MaterialSupplier.query.get(price_id)
        if not item:
            return jsonify({'success': False, 'message': '供应商报价不存在'}), 404
        material_id = item.material_id
        item.status = 'inactive'
        item.is_primary = False
        db.session.flush()
        BOMService.recalculate_boms_for_material(material_id)
        db.session.commit()
        return jsonify({'success': True, 'message': '供应商报价已停用'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'停用供应商报价失败: {str(e)}'}), 500


@bp.route('/visiray/dashboard/stats', methods=['GET'])
def get_visiray_dashboard_stats():
    """鑾峰彇Visiray浠〃鐩樼粺璁℃暟鎹?"""
    try:
        # 鑾峰彇搴撳瓨缁熻鏁版嵁
        total_inventory_items = VisirayInventory.query.count()
        total_inventory_value = db.session.query(db.func.sum(VisirayInventory.stock_quantity)).scalar() or 0
        
        # 鑾峰彇鍏ュ簱璁板綍缁熻鏁版嵁
        total_inbound_records = VisirayStockInRecord.query.count()
        
        # 鑾峰彇鍑哄簱璁板綍缁熻鏁版嵁
        total_outbound_records = VisirayStockOutRecord.query.count()
        
        # 鑾峰彇閲囪喘鍏ュ簱鍗曠粺璁℃暟鎹?
        total_purchase_orders = VisirayPurchaseReceivingVoucher.query.count()
        
        # 鑾峰彇渚涘簲鍟嗕俊鎭粺璁℃暟鎹?
        total_suppliers = VisiraySupplierInformation.query.count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_inventory_items': total_inventory_items,
                'total_inventory_value': int(total_inventory_value),
                'total_inbound_records': total_inbound_records,
                'total_outbound_records': total_outbound_records,
                'total_purchase_orders': total_purchase_orders,
                'total_suppliers': total_suppliers
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取仪表盘统计数据失败: {str(e)}'
        }), 500


@bp.route('/visiray/dashboard/inventory/top-items', methods=['GET'])
def get_visiray_top_inventory_items():
    """鑾峰彇搴撳瓨鏈€澶氱殑鍓?0涓揣鍝?"""
    try:
        # 鑾峰彇搴撳瓨鏁伴噺鏈€澶氱殑鍓?0涓揣鍝?
        top_items = db.session.query(
            VisirayInventory.goods_name,
            VisirayInventory.stock_quantity
        ).order_by(VisirayInventory.stock_quantity.desc()).limit(10).all()
        
        result = [{'goods_name': item[0], 'stock_quantity': item[1] or 0} for item in top_items]
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取库存统计失败: {str(e)}'
        }), 500


@bp.route('/visiray/dashboard/purchase/stats', methods=['GET'])
def get_visiray_purchase_stats():
    """鑾峰彇閲囪喘缁熻鏁版嵁"""
    try:
        # 鑾峰彇閲囪喘鍏ュ簱鍗曟€绘暟
        total_purchase_orders = VisirayPurchaseReceivingVoucher.query.count()
        
        # 鑾峰彇涓嶅悓鐘舵€佺殑閲囪喘鍗曟暟閲?
        status_stats = {}
        statuses = db.session.query(VisirayPurchaseReceivingVoucher.status).distinct().all()
        for status in statuses:
            if status[0]:  # 纭繚鐘舵€佷笉涓虹┖
                count = VisirayPurchaseReceivingVoucher.query.filter_by(status=status[0]).count()
                status_stats[status[0]] = count
        
        return jsonify({
            'success': True,
            'data': {
                'total_purchase_orders': total_purchase_orders,
                'status_stats': status_stats
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取采购统计数据失败: {str(e)}'
        }), 500


@bp.route('/visiray/dashboard/supplier/stats', methods=['GET'])
def get_visiray_supplier_stats():
    """鑾峰彇渚涘簲鍟嗙粺璁℃暟鎹?"""
    try:
        # 鑾峰彇渚涘簲鍟嗘€绘暟
        total_suppliers = VisiraySupplierInformation.query.count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_suppliers': total_suppliers
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取供应商统计数据失败: {str(e)}'
        }), 500


# 娣诲姞涓€涓柊鐨勬暟鎹粨鏋勬潵瀛樺偍宸茬敓鎴愮殑闆朵欢鍙凤紙鐙珛浜庡簱瀛樼鐞嗭級
generated_part_numbers = set()

@bp.route('/visiray/part-number-rules', methods=['GET'])
def get_part_number_rules():
    """List configurable part number rules."""
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401
        rules = PartNumberRuleService.list_rules()
        db.session.commit()
        return jsonify({
            'success': True,
            'data': [rule.to_dict() for rule in rules]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'获取零件号规则失败: {str(e)}'
        }), 500

@bp.route('/visiray/part-number-rules/active', methods=['GET'])
def get_active_part_number_rule():
    """Get active configurable part number rule."""
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401
        rule = PartNumberRuleService.get_active_rule()
        db.session.commit()
        return jsonify({
            'success': True,
            'data': rule.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'获取当前零件号规则失败: {str(e)}'
        }), 500

@bp.route('/visiray/part-number-rules/default-config', methods=['GET'])
def get_default_part_number_rule_config():
    """Get the built-in default part number rule config."""
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401
        return jsonify({
            'success': True,
            'data': PartNumberRuleService.default_config()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取默认规则失败: {str(e)}'
        }), 500

@bp.route('/visiray/part-number-rules', methods=['POST'])
def create_part_number_rule():
    """Create a configurable part number rule."""
    try:
        user, error = _require_admin()
        if error:
            return error
        data = request.get_json() or {}
        rule = PartNumberRuleService.create_rule(data, getattr(user, 'id', None))
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '零件号规则创建成功',
            'data': rule.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建零件号规则失败: {str(e)}'
        }), 400

@bp.route('/visiray/part-number-rules/<int:rule_id>', methods=['PUT'])
def update_part_number_rule(rule_id):
    """Update a configurable part number rule."""
    try:
        user, error = _require_admin()
        if error:
            return error
        data = request.get_json() or {}
        rule = PartNumberRuleService.update_rule(rule_id, data, getattr(user, 'id', None))
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '零件号规则更新成功',
            'data': rule.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新零件号规则失败: {str(e)}'
        }), 400

@bp.route('/visiray/part-number-rules/<int:rule_id>/activate', methods=['POST'])
def activate_part_number_rule(rule_id):
    """Activate a configurable part number rule."""
    try:
        user, error = _require_admin()
        if error:
            return error
        rule = PartNumberRuleService.activate_rule(rule_id, getattr(user, 'id', None))
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '零件号规则已启用',
            'data': rule.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'启用零件号规则失败: {str(e)}'
        }), 400

@bp.route('/visiray/part-number-rules/<int:rule_id>', methods=['DELETE'])
def delete_part_number_rule(rule_id):
    """Delete an inactive part number rule."""
    try:
        user, error = _require_admin()
        if error:
            return error
        rule = VisirayPartNumberRule.query.get(rule_id)
        if not rule:
            return jsonify({'success': False, 'message': '规则不存在'}), 404
        if rule.is_active:
            return jsonify({'success': False, 'message': '当前启用的规则不能删除'}), 400
        db.session.delete(rule)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '零件号规则已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除零件号规则失败: {str(e)}'
        }), 400

def generate_part_number(part_category_code, main_category_code, sub_category_index=0):
    """鐢熸垚闆朵欢鍙?
    
    缂栫爜瑙勫垯锛?
    - 闆堕儴浠剁被鍒紪鐮侊細瀹氬埗浠讹細0-4 澶栬喘浠讹細5-9
    - 澶х被缂栫爜锛氬厜瀛︿欢锛?0-19 鏈烘浠讹細20-39 鐢垫皵/瀛愪欢锛?0-59 杞欢锛?0-69 鍖栧鍝侊細70-79 鍏朵粬锛?0-99
    - 灏忕被缂栫爜锛氭寜绱㈠紩鍒嗛厤鑼冨洿 0000-0009, 0010-0019, ..., 0090-0099
    - 浜у搧缂栧彿锛?000-9999
    - 鐗堟湰鍙凤細01锛堥粯璁わ級
    - 鎬诲叡11浣嶏細闆堕儴浠剁被鍒?1浣? + 澶х被(2浣? + 灏忕被(2浣? + 浜у搧缂栧彿(4浣? + 鐗堟湰鍙?2浣?
    
    鐢熸垚閫昏緫锛?
    1. 浠庝骇鍝佺紪鍙?000寮€濮嬶紝姣忔鐐瑰嚮鍔犱竴
    2. 濡傛灉浜у搧缂栧彿杈惧埌9999锛屽氨澧炲姞灏忕被缂栫爜
    3. 濡傛灉灏忕被缂栫爜瓒呭嚭褰撳墠鑼冨洿锛屽氨澧炲姞灏忕被绱㈠紩锛堝嵆杩涘叆涓嬩竴涓寖鍥达級
    4. 濡傛灉灏忕被绱㈠紩瓒呭嚭鑼冨洿锛?-9锛夛紝灏卞姞澶х被鐨勬暟瀛?
    5. 澶х被缂栫爜鍒版瀬闄愪簡灏卞姞闆堕儴浠剁被鍒殑鏁板瓧
    6. 闆朵欢鍙风敵璇峰姛鑳戒笌搴撳瓨绠＄悊琛ㄧ嫭绔?
    """
    try:
        # 浣跨敤鐙珛鐨勫瓨鍌ㄦ潵璺熻釜宸茬敓鎴愮殑闆朵欢鍙?
        global generated_part_numbers
        
        # 鏍规嵁灏忕被绱㈠紩璁＄畻灏忕被缂栫爜鑼冨洿鐨勮捣濮嬪€?(0, 10, 20, ..., 90)
        sub_category_start = sub_category_index * 10
        # 浠庝骇鍝佺紪鍙?000寮€濮嬪皾璇曠敓鎴?
        product_number = 0
        # 鐗堟湰鍙烽粯璁や负01
        version_number = 1
        # 褰撳墠灏忕被缂栫爜浠庤寖鍥磋捣濮嬪€煎紑濮?
        sub_category_code = sub_category_start
        
        # 灏濊瘯鐢熸垚闆朵欢鍙凤紝鐩村埌鎵惧埌涓€涓湭琚娇鐢ㄧ殑缂栧彿
        while True:
            # 鏍煎紡鍖栦负11浣嶆暟瀛楋細闆堕儴浠剁被鍒?1浣? + 澶х被(2浣? + 灏忕被(2浣? + 浜у搧缂栧彿(4浣? + 鐗堟湰鍙?2浣?
            part_digits = f"{part_category_code}{main_category_code:02d}{sub_category_code:02d}{product_number:04d}{version_number:02d}"
            
            # xyh modi
            #part_number = f"VISB{part_digits}"
            part_number = f"{PN_HEAD}{part_digits}"
            
            # 妫€鏌ョ敓鎴愮殑闆朵欢鍙锋槸鍚﹀凡瀛樺湪
            exists_in_set = part_number in generated_part_numbers
            exists_in_db = VisirayPartNumber.query.get(part_number) is not None
            if not exists_in_set and not exists_in_db:
                # 妫€鏌ユ槸鍚﹀湪姝ｇ‘鐨勭紪鐮佽寖鍥村唴
                if is_valid_part_number(part_number, part_category_code, main_category_code):
                    # 灏嗘柊鐢熸垚鐨勯浂浠跺彿娣诲姞鍒伴泦鍚堜腑
                    generated_part_numbers.add(part_number)
                    return part_number
            
            # 濡傛灉褰撳墠浜у搧缂栧彿宸蹭娇鐢紝灏濊瘯涓嬩竴涓骇鍝佺紪鍙?
            product_number += 1
            
            # 濡傛灉浜у搧缂栧彿瓒呭嚭鑼冨洿锛屽鍔犲皬绫荤紪鐮?
            if product_number > 9999:
                product_number = 0
                sub_category_code += 1
                
                # 妫€鏌ユ槸鍚﹁秴鍑哄綋鍓嶅皬绫昏寖鍥?
                if sub_category_code >= sub_category_start + 10:
                    # 瓒呭嚭褰撳墠灏忕被鑼冨洿锛屽鍔犲皬绫荤储寮?
                    sub_category_index += 1
                    
                    # 濡傛灉灏忕被绱㈠紩瓒呭嚭鑼冨洿锛?-9锛夛紝澧炲姞澶х被缂栫爜
                    if sub_category_index > 9:
                        sub_category_index = 0
                        main_category_code += 1
                        
                        # 妫€鏌ュぇ绫荤紪鐮佹槸鍚﹁秴鍑鸿寖鍥?
                        if not is_main_category_code_valid(main_category_code):
                            main_category_code = get_main_category_start_code(main_category_code)
                            part_category_code += 1
                            
                            # 妫€鏌ラ浂閮ㄤ欢绫诲埆缂栫爜鏄惁瓒呭嚭鑼冨洿
                            if part_category_code > 9:
                                raise Exception('鏃犳硶鐢熸垚鏂扮殑闆朵欢鍙凤細鎵€鏈夌紪鐮佽寖鍥村凡鐢ㄥ畬')
                    
                    # 閲嶆柊璁＄畻灏忕被缂栫爜鑼冨洿鐨勮捣濮嬪€?
                    sub_category_start = sub_category_index * 10
                    sub_category_code = sub_category_start
        
    except Exception as e:
        # 濡傛灉鍑虹幇寮傚父锛岃繑鍥炰竴涓粯璁ょ殑闆朵欢鍙?
        default_digits = f"{part_category_code}{main_category_code:02d}{(sub_category_index * 10):02d}0000{1:02d}"
        
        # xyh modi
        #default_number = f"VISB{default_digits}"
        default_number = f"{PN_HEAD}{default_digits}"
        
        generated_part_numbers.add(default_number)
        return default_number

def is_valid_part_number(part_number, part_category_code, main_category_code):
    """妫€鏌ラ浂浠跺彿鏄惁鍦ㄦ纭殑缂栫爜鑼冨洿鍐?"""
    try:
        # xyh modi
        #digits = part_number[4:] if part_number.startswith('VISB') else part_number
        digits = part_number[4:] if part_number.startswith(PN_HEAD) else part_number

        if len(digits) != 11:
            return False
            
        # 妫€鏌ラ浂閮ㄤ欢绫诲埆缂栫爜
        part_category_digit = int(digits[0])
        if part_category_digit != part_category_code:
            return False
            
        # 妫€鏌ュぇ绫荤紪鐮?
        main_category_digits = int(digits[1:3])
        if not is_main_category_in_range(main_category_digits, main_category_code):
            return False
            
        return True
    except:
        return False

def is_main_category_in_range(main_category_digits, main_category_code):
    """妫€鏌ュぇ绫荤紪鐮佹槸鍚﹀湪姝ｇ‘鐨勮寖鍥村唴"""
    # 澶х被缂栫爜瑙勫垯锛氬厜瀛︿欢锛?0-19 鏈烘浠讹細20-39 鐢垫皵/瀛愪欢锛?0-59 杞欢锛?0-69 鍖栧鍝侊細70-79 鍏朵粬锛?0-99
    ranges = {
        0: (0, 19),    # 鍏夊浠?
        20: (20, 39),  # 鏈烘浠?
        40: (40, 59),  # 鐢垫皵/瀛愪欢
        60: (60, 69),  # 杞欢
        70: (70, 79),  # 鍖栧鍝?
        80: (80, 99)   # 鍏朵粬
    }
    
    # 鎵惧埌瀵瑰簲鐨勫ぇ绫昏寖鍥?
    for start, (range_start, range_end) in ranges.items():
        if main_category_code >= range_start and main_category_code <= range_end:
            return main_category_digits >= range_start and main_category_digits <= range_end
    
    return False

def is_main_category_code_valid(main_category_code):
    """妫€鏌ュぇ绫荤紪鐮佹槸鍚︽湁鏁?"""
    # 澶х被缂栫爜瑙勫垯锛氬厜瀛︿欢锛?0-19 鏈烘浠讹細20-39 鐢垫皵/瀛愪欢锛?0-59 杞欢锛?0-69 鍖栧鍝侊細70-79 鍏朵粬锛?0-99
    valid_ranges = [
        (0, 19),    # 鍏夊浠?
        (20, 39),   # 鏈烘浠?
        (40, 59),   # 鐢垫皵/瀛愪欢
        (60, 69),   # 杞欢
        (70, 79),   # 鍖栧鍝?
        (80, 99)    # 鍏朵粬
    ]
    
    for range_start, range_end in valid_ranges:
        if main_category_code >= range_start and main_category_code <= range_end:
            return True
    
    return False

def get_main_category_start_code(main_category_code):
    """鑾峰彇澶х被缂栫爜鐨勮捣濮嬪€?"""
    # 澶х被缂栫爜瑙勫垯锛氬厜瀛︿欢锛?0-19 鏈烘浠讹細20-39 鐢垫皵/瀛愪欢锛?0-59 杞欢锛?0-69 鍖栧鍝侊細70-79 鍏朵粬锛?0-99
    ranges = [
        (0, 19),    # 鍏夊浠?
        (20, 39),   # 鏈烘浠?
        (40, 59),   # 鐢垫皵/瀛愪欢
        (60, 69),   # 杞欢
        (70, 79),   # 鍖栧鍝?
        (80, 99)    # 鍏朵粬
    ]
    
    for range_start, range_end in ranges:
        if main_category_code >= range_start and main_category_code <= range_end:
            return range_start
    
    return 80

@bp.route('/visiray/part-number/apply', methods=['POST'])
def apply_part_number():
    """鐢宠闆朵欢鍙?"""
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 闆堕儴浠剁被鍒?(custom: 瀹氬埗浠? purchased: 澶栬喘浠?
        part_category = data.get('partCategory')
        # 澶х被
        main_category = data.get('mainCategory')
        # 灏忕被
        sub_category = data.get('subCategory')
        # 闆朵欢鍚嶇О
        part_name = (data.get('partName') or data.get('part_name') or '').strip()
        unit = data.get('unit') or 'pcs'
        standard_cost = _to_float(data.get('standard_cost', data.get('standardCost', 0)))
        # 闆朵欢鎻忚堪
        part_description = data.get('partDescription')
        # 渚涘簲鍟?
        supplier = data.get('supplier')
        # 鏉愭枡
        material = data.get('material')
        # 瑙勬牸
        specification = data.get('specification')
        
        # 楠岃瘉蹇呭～瀛楁
        if not part_category or not main_category:
            return jsonify({
                'success': False,
                'message': '零部件类别和大类为必填项'
            }), 400
        if not part_name:
            return jsonify({
                'success': False,
                'message': '零件名称不能为空'
            }), 400
        
        # 旧版固定编码计算已移除。零件号生成只使用当前启用的零件号规则配置。
        # partCategory / mainCategory / subCategory 作为规则输入，由 PartNumberRuleService 解析。        # 鐢熸垚闆朵欢鍙凤紙涓庡簱瀛樼鐞嗚〃鐙珛锛夛紝瑙勫垯鏉ヨ嚜褰撳墠鍚敤鐨勯浂浠跺彿瑙勫垯閰嶇疆
        part_number = PartNumberRuleService.generate_part_number(data, generated_part_numbers)
        generated_part_numbers.add(part_number)
        
        # 闆朵欢鍙风敵璇峰姛鑳戒笌搴撳瓨绠＄悊琛ㄧ嫭绔嬶紝涓嶄繚瀛樺埌搴撳瓨绠＄悊涓?
        
        # 淇濆瓨闆朵欢鍙峰埌鏁版嵁搴?
        part_number_record = VisirayPartNumber(
            part_id=part_number,
            category=part_category,
            main_type=main_category,
            sub_type=sub_category,
            part_name=(part_name or None),
            unit=unit,
            standard_cost=standard_cost,
            created_by=(getattr(user, 'id', None) if user else None),
            created_by_name=((getattr(user, 'name', None) or getattr(user, 'username', None) or getattr(user, 'email', None)) if user else None)
        )
        
        db.session.add(part_number_record)
        db.session.flush()
        synced_material = _sync_material_from_part_number(part_number_record, getattr(user, 'id', None) if user else None)
        db.session.commit()
        current_app.logger.info(
            "part_number_apply_saved part_id=%s standard_cost=%s material_id=%s material_standard_cost=%s",
            part_number_record.part_id,
            part_number_record.standard_cost,
            getattr(synced_material, 'id', None),
            getattr(synced_material, 'standard_cost', None),
        )
        
        # 杩斿洖鐢熸垚鐨勯浂浠跺彿
        return jsonify({
            'success': True,
            'message': '零件号申请成功',
            'data': {
                'part_number': part_number,
                'part_category': part_category,
                'main_category': main_category,
                'sub_category': sub_category,
                'part_name': part_name,
                'unit': unit,
                'standard_cost': float(part_number_record.standard_cost or 0),
                'material_id': getattr(synced_material, 'id', None),
                'material_standard_cost': float(getattr(synced_material, 'standard_cost', 0) or 0),
                'part_description': part_description,
                'supplier': supplier,
                'material': material,
                'specification': specification
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'零件号申请失败: {str(e)}'
        }), 500

@bp.route('/visiray/part-number/<path:part_id>/versions', methods=['GET'])
def get_part_number_versions(part_id):
    try:
        part = _find_part_number(part_id)
        if not part:
            return jsonify({'success': False, 'message': '零件号不存在'}), 404
        versions = (
            VisirayPartNumberVersion.query
            .filter_by(part_id=part.part_id)
            .order_by(VisirayPartNumberVersion.is_current.desc(), VisirayPartNumberVersion.version_no.desc())
            .all()
        )
        return jsonify({
            'success': True,
            'data': {
                'part': part.to_dict(),
                'items': [_version_to_dict(version) for version in versions],
            },
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取零件版本失败: {str(e)}'}), 500

@bp.route('/visiray/part-number/<path:part_id>/versions', methods=['POST'])
@jwt_required(optional=True)
def create_part_number_version(part_id):
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401
        part = _find_part_number(part_id)
        if not part:
            return jsonify({'success': False, 'message': '零件号不存在'}), 404

        data = request.get_json(silent=True) or {}
        version_no = _validate_version_no(data.get('version_no', data.get('version_number')))
        if VisirayPartNumberVersion.query.filter_by(part_id=part.part_id, version_no=version_no).first():
            return jsonify({'success': False, 'message': '该零件号下版本号已存在'}), 400

        auto_current = data.get('auto_current', True) is not False
        record = VisirayPartNumberVersion(
            part_id=part.part_id,
            version_no=version_no,
            status='active',
            is_current=False,
            remark=data.get('remark'),
            created_by=getattr(user, 'id', None),
            created_by_name=getattr(user, 'name', None) or getattr(user, 'username', None),
        )
        db.session.add(record)
        db.session.flush()

        if auto_current:
            VisirayPartNumberVersion.query.filter(
                VisirayPartNumberVersion.part_id == part.part_id,
                VisirayPartNumberVersion.id != record.id,
            ).update({'is_current': False}, synchronize_session=False)
            record.is_current = True
            part.current_version_id = record.id

        db.session.commit()
        return jsonify({'success': True, 'message': '零件版本创建成功', 'data': _version_to_dict(record)}), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建零件版本失败: {str(e)}'}), 500

@bp.route('/visiray/part-number-versions/<int:version_id>', methods=['PATCH'])
@jwt_required(optional=True)
def update_part_number_version(version_id):
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401
        version = VisirayPartNumberVersion.query.get(version_id)
        if not version:
            return jsonify({'success': False, 'message': '零件版本不存在'}), 404
        data = request.get_json(silent=True) or {}
        if 'version_no' in data or 'version_number' in data:
            version_no = _validate_version_no(data.get('version_no', data.get('version_number')))
            duplicate = VisirayPartNumberVersion.query.filter(
                VisirayPartNumberVersion.part_id == version.part_id,
                VisirayPartNumberVersion.version_no == version_no,
                VisirayPartNumberVersion.id != version.id,
            ).first()
            if duplicate:
                return jsonify({'success': False, 'message': '该零件号下版本号已存在'}), 400
            version.version_no = version_no
        if 'remark' in data:
            version.remark = data.get('remark')
        db.session.commit()
        return jsonify({'success': True, 'message': '零件版本更新成功', 'data': _version_to_dict(version)})
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新零件版本失败: {str(e)}'}), 500

@bp.route('/visiray/part-number-versions/<int:version_id>/set-current', methods=['POST'])
@jwt_required(optional=True)
def set_current_part_number_version(version_id):
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401
        version = VisirayPartNumberVersion.query.get(version_id)
        if not version:
            return jsonify({'success': False, 'message': '零件版本不存在'}), 404
        if (version.status or 'active') != 'active':
            return jsonify({'success': False, 'message': '废弃版本不能设为当前版本'}), 400
        part = VisirayPartNumber.query.get(version.part_id)
        VisirayPartNumberVersion.query.filter_by(part_id=version.part_id).update(
            {'is_current': False}, synchronize_session=False
        )
        version.is_current = True
        if part:
            part.current_version_id = version.id
        db.session.commit()
        return jsonify({'success': True, 'message': '当前版本已更新', 'data': _version_to_dict(version)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'设置当前版本失败: {str(e)}'}), 500

@bp.route('/visiray/part-number-versions/<int:version_id>/obsolete', methods=['POST'])
@jwt_required(optional=True)
def obsolete_part_number_version(version_id):
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401
        version = VisirayPartNumberVersion.query.get(version_id)
        if not version:
            return jsonify({'success': False, 'message': '零件版本不存在'}), 404
        if version.is_current:
            return jsonify({'success': False, 'message': '当前版本不能直接废弃，请先切换当前版本'}), 400
        version.status = 'obsolete'
        version.is_current = False
        db.session.commit()
        return jsonify({'success': True, 'message': '零件版本已废弃', 'data': _version_to_dict(version)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'废弃零件版本失败: {str(e)}'}), 500

@bp.route('/visiray/part-number/<path:part_id>/next-version', methods=['POST'])
@jwt_required(optional=True)
def create_part_number_next_version(part_id):
    """兼容旧调用：现在在同一零件号下创建手工版本。"""
    return create_part_number_version(part_id)

@bp.route('/visiray/part-numbers', methods=['GET'])
def get_part_numbers():
    """鑾峰彇鎵€鏈夐浂浠跺彿鍒楄〃"""
    try:
        user = _get_request_user()
        query = VisirayPartNumber.query.order_by(VisirayPartNumber.created_at.desc())
        
        # 鎼滅储鏉′欢
        keyword = request.args.get('keyword')
        if keyword:
            search_term = f"%{keyword}%"
            query = query.filter(
                (VisirayPartNumber.part_id.like(search_term)) |
                (VisirayPartNumber.part_name.like(search_term)) |
                (VisirayPartNumber.category.like(search_term)) |
                (VisirayPartNumber.main_type.like(search_term)) |
                (VisirayPartNumber.sub_type.like(search_term))
            )
        
        # 零件版本管理需要一次加载全部零件，供前端按零件号、名称和版本号本地搜索。
        # 其他调用仍使用通用分页函数，避免改变其他列表接口的分页限制。
        load_all = request.args.get('all') == '1'
        if load_all:
            page_items = query.all()
            total = len(page_items)
            result = {
                'items': page_items,
                'total': total,
                'pages': 1 if total else 0,
                'current_page': 1,
                'per_page': total,
                'has_prev': False,
                'has_next': False,
                'prev_num': None,
                'next_num': None,
            }
        else:
            result = paginate_query(query)
        items = []
        name_cache = {}
        include_suppliers = request.args.get('include_suppliers') == '1'
        page_items = result['items']
        part_ids = [item.part_id for item in page_items]
        versions_by_part_id = {part_id: [] for part_id in part_ids}
        if part_ids:
            versions = (
                VisirayPartNumberVersion.query
                .filter(VisirayPartNumberVersion.part_id.in_(part_ids))
                .order_by(
                    VisirayPartNumberVersion.part_id.asc(),
                    VisirayPartNumberVersion.is_current.desc(),
                    VisirayPartNumberVersion.version_no.desc(),
                )
                .all()
            )
            for version in versions:
                versions_by_part_id.setdefault(version.part_id, []).append(version)

        material_by_part_id = {}
        if include_suppliers and part_ids:
            markers = [_part_material_marker(part_id) for part_id in part_ids]
            materials = (
                Material.query
                .filter(or_(Material.visiray_part_id.in_(part_ids), Material.remark.in_(markers)))
                .all()
            )
            for material in materials:
                if material.visiray_part_id and material.visiray_part_id not in material_by_part_id:
                    material_by_part_id[material.visiray_part_id] = material
            for material in materials:
                if material.remark and material.remark.startswith('VISIRAY_PART_ID:'):
                    marker_part_id = material.remark.split(':', 1)[1]
                    material_by_part_id.setdefault(marker_part_id, material)

        for item in page_items:
            d = item.to_dict()
            item_versions = versions_by_part_id.get(item.part_id, [])
            d['versions'] = [
                _version_to_dict(version)
                for version in item_versions
            ]
            if include_suppliers:
                d.update(_supplier_payload_from_material(material_by_part_id.get(item.part_id), item, item_versions))
            can_edit = False
            if user:
                try:
                    can_edit = (getattr(user, 'id', None) == item.created_by) or getattr(user, 'has_role', lambda x: False)('admin')
                except Exception:
                    can_edit = False
            d['editable'] = can_edit
            creator_id = item.created_by
            creator_name = None
            if creator_id:
                if creator_id in name_cache:
                    creator_name = name_cache[creator_id]
                else:
                    u = None
                    try:
                        u = User.query.get(int(creator_id))
                    except Exception:
                        u = None
                    if u:
                        creator_name = u.name or u.username or u.email
                        name_cache[creator_id] = creator_name
            d['created_by_name'] = creator_name
            items.append(d)
        result['items'] = items
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取零件号列表失败: {str(e)}'
        }), 500

@bp.route('/visiray/part-number/<part_id>', methods=['PATCH'])
@jwt_required(optional=True)
def update_part_number(part_id):
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '未登录或用户无效'}), 401

        # xyh modi
        # real_id = part_id[4:] if part_id.startswith('VISB') else part_id
        real_id = part_id[4:] if part_id.startswith(PN_HEAD) else part_id

        record = VisirayPartNumber.query.get(part_id) or VisirayPartNumber.query.get(real_id)
        if not record:
            return jsonify({'success': False, 'message': '零件号不存在'}), 404

        # 鏉冮檺锛氬垱寤轰汉鎴朼dmin
        is_admin = False
        try:
            is_admin = getattr(user, 'has_role', lambda x: False)('admin')
        except Exception:
            is_admin = False
        if not is_admin and getattr(user, 'id', None) != record.created_by:
            return jsonify({'success': False, 'message': '权限不足'}), 403

        data = request.get_json(silent=True) or {}
        part_name = (data.get('part_name') or '').strip()
        if not part_name:
            return jsonify({'success': False, 'message': '零件名称不能为空'}), 400

        record.part_name = part_name
        if 'unit' in data:
            record.unit = data.get('unit') or 'pcs'
        if 'standard_cost' in data:
            record.standard_cost = _to_float(data.get('standard_cost'))
        synced_material = _sync_material_from_part_number(record, getattr(user, 'id', None))
        db.session.commit()
        data = record.to_dict()
        data['material_id'] = getattr(synced_material, 'id', None)
        data['material_standard_cost'] = float(getattr(synced_material, 'standard_cost', 0) or 0)

        return jsonify({'success': True, 'message': '更新成功', 'data': data})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500

def _clean_part_id_for_rule(value: str) -> str:
    return re.sub(r'\s+', '', str(value or '')).upper()


def _active_rule_prefix_and_config():
    rule = PartNumberRuleService.get_active_rule()
    return (rule.prefix or '').strip().upper(), rule.get_config()


def _strip_known_part_prefix_for_import(part_id: str, active_prefix: str) -> str:
    body = part_id
    if active_prefix and body.startswith(active_prefix):
        return body[len(active_prefix):]
    for prefix in LEGACY_PART_PREFIXES:
        if body.startswith(prefix):
            return body[len(prefix):]
    return body


def _segment_value_by_source(config: dict, body: str) -> dict:
    values = {}
    cursor = 0
    for segment in config.get('segments') or []:
        length = int(segment.get('length') or 0)
        source = segment.get('source')
        key = segment.get('key')
        value = body[cursor:cursor + length]
        cursor += length
        if source:
            values[source] = value
        if key:
            values[key] = value
    return values


def _category_from_rule_value(config: dict, values: dict) -> str:
    category_code = values.get('part_category_code')
    category_identifier = values.get('part_category_identifier')
    for key, item in (config.get('part_categories') or {}).items():
        if category_code and str(item.get('code')) == category_code:
            return key
        if category_identifier and str(item.get('identifier')) == category_identifier:
            return key
    return 'custom'


def _main_type_from_rule_value(config: dict, values: dict) -> str:
    main_code = values.get('main_category_code')
    for key, item in (config.get('main_categories') or {}).items():
        if main_code and str(item.get('code')) == main_code:
            return key
    try:
        code_number = int(main_code)
    except Exception:
        return 'other'
    for key, item in (config.get('main_categories') or {}).items():
        try:
            min_code = int(item.get('min'))
            max_code = int(item.get('max'))
        except Exception:
            continue
        if min_code <= code_number <= max_code:
            return key
    return 'other'


def _sub_type_from_rule_value(config: dict, category: str, main_type: str, values: dict) -> str:
    sub_code_value = str(values.get('sub_category_index') or values.get('classification') or '').zfill(2)
    for key, item in (config.get('sub_categories') or {}).items():
        if sub_code_value and str(item.get('code')).zfill(2) == sub_code_value:
            return key

    try:
        sub_index = int(sub_code_value or 0)
    except Exception:
        sub_index = 0
    orders = config.get('sub_category_orders') or {}
    for key in (main_type, f'{main_type}.{category}'):
        order = orders.get(key)
        if isinstance(order, list) and 0 <= sub_index < len(order):
            return order[sub_index]
    return _subtype_by_codes(main_type, category, sub_index)


def _part_number_classification_by_active_rule(raw_part_id: str):
    part_id = _clean_part_id_for_rule(raw_part_id)
    active_prefix, config = _active_rule_prefix_and_config()
    code_length = int(config.get('code_length') or 0)
    body = _strip_known_part_prefix_for_import(part_id, active_prefix)
    if not code_length or len(body) != code_length:
        raise ValueError('零件号长度与当前规则不一致')

    PartNumberRuleService.validate_config(config)
    values = _segment_value_by_source(config, body)
    category = _category_from_rule_value(config, values)
    main_type = _main_type_from_rule_value(config, values)
    sub_type = _sub_type_from_rule_value(config, category, main_type, values)
    normalized_part_id = f'{active_prefix}{body}' if active_prefix else body
    return normalized_part_id, category, main_type, sub_type


def _part_number_classification_by_legacy_rule(raw_part_id: str):
    part_id = _clean_part_id_for_rule(raw_part_id)
    active_prefix, _config = _active_rule_prefix_and_config()
    if active_prefix and part_id.startswith(active_prefix):
        part_id = part_id[len(active_prefix):]
    for prefix in LEGACY_PART_PREFIXES:
        if part_id.startswith(prefix):
            part_id = part_id[len(prefix):]
            break
    digits = part_id
    try:
        part_category_code = int(digits[0])
        main_category_code = int(digits[1:3])
        sub_category_code = int(digits[3:5])
    except Exception:
        raise ValueError('零件号格式错误')

    legacy_part_id_for_validation = f'{PN_HEAD}{digits}'
    if not is_valid_part_number(legacy_part_id_for_validation, part_category_code, main_category_code):
        raise ValueError('零件号不符合编码规则')

    category = 'custom' if 0 <= part_category_code <= 4 else 'purchased'
    main_type = (
        'optical' if 0 <= main_category_code <= 19 else
        'mechanical' if 20 <= main_category_code <= 39 else
        'electrical' if 40 <= main_category_code <= 59 else
        'software' if 60 <= main_category_code <= 69 else
        'chemical' if 70 <= main_category_code <= 79 else
        'other'
    )
    sub_type = _subtype_by_codes(main_type, category, sub_category_code)
    normalized_part_id = f'{active_prefix}{digits}' if active_prefix else digits
    return normalized_part_id, category, main_type, sub_type


def _part_number_classification(part_id: str):
    try:
        return _part_number_classification_by_active_rule(part_id)
    except Exception:
        return _part_number_classification_by_legacy_rule(part_id)


def _subtype_by_codes(main_type: str, category: str, sub_code: int) -> str:
    index_group = max(0, min(9, sub_code // 10))
    maps = {
        ('optical', 'purchased'): [
            'light_source', 'light_transmission', 'lens_prism', 'optical_filter',
            'optical_sensor', 'light_modulator', 'display_imaging', 'optical_other'
        ],
        ('mechanical', 'purchased'): [
            'aluminum_profile', 'transmission', 'fasteners', 'spring', 'net_filter', 'mechanical_other'
        ],
        ('mechanical', 'custom'): [
            'iron_steel', 'copper_aluminum_titanium', 'other_metal', 'plastic', 'rubber', 'glass_ceramic', 'material_other'
        ],
        ('electrical', 'purchased'): [
            'passive', 'semiconductor', 'electromechanical', 'power', 'sensor', 'electrical_other'
        ],
        ('electrical', 'custom'): [
            'custom_power', 'custom_sensor', 'wire_harness', 'drive_control', 'custom_electrical_other'
        ],
        ('software', 'purchased'): [
            'system_software', 'office_software', 'security_software', 'engineering_software', 'development_tools', 'software_other'
        ],
        ('software', 'custom'): [
            'custom_platform', 'custom_development_tools', 'custom_information_visualization', 'custom_software_other'
        ],
        ('chemical', 'purchased'): [
            'inorganic', 'organic', 'reagent', 'functional', 'material_chemical', 'hazardous', 'chemical_other'
        ],
        ('chemical', 'custom'): [
            'custom_formulation', 'custom_polymer', 'custom_coating', 'custom_functional', 'custom_material', 'custom_environmental', 'custom_chemical_other'
        ],
        ('other', 'purchased'): [],
        ('other', 'custom'): []
    }
    values = maps.get((main_type, category)) or []
    return values[index_group] if index_group < len(values) else ''


def _clean_excel_cell(value):
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _normalize_excel_header(value):
    return re.sub(r'\s+', '', _clean_excel_cell(value)).lower()


def _first_excel_value(row_data, *names):
    for name in names:
        if name in row_data and row_data[name] not in (None, ''):
            return row_data[name]
    return None


def _find_part_import_header(headers):
    normalized = [_normalize_excel_header(value) for value in headers]
    part_aliases = {'零件号', '物料号', '料号', 'partno', 'partnumber', 'part_id', 'partid'}
    name_aliases = {'零件名称', '名称', '物料名称', 'partname', 'part_name'}
    supplier_aliases = {'供应商', '供应厂商', '厂商', '厂家', '加工厂', '加工厂或采购网址', '采购网址', 'supplier', 'vendor'}
    remark_aliases = {'备注', '说明', 'remark', 'note'}
    material_aliases = {'材质', '材料', '材料类别', '规格', '规格型号', 'material', 'specification'}
    price_aliases = {'标准成本', '单价', '价格', '报价', '采购价', 'unitprice', 'price', 'standardcost'}
    if any(value in part_aliases for value in normalized) or any(value in name_aliases for value in normalized):
        return {
            'part_id': next((idx for idx, value in enumerate(normalized) if value in part_aliases), None),
            'part_name': next((idx for idx, value in enumerate(normalized) if value in name_aliases), None),
            'unit': next((idx for idx, value in enumerate(normalized) if value in {'单位', 'unit'}), None),
            'standard_cost': next((idx for idx, value in enumerate(normalized) if value in price_aliases), None),
            'supplier': next((idx for idx, value in enumerate(normalized) if value in supplier_aliases), None),
            'remark': next((idx for idx, value in enumerate(normalized) if value in remark_aliases), None),
            'material_note': next((idx for idx, value in enumerate(normalized) if value in material_aliases), None),
        }
    return None


def _normalize_part_name_key(value):
    return re.sub(r'\s+', '', _clean_excel_cell(value)).lower()


def _truncate_text(value, max_length):
    text = _clean_excel_cell(value)
    return text[:max_length] if text else None


def _parse_excel_price(value):
    if value in (None, ''):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = _clean_excel_cell(value)
    if not text:
        return None
    text = (
        text.replace(',', '')
        .replace('￥', '')
        .replace('¥', '')
        .replace('元', '')
        .replace('/个', '')
        .replace('/件', '')
        .strip()
    )
    match = re.search(r'-?\d+(?:\.\d+)?', text)
    return float(match.group(0)) if match else None


def _split_supplier_text(value):
    text = re.sub(r'\s+', ' ', _clean_excel_cell(value)).strip()
    if not text:
        return '', None, None

    url_match = re.search(r'(https?://\S+|www\.\S+)', text, re.IGNORECASE)
    if url_match:
        raw_url = url_match.group(1).rstrip('，,；;')
        parsed = urlparse(raw_url if raw_url.lower().startswith(('http://', 'https://')) else f'http://{raw_url}')
        host = parsed.netloc or parsed.path.split('/')[0]
        name = host or text
        prefix = text[:url_match.start()].strip('：:，,；; ')
        return _truncate_text(prefix or name, 128), None, _truncate_text(raw_url, 255)

    for separator in ('：', ':', '；', ';', '，', ','):
        if separator in text:
            left, right = text.split(separator, 1)
            left = left.strip()
            right = right.strip()
            if left:
                return _truncate_text(left, 128), _truncate_text(right, 64), None

    return _truncate_text(text, 128), None, None


def _generate_unique_supplier_code():
    for _ in range(50):
        code = generate_code('SUP', 6)
        if not Supplier.query.filter_by(supplier_code=code).first():
            return code
    raise ValueError('供应商编码生成失败，请重试')


def _ensure_supplier_by_name(supplier_name, created_by=None, website=None, remark=None):
    name = _truncate_text(supplier_name, 128)
    if not name:
        raise ValueError('供应商为空')

    supplier = Supplier.query.filter(or_(Supplier.supplier_name == name, Supplier.supplier_code == name)).first()
    if supplier:
        if website and not supplier.website:
            supplier.website = website
        return supplier, False

    supplier = Supplier(
        supplier_code=_generate_unique_supplier_code(),
        supplier_name=name,
        website=website,
        supplier_type='material',
        supplier_level='C',
        status='active',
        cooperation_status='cooperation',
        remark=remark,
        is_active=True,
        created_by=created_by,
    )
    db.session.add(supplier)
    db.session.flush()
    return supplier, True


def _upsert_material_supplier(material, supplier, price, supplier_part_no=None, remark=None):
    if price is None or price <= 0:
        raise ValueError('单价必须大于0')

    db.session.flush()
    existing = MaterialSupplier.query.filter_by(material_id=material.id, supplier_id=supplier.id).first()
    if existing:
        existing.price = price
        existing.currency = 'CNY'
        existing.price_date = datetime.utcnow()
        existing.status = 'active'
        if supplier_part_no:
            existing.supplier_part_no = _truncate_text(supplier_part_no, 64)
        if remark:
            existing.remark = remark
        return 'updated'

    primary_exists = MaterialSupplier.query.filter_by(
        material_id=material.id,
        is_primary=True,
        status='active'
    ).first()
    item = MaterialSupplier(
        material_id=material.id,
        supplier_id=supplier.id,
        price=price,
        currency='CNY',
        price_date=datetime.utcnow(),
        is_primary=primary_exists is None,
        supplier_part_no=_truncate_text(supplier_part_no, 64),
        remark=remark,
        status='active',
    )
    db.session.add(item)
    return 'created'


@bp.route('/visiray/part-number/import', methods=['POST'])
def import_part_number():
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401
        data = request.get_json() or {}
        part_id = (data.get('part_id') or '').strip()
        unit = data.get('unit') or 'pcs'
        standard_cost = _to_float(data.get('standard_cost', 0))
        part_name = (data.get('part_name') or '').strip() or None

        if not part_id:
            return jsonify({'success': False, 'message': '请提供零件号'}), 400

        # xyh modi
        #if not part_id.startswith('VISB'):
        #    part_id = f"VISB{part_id}"
        if not part_id.startswith(PN_HEAD):
            part_id = f"{PN_HEAD}{part_id}"

        digits = part_id[4:]
        try:
            part_category_code = int(digits[0])
            main_category_code = int(digits[1:3])
            sub_category_code = int(digits[3:5])
        except Exception:
            return jsonify({'success': False, 'message': '零件号格式错误'}), 400

        if not is_valid_part_number(part_id, part_category_code, main_category_code):
            return jsonify({'success': False, 'message': '零件号不符合编码规则'}), 400

        exists = VisirayPartNumber.query.get(part_id)
        if exists:
            if part_name:
                exists.part_name = part_name
            exists.unit = unit
            exists.standard_cost = standard_cost
            synced_material = _sync_material_from_part_number(exists, getattr(user, 'id', None) if user else None)
            db.session.commit()
            data = exists.to_dict()
            data['material_id'] = getattr(synced_material, 'id', None)
            data['material_standard_cost'] = float(getattr(synced_material, 'standard_cost', 0) or 0)
            return jsonify({'success': True, 'message': '零件号已存在', 'data': data})

        category = 'custom' if 0 <= part_category_code <= 4 else 'purchased'
        main_type = (
            'optical' if 0 <= main_category_code <= 19 else
            'mechanical' if 20 <= main_category_code <= 39 else
            'electrical' if 40 <= main_category_code <= 59 else
            'software' if 60 <= main_category_code <= 69 else
            'chemical' if 70 <= main_category_code <= 79 else
            'other'
        )

        def get_subtype_by_codes(main_type: str, category: str, sub_code: int) -> str:
            index_group = max(0, min(9, sub_code // 10))
            maps = {
                ('optical', 'purchased'): [
                    'light_source', 'light_transmission', 'lens_prism', 'optical_filter',
                    'optical_sensor', 'light_modulator', 'display_imaging', 'optical_other'
                ],
                ('mechanical', 'purchased'): [
                    'aluminum_profile', 'transmission', 'fasteners', 'spring', 'net_filter', 'mechanical_other'
                ],
                ('mechanical', 'custom'): [
                    'iron_steel', 'copper_aluminum_titanium', 'other_metal', 'plastic', 'rubber', 'glass_ceramic', 'material_other'
                ],
                ('electrical', 'purchased'): [
                    'passive', 'semiconductor', 'electromechanical', 'power', 'sensor', 'electrical_other'
                ],
                ('electrical', 'custom'): [
                    'custom_power', 'custom_sensor', 'wire_harness', 'drive_control', 'custom_electrical_other'
                ],
                ('software', 'purchased'): [
                    'system_software', 'office_software', 'security_software', 'engineering_software', 'development_tools', 'software_other'
                ],
                ('software', 'custom'): [
                    'custom_platform', 'custom_development_tools', 'custom_information_visualization', 'custom_software_other'
                ],
                ('chemical', 'purchased'): [
                    'inorganic', 'organic', 'reagent', 'functional', 'material_chemical', 'hazardous', 'chemical_other'
                ],
                ('chemical', 'custom'): [
                    'custom_formulation', 'custom_polymer', 'custom_coating', 'custom_functional', 'custom_material', 'custom_environmental', 'custom_chemical_other'
                ],
                ('other', 'purchased'): [],
                ('other', 'custom'): []
            }
            lst = maps.get((main_type, category)) or []
            return lst[index_group] if index_group < len(lst) else ''

        sub_type = get_subtype_by_codes(main_type, category, sub_category_code)
        record = VisirayPartNumber(
            part_id=part_id,
            category=category,
            main_type=main_type,
            sub_type=sub_type,
            part_name=part_name,
            unit=unit,
            standard_cost=standard_cost,
            created_by=(getattr(user, 'id', None) if user else None),
            created_by_name=((getattr(user, 'name', None) or getattr(user, 'username', None) or getattr(user, 'email', None)) if user else None)
        )
        db.session.add(record)
        db.session.flush()
        synced_material = _sync_material_from_part_number(record, getattr(user, 'id', None) if user else None)
        db.session.commit()
        data = record.to_dict()
        data['material_id'] = getattr(synced_material, 'id', None)
        data['material_standard_cost'] = float(getattr(synced_material, 'standard_cost', 0) or 0)

        return jsonify({'success': True, 'message': '添加成功', 'data': data})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'}), 500


@bp.route('/visiray/part-number/import-xlsx', methods=['POST'])
@jwt_required(optional=True)
def import_part_numbers_from_xlsx():
    try:
        user = _get_request_user()
        if not user or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401

        upload_file = request.files.get('file')
        if not upload_file or not upload_file.filename:
            return jsonify({'success': False, 'message': '请选择要导入的Excel文件'}), 400
        if not upload_file.filename.lower().endswith(('.xlsx', '.xlsm')):
            return jsonify({'success': False, 'message': '仅支持 .xlsx 或 .xlsm 文件'}), 400

        from openpyxl import load_workbook
        workbook = load_workbook(upload_file, read_only=True, data_only=True)

        created_count = 0
        updated_count = 0
        created_supplier_count = 0
        created_quote_count = 0
        updated_quote_count = 0
        skipped_count = 0
        error_items = []
        imported_items = []
        processed_part_ids = set()
        part_ids_by_name = {}
        import_rows = []

        def add_error(sheet_title, row_number, part_id, reason):
            if len(error_items) < 100:
                error_items.append({
                    'sheet': sheet_title,
                    'row': row_number,
                    'part_id': part_id,
                    'reason': reason
                })

        def remember_part_name(part):
            name_key = _normalize_part_name_key(getattr(part, 'part_name', None))
            if name_key:
                part_ids_by_name.setdefault(name_key, set()).add(part.part_id)

        def row_value(row, index):
            return row[index] if index is not None and index < len(row) else None

        for sheet in workbook.worksheets:
            header_map = None
            header_row_number = 0
            for row_number, row in enumerate(sheet.iter_rows(min_row=1, max_row=min(sheet.max_row or 1, 20), values_only=True), 1):
                header_map = _find_part_import_header(row)
                if header_map:
                    header_row_number = row_number
                    break
            if not header_map:
                continue

            part_id_index = header_map.get('part_id')
            for row_number, row in enumerate(sheet.iter_rows(min_row=header_row_number + 1, values_only=True), header_row_number + 1):
                raw_part_id = _clean_excel_cell(row_value(row, part_id_index))
                part_name = _clean_excel_cell(row_value(row, header_map.get('part_name')))
                supplier_raw = _clean_excel_cell(row_value(row, header_map.get('supplier')))
                price_raw = row_value(row, header_map.get('standard_cost'))
                remark = _clean_excel_cell(row_value(row, header_map.get('remark')))
                material_note = _clean_excel_cell(row_value(row, header_map.get('material_note')))
                unit = _clean_excel_cell(row_value(row, header_map.get('unit'))) or 'pcs'

                if not any([raw_part_id, part_name, supplier_raw, price_raw, remark, material_note]):
                    skipped_count += 1
                    continue

                import_rows.append({
                    'sheet': sheet.title,
                    'row': row_number,
                    'raw_part_id': raw_part_id,
                    'part_name': part_name,
                    'unit': unit,
                    'standard_cost': _parse_excel_price(price_raw),
                    'supplier_raw': supplier_raw,
                    'remark': remark,
                    'material_note': material_note,
                    'part_id': None,
                    'part_error': None,
                })

        for entry in import_rows:
            raw_part_id = entry['raw_part_id']
            if not raw_part_id:
                continue

            try:
                part_id, category, main_type, sub_type = _part_number_classification(raw_part_id)
                entry['part_id'] = part_id
                if part_id in processed_part_ids:
                    existing_duplicate = VisirayPartNumber.query.get(part_id)
                    if existing_duplicate:
                        remember_part_name(existing_duplicate)
                    continue
                processed_part_ids.add(part_id)

                part_name = entry['part_name'] or None
                unit = entry['unit'] or 'pcs'
                standard_cost = entry['standard_cost']

                existing = VisirayPartNumber.query.get(part_id)
                if existing:
                    if part_name:
                        existing.part_name = part_name
                    if unit:
                        existing.unit = unit
                    if standard_cost is not None:
                        existing.standard_cost = standard_cost
                    _sync_material_from_part_number(existing, getattr(user, 'id', None))
                    db.session.flush()
                    remember_part_name(existing)
                    updated_count += 1
                    imported_items.append({'row': entry['row'], 'sheet': entry['sheet'], 'part_id': part_id, 'status': 'updated'})
                    continue

                record = VisirayPartNumber(
                    part_id=part_id,
                    category=category,
                    main_type=main_type,
                    sub_type=sub_type,
                    part_name=part_name,
                    unit=unit,
                    standard_cost=standard_cost if standard_cost is not None else 0,
                    created_by=(getattr(user, 'id', None) if user else None),
                    created_by_name=((getattr(user, 'name', None) or getattr(user, 'username', None) or getattr(user, 'email', None)) if user else None)
                )
                db.session.add(record)
                db.session.flush()
                _sync_material_from_part_number(record, getattr(user, 'id', None))
                db.session.flush()
                remember_part_name(record)
                created_count += 1
                imported_items.append({'row': entry['row'], 'sheet': entry['sheet'], 'part_id': part_id, 'status': 'created'})
            except Exception as row_error:
                entry['part_error'] = str(row_error)
                skipped_count += 1
                add_error(entry['sheet'], entry['row'], raw_part_id, str(row_error))

        def resolve_quote_part(entry):
            if entry.get('part_id'):
                part = VisirayPartNumber.query.get(entry['part_id'])
                if part:
                    return part

            name_key = _normalize_part_name_key(entry.get('part_name'))
            if not name_key:
                raise ValueError('缺少零件号，且没有零件名称可用于匹配')

            candidate_ids = set(part_ids_by_name.get(name_key) or [])
            db_matches = VisirayPartNumber.query.filter_by(part_name=entry.get('part_name')).limit(20).all()
            for match in db_matches:
                candidate_ids.add(match.part_id)

            if len(candidate_ids) == 1:
                return VisirayPartNumber.query.get(next(iter(candidate_ids)))
            if len(candidate_ids) > 1:
                raise ValueError('零件名称匹配到多个零件号，请在Excel中补充零件号')
            raise ValueError('未找到匹配的零件号，请先导入零件号或在Excel中补充零件号')

        for entry in import_rows:
            supplier_raw = entry.get('supplier_raw')
            price = entry.get('standard_cost')
            if not supplier_raw or price is None or price <= 0:
                continue
            if entry.get('part_error'):
                continue

            try:
                supplier_name, supplier_part_no, website = _split_supplier_text(supplier_raw)
                if not supplier_name:
                    continue
                part = resolve_quote_part(entry)
                material = _sync_material_from_part_number(part, getattr(user, 'id', None))
                if not part.standard_cost or float(part.standard_cost or 0) == 0:
                    part.standard_cost = price
                    material.standard_cost = price
                db.session.flush()

                remark_parts = [entry.get('remark'), entry.get('material_note')]
                remark = ' / '.join([value for value in remark_parts if value])
                supplier, created_supplier = _ensure_supplier_by_name(
                    supplier_name,
                    getattr(user, 'id', None),
                    website=website,
                    remark='Excel导入自动创建'
                )
                if created_supplier:
                    created_supplier_count += 1

                quote_status = _upsert_material_supplier(
                    material,
                    supplier,
                    price,
                    supplier_part_no=supplier_part_no,
                    remark=remark or None
                )
                if quote_status == 'created':
                    created_quote_count += 1
                else:
                    updated_quote_count += 1
            except Exception as quote_error:
                skipped_count += 1
                add_error(entry['sheet'], entry['row'], entry.get('part_id') or entry.get('raw_part_id'), str(quote_error))

        total_changed = created_count + updated_count + created_supplier_count + created_quote_count + updated_quote_count
        if total_changed == 0:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': '未导入任何数据，请确认Excel包含“零件号/零件名称/供应商/单价”等列且数据格式正确',
                'data': {
                    'created_count': created_count,
                    'updated_count': updated_count,
                    'created_supplier_count': created_supplier_count,
                    'created_quote_count': created_quote_count,
                    'updated_quote_count': updated_quote_count,
                    'skipped_count': skipped_count,
                    'errors': error_items
                }
            }), 400

        db.session.commit()
        return jsonify({
            'success': True,
            'message': (
                f'导入完成：新增零件{created_count}条，更新零件{updated_count}条，'
                f'新增供应商{created_supplier_count}条，新增报价{created_quote_count}条，'
                f'更新报价{updated_quote_count}条，跳过{skipped_count}条'
            ),
            'data': {
                'created_count': created_count,
                'updated_count': updated_count,
                'created_supplier_count': created_supplier_count,
                'created_quote_count': created_quote_count,
                'updated_quote_count': updated_quote_count,
                'skipped_count': skipped_count,
                'errors': error_items,
                'items': imported_items[:100]
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'导入Excel失败: {str(e)}'}), 500

@bp.route('/visiray/register', methods=['POST'])
def visiray_register():
    """Visiray鐢ㄦ埛娉ㄥ唽"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 楠岃瘉蹇呭～瀛楁
        required_fields = ['username', 'account', 'password', 'confirm_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空'
                }), 400
        
        # 楠岃瘉瀵嗙爜闀垮害
        password = data.get('password', '')
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': '密码长度不能少于6位'
            }), 400
        
        # 楠岃瘉瀵嗙爜纭
        if password != data.get('confirm_password'):
            return jsonify({
                'success': False,
                'message': '两次输入的密码不一致'
            }), 400
        
        # 妫€鏌ヨ处鎴锋槸鍚﹀凡瀛樺湪
        existing_user = VisirayUserAccount.query.filter_by(account=data['account']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': '璐︽埛宸插瓨鍦?'
            }), 400
        
        # 鍒涘缓鏂扮敤鎴?
        new_user = VisirayUserAccount(
            username=data['username'],
            account=data['account'],
            password=generate_password_hash(password)  # 瀵嗙爜鍝堝笇澶勭悊
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Visiray鐢ㄦ埛娉ㄥ唽澶辫触: {str(e)}")
        return jsonify({
            'success': False,
            'message': '注册失败，请稍后重试'
        }), 500


@bp.route('/visiray/login', methods=['POST'])
def visiray_login():
    """Visiray鐢ㄦ埛鐧诲綍"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 楠岃瘉蹇呭～瀛楁
        account = data.get('account', '').strip()
        password = data.get('password', '')
        
        if not account or not password:
            return jsonify({
                'success': False,
                'message': '璐︽埛鍜屽瘑鐮佷笉鑳戒负绌?'
            }), 400
        
        # 鏌ユ壘鐢ㄦ埛
        user = VisirayUserAccount.query.filter_by(account=account).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({
                'success': False,
                'message': '账号或密码错误'
            }), 401
        
        # 鐧诲綍鎴愬姛锛屽啓鍏ヤ細璇濅互渚垮悗缁姹傝瘑鍒垱寤轰汉
        try:
            session['visiray_account'] = user.account
            session['visiray_username'] = user.username
        except Exception:
            pass
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Visiray鐢ㄦ埛鐧诲綍澶辫触: {str(e)}")
        return jsonify({
            'success': False,
            'message': '登录失败，请稍后重试'
        }), 500


def _contract_number_attachment_dir():
    folder = os.path.join(current_app.root_path, '..', 'uploads', 'contract_number_attachments')
    os.makedirs(folder, exist_ok=True)
    return folder


@bp.route('/visiray/contract-number/apply', methods=['POST'])
@jwt_required(optional=True)
def apply_contract_number():
    try:
        user = _get_request_user()
        if not user or not user.is_active:
            return jsonify({'success': False, 'message': '用户无效'}), 401

        data = request.get_json(silent=True) or {} if request.is_json else request.form.to_dict()
        date_str = data.get('date')
        subject = (data.get('subject') or '').strip()
        supplier = (data.get('supplier') or '').strip()
        related_order_no = (data.get('related_order_no') or '').strip()
        purchase_content = (data.get('purchase_content') or '').strip()
        quantity = None if data.get('quantity') in (None, '') else _to_float(data.get('quantity'))
        amount = None if data.get('amount') in (None, '') else _to_float(data.get('amount'))
        remark = (data.get('remark') or '').strip()
        attachment = request.files.get('attachment') if not request.is_json else None

        if not subject:
            return jsonify({'success': False, 'message': '请填写合同绑定事宜（主题/用途）'}), 400
        if attachment and attachment.filename and not _allowed_file(attachment.filename):
            return jsonify({'success': False, 'message': '附件类型不支持'}), 400
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'message': '日期格式错误，应为 YYYY-MM-DD'}), 400
        else:
            date_obj = datetime.now().date()

        current_seq = db.session.query(func.max(VisirayContractNumberRecord.seq)).filter(
            VisirayContractNumberRecord.date == date_obj
        ).scalar() or 0
        if current_seq >= 999:
            return jsonify({'success': False, 'message': '当天合同号已达到上限(999)'}), 400

        next_seq = int(current_seq) + 1
        contract_no = f"VISC{date_obj.strftime('%Y%m%d')}-{next_seq:03d}"

        attachment_file = None
        attachment_name = None
        if attachment and attachment.filename:
            attachment_name = attachment.filename
            safe_name = _safe_filename(attachment.filename)
            attachment_file = f"{contract_no}_{uuid.uuid4().hex[:8]}_{safe_name}"
            attachment.save(os.path.join(_contract_number_attachment_dir(), attachment_file))

        record = VisirayContractNumberRecord(
            date=date_obj,
            seq=next_seq,
            contract_no=contract_no,
            subject=subject,
            supplier=supplier,
            related_order_no=related_order_no,
            purchase_content=purchase_content,
            quantity=quantity,
            amount=amount,
            attachment_file=attachment_file,
            attachment_name=attachment_name,
            remark=remark,
            created_by=getattr(user, 'name', None) or getattr(user, 'username', None) or str(user.id),
            created_at=datetime.now(),
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({'success': True, 'data': record.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'合同号申请失败: {str(e)}'}), 500


@bp.route('/visiray/contract-number/<path:contract_no>/attachment', methods=['GET'])
@jwt_required(optional=True)
def get_contract_number_attachment(contract_no):
    try:
        user = _get_request_user()
        if not user or not user.is_active:
            return jsonify({'success': False, 'message': '用户无效'}), 401

        record = VisirayContractNumberRecord.query.filter_by(contract_no=contract_no).first()
        if not record or not record.attachment_file:
            return jsonify({'success': False, 'message': '附件不存在'}), 404

        file_path = os.path.join(_contract_number_attachment_dir(), record.attachment_file)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '附件不存在'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=record.attachment_name or record.attachment_file
        )
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取合同号附件失败: {str(e)}'}), 500


@bp.route('/visiray/contract-number/list', methods=['GET'])
@jwt_required(optional=True)
def list_contract_numbers():
    try:
        user = _get_request_user()
        if not user or not user.is_active:
            return jsonify({'success': False, 'message': '用户无效'}), 401

        keyword = (request.args.get('keyword') or '').strip()
        date_filter = (request.args.get('date') or '').strip()
        query = VisirayContractNumberRecord.query
        if keyword:
            search_term = f"%{keyword}%"
            query = query.filter(
                (VisirayContractNumberRecord.contract_no.like(search_term)) |
                (VisirayContractNumberRecord.subject.like(search_term)) |
                (VisirayContractNumberRecord.supplier.like(search_term)) |
                (VisirayContractNumberRecord.related_order_no.like(search_term)) |
                (VisirayContractNumberRecord.purchase_content.like(search_term))
            )
        if date_filter:
            try:
                query = query.filter(VisirayContractNumberRecord.date == datetime.strptime(date_filter, '%Y-%m-%d').date())
            except ValueError:
                return jsonify({'success': False, 'message': '日期格式错误，应为 YYYY-MM-DD'}), 400

        try:
            page = int(request.args.get('page', '1'))
            per_page = int(request.args.get('per_page', '20'))
        except Exception:
            page = 1
            per_page = 20
        page = max(page, 1)
        per_page = max(per_page, 1)

        total = query.count()
        records = (
            query
            .order_by(VisirayContractNumberRecord.created_at.desc(), VisirayContractNumberRecord.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return jsonify({'success': True, 'data': {
            'items': [record.to_dict() for record in records],
            'current_page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
        }})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取合同号列表失败: {str(e)}'}), 500

