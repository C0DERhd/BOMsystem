import secrets
import string
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request
from sqlalchemy.orm.query import Query

def paginate_query(query: Query, page: int = None, per_page: int = None) -> Dict[str, Any]:
    """
    分页查询辅助函数
    
    Args:
        query: SQLAlchemy查询对象
        page: 页码（从1开始）
        per_page: 每页数量
        
    Returns:
        Dict: 分页结果
    """
    
    # 从请求参数获取分页信息
    if page is None:
        page = request.args.get('page', 1, type=int)
    if per_page is None:
        per_page = request.args.get('per_page', 20, type=int)
    
    # 限制每页数量范围
    per_page = max(1, min(per_page, 100))
    page = max(1, page)
    
    # 执行分页查询
    paginated = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return {
        'items': paginated.items,
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': paginated.page,
        'per_page': paginated.per_page,
        'has_prev': paginated.has_prev,
        'has_next': paginated.has_next,
        'prev_num': paginated.prev_num,
        'next_num': paginated.next_num
    }

def format_datetime(dt: Optional[datetime], format_str: str = '%Y-%m-%d %H:%M:%S') -> Optional[str]:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象
        format_str: 格式字符串
        
    Returns:
        str: 格式化后的字符串
    """
    
    if dt is None:
        return None
    
    return dt.strftime(format_str)

def generate_random_string(length: int = 32, 
                          include_digits: bool = True,
                          include_uppercase: bool = True, 
                          include_lowercase: bool = True) -> str:
    """
    生成随机字符串
    
    Args:
        length: 字符串长度
        include_digits: 是否包含数字
        include_uppercase: 是否包含大写字母
        include_lowercase: 是否包含小写字母
        
    Returns:
        str: 随机字符串
    """
    
    chars = ''
    if include_lowercase:
        chars += string.ascii_lowercase
    if include_uppercase:
        chars += string.ascii_uppercase
    if include_digits:
        chars += string.digits
    
    if not chars:
        chars = string.ascii_letters + string.digits
    
    return ''.join(secrets.choice(chars) for _ in range(length))

def parse_sort_params(default_sort: str = 'id', allowed_fields: list = None) -> Dict[str, str]:
    """
    解析排序参数
    
    Args:
        default_sort: 默认排序字段
        allowed_fields: 允许排序的字段列表
        
    Returns:
        Dict: 排序参数
    """
    
    sort_by = request.args.get('sort_by', default_sort)
    sort_order = request.args.get('sort_order', 'asc').lower()
    
    # 验证排序方向
    if sort_order not in ['asc', 'desc']:
        sort_order = 'asc'
    
    # 验证排序字段
    if allowed_fields and sort_by not in allowed_fields:
        sort_by = default_sort
    
    return {
        'sort_by': sort_by,
        'sort_order': sort_order
    }

def build_search_query(query: Query, search_fields: list, search_term: str) -> Query:
    """
    构建搜索查询
    
    Args:
        query: 基础查询
        search_fields: 搜索字段列表
        search_term: 搜索词
        
    Returns:
        Query: 添加搜索条件的查询
    """
    
    if not search_term or not search_fields:
        return query
    
    # 构建OR条件
    conditions = []
    for field in search_fields:
        if hasattr(field, 'like'):
            conditions.append(field.like(f'%{search_term}%'))
    
    if conditions:
        from sqlalchemy import or_
        query = query.filter(or_(*conditions))
    
    return query

def safe_int(value: Any, default: int = 0) -> int:
    """
    安全转换为整数
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        int: 转换后的整数
    """
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    安全转换为浮点数
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        float: 转换后的浮点数
    """
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def filter_dict_keys(data: dict, allowed_keys: list) -> dict:
    """
    过滤字典键
    
    Args:
        data: 原始字典
        allowed_keys: 允许的键列表
        
    Returns:
        dict: 过滤后的字典
    """
    
    return {k: v for k, v in data.items() if k in allowed_keys}

def remove_empty_values(data: dict) -> dict:
    """
    移除字典中的空值
    
    Args:
        data: 原始字典
        
    Returns:
        dict: 移除空值后的字典
    """
    
    return {k: v for k, v in data.items() 
            if v is not None and v != '' and v != []}

def generate_code(prefix: str = '', length: int = 8) -> str:
    """
    生成编码
    
    Args:
        prefix: 前缀
        length: 编码长度（不包含前缀）
        
    Returns:
        str: 生成的编码
    """
    
    code_part = generate_random_string(
        length=length,
        include_lowercase=False,
        include_digits=True,
        include_uppercase=True
    )
    
    return f"{prefix}{code_part}" if prefix else code_part