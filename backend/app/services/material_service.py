from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import and_, or_
from app import db
from app.models.material import Material, MaterialCategory, MaterialSupplier
from app.models.supplier import Supplier
from app.services.material_code_service import MaterialCodeService

class MaterialService:
    """物料管理服务类"""
    
    @staticmethod
    def create_material(data: Dict[str, Any], created_by: int) -> Material:
        """
        创建物料
        
        Args:
            data: 物料数据
            created_by: 创建人ID
            
        Returns:
            Material: 创建的物料对象
        """
        
        # 生成物料编码
        if not data.get('material_code'):
            try:
                material_code = MaterialCodeService.generate_material_code(
                    part_type=data.get('part_type', 'custom'),
                    material_type=data.get('material_type', 'custom'),
                    part_category=data.get('part_category', 'mechanical'),
                    classification=data.get('classification', 0),
                    version=data.get('version', 0)
                )
                data['material_code'] = material_code
            except ValueError as e:
                raise ValueError(f"物料编码生成失败: {str(e)}")
        
        # 验证物料编码
        is_valid, message = MaterialCodeService.validate_material_code(data['material_code'])
        if not is_valid:
            raise ValueError(f"物料编码验证失败: {message}")
        
        # 检查编码唯一性
        if not MaterialCodeService.check_code_uniqueness(data['material_code']):
            raise ValueError(f"物料编码 {data['material_code']} 已存在")
        
        # 创建物料
        material = Material(
            material_code=data['material_code'],
            material_name=data['material_name'],
            visiray_part_id=data.get('visiray_part_id'),
            specification=data.get('specification'),
            unit=data.get('unit', '个'),
            category_id=data.get('category_id'),
            standard_cost=data.get('standard_cost', 0),
            currency=data.get('currency', 'CNY'),
            material_type=data.get('material_type', 'custom'),
            safety_stock=data.get('safety_stock', 0),
            current_stock=data.get('current_stock', 0),
            weight=data.get('weight'),
            volume=data.get('volume'),
            color=data.get('color'),
            material_grade=data.get('material_grade'),
            remark=data.get('remark'),
            created_by=created_by
        )
        
        # 解析物料编码
        material.parse_material_code()
        
        db.session.add(material)
        db.session.flush()  # 获取物料ID
        
        # 添加供应商信息
        if data.get('suppliers'):
            for supplier_data in data['suppliers']:
                MaterialService._create_material_supplier(material.id, supplier_data)
        
        db.session.commit()
        return material
    
    @staticmethod
    def update_material(material_id: int, data: Dict[str, Any]) -> Material:
        """
        更新物料
        
        Args:
            material_id: 物料ID
            data: 更新数据
            
        Returns:
            Material: 更新后的物料对象
        """
        
        material = Material.query.get(material_id)
        if not material:
            raise ValueError("物料不存在")
        
        # 如果更新物料编码，需要验证
        if 'material_code' in data and data['material_code'] != material.material_code:
            is_valid, message = MaterialCodeService.validate_material_code(data['material_code'])
            if not is_valid:
                raise ValueError(f"物料编码验证失败: {message}")
            
            if not MaterialCodeService.check_code_uniqueness(data['material_code'], material.id):
                raise ValueError(f"物料编码 {data['material_code']} 已存在")
        
        # 可更新的字段
        updatable_fields = [
            'material_code', 'material_name', 'visiray_part_id', 'specification', 'unit',
            'category_id', 'standard_cost', 'currency', 'material_type',
            'safety_stock', 'current_stock', 'weight', 'volume',
            'color', 'material_grade', 'remark', 'status'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(material, field, data[field])
        
        # 如果编码发生变化，重新解析
        if 'material_code' in data:
            material.parse_material_code()
        
        # 更新供应商信息
        if 'suppliers' in data:
            # 删除现有供应商关联
            MaterialSupplier.query.filter_by(material_id=material_id).delete()
            
            # 添加新的供应商关联
            for supplier_data in data['suppliers']:
                MaterialService._create_material_supplier(material_id, supplier_data)
        
        db.session.commit()
        return material
    
    @staticmethod
    def delete_material(material_id: int) -> bool:
        """
        删除物料
        
        Args:
            material_id: 物料ID
            
        Returns:
            bool: 是否删除成功
        """
        
        material = Material.query.get(material_id)
        if not material:
            return False
        
        # 检查是否被BOM引用
        if material.bom_items.first():
            raise ValueError("物料被BOM引用，无法删除")
        
        db.session.delete(material)
        db.session.commit()
        return True
    
    @staticmethod
    def search_materials(filters: Dict[str, Any], page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        搜索物料
        
        Args:
            filters: 搜索条件
            page: 页码
            per_page: 每页数量
            
        Returns:
            Dict: 搜索结果
        """
        
        query = Material.query
        
        # 搜索条件
        if filters.get('keyword'):
            keyword = f"%{filters['keyword']}%"
            query = query.filter(
                or_(
                    Material.material_code.like(keyword),
                    Material.material_name.like(keyword),
                    Material.specification.like(keyword)
                )
            )
        
        if filters.get('category_id'):
            query = query.filter(Material.category_id == filters['category_id'])
        
        if filters.get('material_type'):
            query = query.filter(Material.material_type == filters['material_type'])
        
        if filters.get('status'):
            query = query.filter(Material.status == filters['status'])
        
        if filters.get('created_by'):
            query = query.filter(Material.created_by == filters['created_by'])
        
        # 排序
        sort_by = filters.get('sort_by', 'created_at')
        sort_order = filters.get('sort_order', 'desc')
        
        if hasattr(Material, sort_by):
            order_field = getattr(Material, sort_by)
            if sort_order == 'desc':
                order_field = order_field.desc()
            query = query.order_by(order_field)
        
        # 分页
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'items': [material.to_dict() for material in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': paginated.page,
            'per_page': paginated.per_page,
            'has_prev': paginated.has_prev,
            'has_next': paginated.has_next
        }
    
    @staticmethod
    def get_material_categories(parent_id: int = None) -> List[Dict[str, Any]]:
        """
        获取物料分类
        
        Args:
            parent_id: 父分类ID
            
        Returns:
            List: 分类列表
        """
        
        query = MaterialCategory.query.filter_by(is_active=True)
        
        if parent_id is not None:
            query = query.filter_by(parent_id=parent_id)
        else:
            query = query.filter_by(parent_id=None)
        
        categories = query.order_by(MaterialCategory.sort_order).all()
        
        result = []
        for category in categories:
            category_data = category.to_dict()
            
            # 获取子分类
            children = MaterialCategory.query.filter_by(
                parent_id=category.id, 
                is_active=True
            ).order_by(MaterialCategory.sort_order).all()
            
            category_data['children'] = [child.to_dict() for child in children]
            result.append(category_data)
        
        return result
    
    @staticmethod
    def create_material_category(data: Dict[str, Any]) -> MaterialCategory:
        """
        创建物料分类
        
        Args:
            data: 分类数据
            
        Returns:
            MaterialCategory: 创建的分类对象
        """
        
        # 检查分类代码唯一性
        if MaterialCategory.query.filter_by(category_code=data['category_code']).first():
            raise ValueError(f"分类代码 {data['category_code']} 已存在")
        
        # 计算层级
        level = 1
        if data.get('parent_id'):
            parent = MaterialCategory.query.get(data['parent_id'])
            if parent:
                level = parent.level + 1
        
        category = MaterialCategory(
            category_code=data['category_code'],
            category_name=data['category_name'],
            parent_id=data.get('parent_id'),
            level=level,
            code_range_start=data.get('code_range_start'),
            code_range_end=data.get('code_range_end'),
            part_type=data.get('part_type'),
            type_identifier=data.get('type_identifier'),
            part_category=data.get('part_category'),
            classification=data.get('classification'),
            description=data.get('description'),
            sort_order=data.get('sort_order', 0)
        )
        
        db.session.add(category)
        db.session.commit()
        return category
    
    @staticmethod
    def generate_material_code_by_category(category_id: int, version: int = 0) -> str:
        """
        根据分类生成物料编码
        
        Args:
            category_id: 分类ID
            version: 版本号
            
        Returns:
            str: 生成的物料编码
        """
        
        category = MaterialCategory.query.get(category_id)
        if not category:
            raise ValueError("物料分类不存在")
        
        # 根据分类配置生成编码
        try:
            part_type = 'custom' if category.part_type == 1 else 'purchase'
            material_type = 'custom' if category.type_identifier == 0 else 'purchase'
            
            # 根据部件类别确定类型
            part_category = 'mechanical'
            if 30 <= category.part_category <= 34:
                part_category = 'optical'
            elif 35 <= category.part_category <= 39:
                part_category = 'electrical'
            
            return MaterialCodeService.generate_material_code(
                part_type=part_type,
                material_type=material_type,
                part_category=part_category,
                classification=category.classification or 0,
                version=version
            )
            
        except Exception as e:
            raise ValueError(f"编码生成失败: {str(e)}")
    
    @staticmethod
    def _create_material_supplier(material_id: int, supplier_data: Dict[str, Any]) -> MaterialSupplier:
        """创建物料供应商关联"""
        
        material_supplier = MaterialSupplier(
            material_id=material_id,
            supplier_id=supplier_data['supplier_id'],
            price=supplier_data['price'],
            currency=supplier_data.get('currency', 'CNY'),
            valid_from=datetime.fromisoformat(supplier_data['valid_from']) if supplier_data.get('valid_from') else None,
            valid_to=datetime.fromisoformat(supplier_data['valid_to']) if supplier_data.get('valid_to') else None,
            is_primary=supplier_data.get('is_primary', False),
            lead_time=supplier_data.get('lead_time'),
            min_order_qty=supplier_data.get('min_order_qty'),
            supplier_part_no=supplier_data.get('supplier_part_no'),
            remark=supplier_data.get('remark')
        )
        
        db.session.add(material_supplier)
        return material_supplier
