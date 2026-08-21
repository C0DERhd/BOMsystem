import re
from typing import Dict, Any

def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 是否有效
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> Dict[str, Any]:
    """
    验证密码强度
    
    Args:
        password: 密码
        
    Returns:
        Dict: 验证结果
    """
    if not password:
        return {'valid': False, 'message': '密码不能为空'}
    
    if len(password) < 6:
        return {'valid': False, 'message': '密码长度至少6位'}
    
    if len(password) > 64:
        return {'valid': False, 'message': '密码长度不能超过64位'}
    
    # 检查是否包含字母
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    # 检查是否包含数字
    has_digit = bool(re.search(r'\d', password))
    
    if not (has_letter and has_digit):
        return {
            'valid': False, 
            'message': '密码必须包含字母和数字'
        }
    
    return {'valid': True, 'message': '密码格式正确'}

def validate_material_code(material_code: str) -> Dict[str, Any]:
    """
    验证物料编码格式
    
    Args:
        material_code: 物料编码
        
    Returns:
        Dict: 验证结果
    """
    from app.services.material_code_service import MaterialCodeService
    
    is_valid, message = MaterialCodeService.validate_material_code(material_code)
    return {
        'valid': is_valid,
        'message': message
    }

def validate_phone(phone: str) -> bool:
    """
    验证手机号格式
    
    Args:
        phone: 手机号
        
    Returns:
        bool: 是否有效
    """
    if not phone:
        return True  # 手机号可选
    
    # 支持中国手机号格式
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))

def validate_bom_code(bom_code: str) -> Dict[str, Any]:
    """
    验证BOM编码格式
    
    Args:
        bom_code: BOM编码
        
    Returns:
        Dict: 验证结果
    """
    if not bom_code:
        return {'valid': False, 'message': 'BOM编码不能为空'}
    
    if len(bom_code) > 32:
        return {'valid': False, 'message': 'BOM编码长度不能超过32位'}
    
    # BOM编码可以包含字母、数字、下划线、中划线
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, bom_code):
        return {
            'valid': False, 
            'message': 'BOM编码只能包含字母、数字、下划线、中划线'
        }
    
    return {'valid': True, 'message': 'BOM编码格式正确'}

def validate_supplier_code(supplier_code: str) -> Dict[str, Any]:
    """
    验证供应商编码格式
    
    Args:
        supplier_code: 供应商编码
        
    Returns:
        Dict: 验证结果
    """
    if not supplier_code:
        return {'valid': False, 'message': '供应商编码不能为空'}
    
    if len(supplier_code) > 32:
        return {'valid': False, 'message': '供应商编码长度不能超过32位'}
    
    # 供应商编码可以包含字母、数字、下划线、中划线
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, supplier_code):
        return {
            'valid': False,
            'message': '供应商编码只能包含字母、数字、下划线、中划线'
        }
    
    return {'valid': True, 'message': '供应商编码格式正确'}

def validate_decimal(value: Any, min_value: float = None, max_value: float = None) -> Dict[str, Any]:
    """
    验证数字格式
    
    Args:
        value: 数值
        min_value: 最小值
        max_value: 最大值
        
    Returns:
        Dict: 验证结果
    """
    try:
        if value is None or value == '':
            return {'valid': False, 'message': '数值不能为空'}
        
        num_value = float(value)
        
        if min_value is not None and num_value < min_value:
            return {'valid': False, 'message': f'数值不能小于{min_value}'}
        
        if max_value is not None and num_value > max_value:
            return {'valid': False, 'message': f'数值不能大于{max_value}'}
        
        return {'valid': True, 'message': '数值格式正确'}
        
    except (ValueError, TypeError):
        return {'valid': False, 'message': '数值格式不正确'}