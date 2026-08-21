from datetime import datetime
from app import db

class MaterialCategory(db.Model):
    """物料分类模型"""
    __tablename__ = 'material_categories'
    
    id = db.Column(db.BigInteger, primary_key=True)
    category_code = db.Column(db.String(10), unique=True, nullable=False, comment='分类代码')
    category_name = db.Column(db.String(64), nullable=False, comment='分类名称')
    parent_id = db.Column(db.BigInteger, db.ForeignKey('material_categories.id'), comment='父分类ID')
    level = db.Column(db.Integer, default=1, comment='分类层级')
    
    # 编码范围配置
    code_range_start = db.Column(db.Integer, comment='编码范围起始值')
    code_range_end = db.Column(db.Integer, comment='编码范围结束值')
    next_sequence = db.Column(db.Integer, default=1, comment='下一个可用流水号')
    
    # 分类属性
    part_type = db.Column(db.Integer, comment='零部件大类(1-2位)')
    type_identifier = db.Column(db.Integer, comment='定制/外购标识(3位)')
    part_category = db.Column(db.Integer, comment='部件类别(4-5位)')
    classification = db.Column(db.Integer, comment='分类号(6-7位)')
    
    description = db.Column(db.Text, comment='分类描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    parent = db.relationship('MaterialCategory', remote_side=[id], backref='children')
    materials = db.relationship('Material', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<MaterialCategory {self.category_name}>'
    
    def get_next_sequence(self):
        """获取并更新下一个序列号"""
        current = self.next_sequence
        self.next_sequence += 1
        db.session.commit()
        return current
    
    def to_dict(self, include_children=False):
        data = {
            'id': self.id,
            'category_code': self.category_code,
            'category_name': self.category_name,
            'parent_id': self.parent_id,
            'level': self.level,
            'part_type': self.part_type,
            'type_identifier': self.type_identifier,
            'part_category': self.part_category,
            'classification': self.classification,
            'description': self.description,
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }
        if include_children:
            data['children'] = [child.to_dict() for child in self.children]
        return data

class Material(db.Model):
    """物料模型"""
    __tablename__ = 'materials'
    
    id = db.Column(db.BigInteger, primary_key=True)
    visiray_part_id = db.Column(db.String(50), unique=True, comment='关联visiray.part_number.part_id')
    material_code = db.Column(db.String(12), unique=True, nullable=False, comment='12位物料编码')
    material_name = db.Column(db.String(128), nullable=False, comment='物料名称')
    specification = db.Column(db.Text, comment='规格型号')
    unit = db.Column(db.String(20), nullable=False, default='个', comment='单位')
    
    # 分类信息
    category_id = db.Column(db.BigInteger, db.ForeignKey('material_categories.id'), comment='分类ID')
    
    # 编码解析字段
    code_category = db.Column(db.Integer, comment='1-2位：零部件大类')
    code_type = db.Column(db.Integer, comment='3位：定制/外购标识')
    code_part_type = db.Column(db.Integer, comment='4-5位：部件类别')
    code_classification = db.Column(db.Integer, comment='6-7位：分类号')
    code_sequence = db.Column(db.Integer, comment='8-11位：零件顺序号')
    code_version = db.Column(db.Integer, comment='12位：版本号')
    
    # 成本信息
    standard_cost = db.Column(db.Numeric(12, 4), default=0.0000, comment='标准成本')
    currency = db.Column(db.String(3), default='CNY', comment='币种')
    
    # 物料属性
    material_type = db.Column(db.Enum('custom', 'purchase', name='material_type'), comment='物料类型')
    status = db.Column(db.Enum('active', 'inactive', 'obsolete', name='material_status'), 
                      default='active', comment='物料状态')
    
    # 库存信息
    safety_stock = db.Column(db.Numeric(12, 4), default=0.0000, comment='安全库存')
    current_stock = db.Column(db.Numeric(12, 4), default=0.0000, comment='当前库存')
    
    # 技术参数
    weight = db.Column(db.Numeric(10, 4), comment='重量(kg)')
    volume = db.Column(db.Numeric(10, 4), comment='体积(m³)')
    color = db.Column(db.String(50), comment='颜色')
    material_grade = db.Column(db.String(50), comment='材料牌号')
    
    # 管理信息
    remark = db.Column(db.Text, comment='备注')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_by = db.Column(db.BigInteger, db.ForeignKey('users.id'), comment='创建人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    suppliers = db.relationship('MaterialSupplier', backref='material', lazy='dynamic', cascade='all, delete-orphan')
    bom_items = db.relationship('BOMItem', backref='material', lazy='dynamic')
    
    def __repr__(self):
        return f'<Material {self.material_code}>'
    
    def get_supplier_options(self, part_version_id=None):
        """获取报价选项，版本报价优先，通用报价作为回退。"""
        query = self.suppliers.filter_by(status='active')
        if part_version_id:
            exact = query.filter_by(part_version_id=part_version_id).order_by(
                MaterialSupplier.is_primary.desc(), MaterialSupplier.id.asc()
            ).all()
            generic = query.filter(
                MaterialSupplier.part_version_id.is_(None)
            ).order_by(
                MaterialSupplier.is_primary.desc(), MaterialSupplier.id.asc()
            ).all()
            return exact + generic
        return query.filter(
            MaterialSupplier.part_version_id.is_(None)
        ).order_by(
            MaterialSupplier.is_primary.desc(), MaterialSupplier.id.asc()
        ).all()

    def get_versioned_supplier_options(self, part_version_id=None):
        """兼容旧调用：返回版本优先的报价列表。"""
        return self.get_supplier_options(part_version_id)

    def get_primary_supplier(self, part_version_id=None):
        """获取指定版本或通用报价中的主供应商。"""
        return next(
            (
                supplier for supplier in self.get_supplier_options(part_version_id)
                if supplier.is_primary
            ),
            None,
        )

    def get_default_supplier(self, part_version_id=None):
        """获取默认计价供应商：版本报价优先，其次使用通用报价。"""
        options = self.get_supplier_options(part_version_id)
        return options[0] if options else None

    def get_latest_price(self, part_version_id=None):
        """获取指定版本的最新价格。"""
        supplier = self.get_default_supplier(part_version_id)
        return supplier.price if supplier else self.standard_cost
    
    def parse_material_code(self):
        """解析物料编码"""
        if len(self.material_code) == 12:
            self.code_category = int(self.material_code[0:2])
            self.code_type = int(self.material_code[2:3])
            self.code_part_type = int(self.material_code[3:5])
            self.code_classification = int(self.material_code[5:7])
            self.code_sequence = int(self.material_code[7:11])
            self.code_version = int(self.material_code[11:12])
    
    def to_dict(self, include_suppliers=False):
        data = {
            'id': self.id,
            'material_code': self.material_code,
            'visiray_part_id': self.visiray_part_id,
            'material_name': self.material_name,
            'specification': self.specification,
            'unit': self.unit,
            'category_id': self.category_id,
            'category_name': self.category.category_name if self.category else None,
            'standard_cost': float(self.standard_cost) if self.standard_cost else 0,
            'currency': self.currency,
            'material_type': self.material_type,
            'status': self.status,
            'safety_stock': float(self.safety_stock) if self.safety_stock else 0,
            'current_stock': float(self.current_stock) if self.current_stock else 0,
            'weight': float(self.weight) if self.weight else None,
            'volume': float(self.volume) if self.volume else None,
            'color': self.color,
            'material_grade': self.material_grade,
            'remark': self.remark,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }
        if include_suppliers:
            data['suppliers'] = [s.to_dict() for s in self.suppliers]
        return data

class MaterialSupplier(db.Model):
    """物料供应商关联模型"""
    __tablename__ = 'material_suppliers'
    
    id = db.Column(db.BigInteger, primary_key=True)
    material_id = db.Column(db.BigInteger, db.ForeignKey('materials.id'), nullable=False)
    supplier_id = db.Column(db.BigInteger, db.ForeignKey('suppliers.id'), nullable=False)
    part_version_id = db.Column(db.BigInteger, comment='零件版本ID，空值表示零件号通用报价')
    
    # 价格信息
    price = db.Column(db.Numeric(12, 4), nullable=False, comment='采购价格')
    currency = db.Column(db.String(3), default='CNY', comment='币种')
    price_date = db.Column(db.DateTime, default=datetime.utcnow, comment='报价日期')
    valid_from = db.Column(db.DateTime, comment='价格生效日期')
    valid_to = db.Column(db.DateTime, comment='价格失效日期')
    
    # 供应商属性
    is_primary = db.Column(db.Boolean, default=False, comment='是否主供应商')
    lead_time = db.Column(db.Integer, comment='交期(天)')
    min_order_qty = db.Column(db.Numeric(12, 4), comment='最小订购量')
    supplier_part_no = db.Column(db.String(64), comment='供应商料号')
    
    # 管理信息
    status = db.Column(db.Enum('active', 'inactive', name='supplier_status'), 
                      default='active', comment='状态')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    supplier = db.relationship('Supplier', backref='material_suppliers')
    
    def __repr__(self):
        return f'<MaterialSupplier {self.material_id}-{self.supplier_id}-{self.part_version_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'material_id': self.material_id,
            'supplier_id': self.supplier_id,
            'part_version_id': self.part_version_id,
            'supplier_name': self.supplier.supplier_name if self.supplier else None,
            'price': float(self.price) if self.price is not None else 0,
            'currency': self.currency,
            'price_date': self.price_date.isoformat() if self.price_date else None,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_to': self.valid_to.isoformat() if self.valid_to else None,
            'is_primary': self.is_primary,
            'lead_time': self.lead_time,
            'min_order_qty': float(self.min_order_qty) if self.min_order_qty else None,
            'supplier_part_no': self.supplier_part_no,
            'status': self.status,
            'remark': self.remark
        }
