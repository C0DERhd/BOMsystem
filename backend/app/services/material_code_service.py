import re
from typing import Dict, Tuple, Optional
from sqlalchemy import func
from app import db
from app.models.material import Material, MaterialCategory

class MaterialCodeService:
    """12位物料编码生成和验证服务"""
    
    # 编码规则配置
    CODE_LENGTH = 12
    
    # 各段位数定义
    PART_TYPE_LENGTH = 2        # 1-2位：零部件大类
    TYPE_IDENTIFIER_LENGTH = 1  # 3位：定制/外购标识  
    PART_CATEGORY_LENGTH = 2    # 4-5位：部件类别
    CLASSIFICATION_LENGTH = 2   # 6-7位：分类号
    SEQUENCE_LENGTH = 4         # 8-11位：零件顺序号
    VERSION_LENGTH = 1          # 12位：版本号
    
    # 编码范围定义
    PART_TYPE_RANGES = {
        'custom': {'min': 1, 'max': 1, 'name': '定制件'},
        'purchase': {'min': 2, 'max': 2, 'name': '外购件'},
        # 预留扩展到04
    }
    
    TYPE_IDENTIFIER_MAP = {
        'custom': 0,    # 定制件标识
        'purchase': 5,  # 外购件标识
    }
    
    PART_CATEGORY_RANGES = {
        'mechanical': {'min': 20, 'max': 29, 'name': '机械件'},
        'optical': {'min': 30, 'max': 34, 'name': '光学件'},
        'electrical': {'min': 35, 'max': 39, 'name': '电气件'},
        # 可扩展其他类别
    }
    
    @classmethod
    def generate_material_code(cls, part_type: str, material_type: str, 
                              part_category: str, classification: int, 
                              version: int = 0) -> str:
        """
        生成12位物料编码
        
        Args:
            part_type: 零部件类型 ('custom', 'purchase')
            material_type: 材料类型 ('custom', 'purchase') 
            part_category: 部件类别 ('mechanical', 'optical', 'electrical')
            classification: 分类号 (00-99)
            version: 版本号 (0-9)
            
        Returns:
            str: 12位物料编码
            
        Raises:
            ValueError: 参数无效时抛出异常
        """
        
        # 验证输入参数
        if part_type not in cls.PART_TYPE_RANGES:
            raise ValueError(f"无效的零部件类型: {part_type}")
            
        if material_type not in cls.TYPE_IDENTIFIER_MAP:
            raise ValueError(f"无效的材料类型: {material_type}")
            
        if part_category not in cls.PART_CATEGORY_RANGES:
            raise ValueError(f"无效的部件类别: {part_category}")
            
        if not (0 <= classification <= 99):
            raise ValueError(f"分类号必须在0-99范围内: {classification}")
            
        if not (0 <= version <= 9):
            raise ValueError(f"版本号必须在0-9范围内: {version}")
        
        # 获取各段编码
        part_type_code = f"{cls.PART_TYPE_RANGES[part_type]['min']:02d}"
        type_identifier = cls.TYPE_IDENTIFIER_MAP[material_type]
        part_category_code = f"{cls.PART_CATEGORY_RANGES[part_category]['min']:02d}"
        classification_code = f"{classification:02d}"
        
        # 生成唯一序列号
        sequence = cls._generate_sequence(part_type_code, type_identifier, 
                                        part_category_code, classification_code)
        sequence_code = f"{sequence:04d}"
        
        # 组装完整编码
        material_code = (f"{part_type_code}"
                        f"{type_identifier}"
                        f"{part_category_code}"
                        f"{classification_code}"
                        f"{sequence_code}"
                        f"{version}")
        
        return material_code
    
    @classmethod
    def _generate_sequence(cls, part_type: str, type_identifier: int,
                          part_category: str, classification: str) -> int:
        """
        生成序列号 (8-11位)
        
        Args:
            part_type: 零部件大类代码
            type_identifier: 定制/外购标识
            part_category: 部件类别代码  
            classification: 分类号代码
            
        Returns:
            int: 序列号
        """
        
        # 构建前缀模式用于查询
        prefix = f"{part_type}{type_identifier}{part_category}{classification}"
        
        # 查询该前缀下的最大序列号
        max_code = db.session.query(func.max(Material.material_code)).filter(
            Material.material_code.like(f"{prefix}____")
        ).scalar()
        
        if max_code:
            # 提取序列号并递增
            try:
                current_sequence = int(max_code[7:11])
                return current_sequence + 1
            except (ValueError, IndexError):
                return 1
        else:
            # 首次生成从1开始
            return 1
    
    @classmethod
    def validate_material_code(cls, material_code: str) -> Tuple[bool, str]:
        """
        验证物料编码格式和有效性
        
        Args:
            material_code: 待验证的物料编码
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        
        # 基础格式验证
        if not material_code:
            return False, "物料编码不能为空"
            
        if not material_code.isdigit():
            return False, "物料编码必须为纯数字"
            
        if len(material_code) != cls.CODE_LENGTH:
            return False, f"物料编码长度必须为{cls.CODE_LENGTH}位"
        
        try:
            # 解析各段
            parsed = cls.parse_material_code(material_code)
            
            # 验证零部件大类
            part_type_valid = any(
                parsed['part_type'] == range_info['min'] 
                for range_info in cls.PART_TYPE_RANGES.values()
            )
            if not part_type_valid:
                return False, f"无效的零部件大类: {parsed['part_type']:02d}"
            
            # 验证定制/外购标识
            type_identifier_valid = parsed['type_identifier'] in cls.TYPE_IDENTIFIER_MAP.values()
            if not type_identifier_valid:
                return False, f"无效的定制/外购标识: {parsed['type_identifier']}"
            
            # 验证部件类别
            part_category_valid = any(
                range_info['min'] <= parsed['part_category'] <= range_info['max']
                for range_info in cls.PART_CATEGORY_RANGES.values()
            )
            if not part_category_valid:
                return False, f"无效的部件类别: {parsed['part_category']:02d}"
            
            # 验证分类号范围
            if not (0 <= parsed['classification'] <= 99):
                return False, f"无效的分类号: {parsed['classification']:02d}"
            
            # 验证序列号范围
            if not (0 <= parsed['sequence'] <= 9999):
                return False, f"无效的序列号: {parsed['sequence']:04d}"
            
            # 验证版本号范围
            if not (0 <= parsed['version'] <= 9):
                return False, f"无效的版本号: {parsed['version']}"
            
            # 验证逻辑一致性
            consistency_check = cls._validate_code_consistency(parsed)
            if not consistency_check[0]:
                return False, consistency_check[1]
            
            return True, "编码有效"
            
        except Exception as e:
            return False, f"编码解析错误: {str(e)}"
    
    @classmethod
    def parse_material_code(cls, material_code: str) -> Dict:
        """
        解析物料编码各段信息
        
        Args:
            material_code: 12位物料编码
            
        Returns:
            Dict: 解析后的编码信息
        """
        
        if len(material_code) != cls.CODE_LENGTH:
            raise ValueError("编码长度不正确")
        
        return {
            'part_type': int(material_code[0:2]),           # 1-2位
            'type_identifier': int(material_code[2:3]),     # 3位
            'part_category': int(material_code[3:5]),       # 4-5位  
            'classification': int(material_code[5:7]),      # 6-7位
            'sequence': int(material_code[7:11]),           # 8-11位
            'version': int(material_code[11:12]),           # 12位
        }
    
    @classmethod
    def _validate_code_consistency(cls, parsed: Dict) -> Tuple[bool, str]:
        """
        验证编码逻辑一致性
        
        Args:
            parsed: 解析后的编码信息
            
        Returns:
            Tuple[bool, str]: (是否一致, 错误信息)
        """
        
        # 检查零部件大类与定制/外购标识的一致性
        part_type = parsed['part_type']
        type_identifier = parsed['type_identifier']
        
        if part_type == 1:  # 定制件
            if type_identifier != 0:
                return False, "定制件(01)的第3位应该为0"
        elif part_type == 2:  # 外购件
            if type_identifier != 5:
                return False, "外购件(02)的第3位应该为5"
        
        return True, "逻辑一致"
    
    @classmethod
    def check_code_uniqueness(cls, material_code: str, exclude_id: Optional[int] = None) -> bool:
        """
        检查编码唯一性
        
        Args:
            material_code: 待检查的编码
            exclude_id: 排除的物料ID（用于更新时检查）
            
        Returns:
            bool: 是否唯一
        """
        
        query = Material.query.filter_by(material_code=material_code)
        if exclude_id:
            query = query.filter(Material.id != exclude_id)
        
        return query.first() is None
    
    @classmethod
    def get_next_version_code(cls, base_code: str) -> str:
        """
        获取下一个版本的编码
        
        Args:
            base_code: 基础编码(前11位)
            
        Returns:
            str: 新版本编码
        """
        
        if len(base_code) == cls.CODE_LENGTH:
            base_code = base_code[:11]  # 取前11位
        elif len(base_code) != 11:
            raise ValueError("基础编码长度应为11位")
        
        # 查询该基础编码的最大版本号
        max_code = db.session.query(func.max(Material.material_code)).filter(
            Material.material_code.like(f"{base_code}_")
        ).scalar()
        
        if max_code:
            current_version = int(max_code[11])
            if current_version >= 9:
                raise ValueError("版本号已达到最大值(9)，需要重新分配物料号")
            new_version = current_version + 1
        else:
            new_version = 0
        
        return f"{base_code}{new_version}"
    
    @classmethod
    def get_code_description(cls, material_code: str) -> Dict:
        """
        获取编码各段的中文描述
        
        Args:
            material_code: 12位物料编码
            
        Returns:
            Dict: 编码描述信息
        """
        
        try:
            parsed = cls.parse_material_code(material_code)
            
            # 获取零部件大类描述
            part_type_desc = "未知"
            for key, value in cls.PART_TYPE_RANGES.items():
                if parsed['part_type'] == value['min']:
                    part_type_desc = value['name']
                    break
            
            # 获取定制/外购描述
            type_identifier_desc = "未知"
            for key, value in cls.TYPE_IDENTIFIER_MAP.items():
                if parsed['type_identifier'] == value:
                    type_identifier_desc = "定制件" if key == 'custom' else "外购件"
                    break
            
            # 获取部件类别描述
            part_category_desc = "未知"
            for key, value in cls.PART_CATEGORY_RANGES.items():
                if value['min'] <= parsed['part_category'] <= value['max']:
                    part_category_desc = value['name']
                    break
            
            return {
                'material_code': material_code,
                'part_type': {
                    'code': f"{parsed['part_type']:02d}",
                    'description': part_type_desc
                },
                'type_identifier': {
                    'code': str(parsed['type_identifier']),
                    'description': type_identifier_desc
                },
                'part_category': {
                    'code': f"{parsed['part_category']:02d}",
                    'description': part_category_desc
                },
                'classification': {
                    'code': f"{parsed['classification']:02d}",
                    'description': f"分类{parsed['classification']:02d}"
                },
                'sequence': {
                    'code': f"{parsed['sequence']:04d}",
                    'description': f"序号{parsed['sequence']:04d}"
                },
                'version': {
                    'code': str(parsed['version']),
                    'description': f"版本{parsed['version']}"
                }
            }
            
        except Exception as e:
            return {'error': f"编码解析失败: {str(e)}"}
    
    @classmethod
    def get_coding_rules(cls) -> Dict:
        """
        获取编码规则配置
        
        Returns:
            Dict: 编码规则信息
        """
        
        return {
            'code_length': cls.CODE_LENGTH,
            'structure': {
                'part_type': {
                    'position': '1-2位',
                    'description': '零部件大类',
                    'ranges': cls.PART_TYPE_RANGES
                },
                'type_identifier': {
                    'position': '3位', 
                    'description': '定制/外购标识',
                    'mapping': cls.TYPE_IDENTIFIER_MAP
                },
                'part_category': {
                    'position': '4-5位',
                    'description': '部件类别',
                    'ranges': cls.PART_CATEGORY_RANGES
                },
                'classification': {
                    'position': '6-7位',
                    'description': '分类号',
                    'range': '00-99'
                },
                'sequence': {
                    'position': '8-11位',
                    'description': '零件顺序号',
                    'range': '0000-9999'
                },
                'version': {
                    'position': '12位',
                    'description': '版本号',
                    'range': '0-9'
                }
            },
            'examples': {
                'custom_mechanical': {
                    'code': '010200050123​0',
                    'description': '定制机械件示例'
                },
                'purchase_mechanical': {
                    'code': '025203504560​0',
                    'description': '外购机械件示例'
                }
            }
        }