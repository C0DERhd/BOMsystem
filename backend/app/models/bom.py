from datetime import datetime
from datetime import timezone
from decimal import Decimal, InvalidOperation
import re
from app import db
from app.models.material import MaterialSupplier
from app.models.visiray import VisirayPartNumber, VisirayPartNumberVersion

def utc_isoformat(value):
    if not value:
        return None
    if value.tzinfo is None:
        return f"{value.isoformat()}Z"
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def format_bom_version(value):
    text = str(value or '').strip()
    if not text:
        return '0001'
    if re.fullmatch(r'\d{1,4}', text):
        return text.zfill(4)
    if re.fullmatch(r'\d+(?:\.\d+)?', text):
        try:
            number = int(Decimal(text))
            if 0 <= number <= 9999:
                return str(number).zfill(4)
        except (InvalidOperation, ValueError):
            pass
    return text


class BOM(db.Model):
    """BOM主表模型"""
    __tablename__ = 'boms'
    
    id = db.Column(db.BigInteger, primary_key=True)
    bom_code = db.Column(db.String(32), unique=True, nullable=False, comment='BOM编码')
    product_name = db.Column(db.String(128), nullable=False, comment='产品名称')
    product_model = db.Column(db.String(64), comment='产品型号')
    product_spec = db.Column(db.Text, comment='产品规格')
    
    # 版本信息
    version = db.Column(db.String(16), nullable=False, default='0001', comment='版本号')
    parent_bom_id = db.Column(db.BigInteger, db.ForeignKey('boms.id'), comment='父BOM ID')
    
    # 状态管理
    status = db.Column(db.Enum('draft', 'active', 'inactive', 'obsolete', name='bom_status'), 
                      default='draft', comment='BOM状态')
    
    # 数量和单位
    base_quantity = db.Column(db.Numeric(12, 4), default=1.0000, comment='基础数量')
    unit = db.Column(db.String(20), default='个', comment='单位')
    
    # 成本信息
    total_cost = db.Column(db.Numeric(12, 4), default=0.0000, comment='总成本')
    material_cost = db.Column(db.Numeric(12, 4), default=0.0000, comment='材料成本')
    labor_cost = db.Column(db.Numeric(12, 4), default=0.0000, comment='人工成本')
    overhead_cost = db.Column(db.Numeric(12, 4), default=0.0000, comment='制造费用')
    
    # 工艺信息
    process_route = db.Column(db.Text, comment='工艺路线')
    lead_time = db.Column(db.Integer, comment='生产周期(天)')
    
    # 管理信息
    effective_date = db.Column(db.DateTime, comment='生效日期')
    expiry_date = db.Column(db.DateTime, comment='失效日期')
    remark = db.Column(db.Text, comment='备注')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, comment='是否已删除')
    deleted_at = db.Column(db.DateTime, comment='删除时间')
    deleted_by = db.Column(db.BigInteger, db.ForeignKey('users.id'), comment='删除人ID')
    
    # 审核信息
    approved_by = db.Column(db.BigInteger, db.ForeignKey('users.id'), comment='审核人ID')
    approved_at = db.Column(db.DateTime, comment='审核时间')
    
    # 创建信息
    created_by = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, comment='创建人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    parent_bom = db.relationship('BOM', remote_side=[id], backref='child_boms')
    bom_items = db.relationship('BOMItem', backref='bom', lazy='dynamic', 
                               cascade='all, delete-orphan', order_by='BOMItem.sort_order',
                               foreign_keys='BOMItem.bom_id')
    versions = db.relationship('BOMVersion', backref='bom', lazy='dynamic', 
                              cascade='all, delete-orphan')
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<BOM {self.bom_code}>'

    def is_cost_excluded(self):
        return self.is_deleted or self.status in {'inactive', 'obsolete'}
    
    def get_tree_structure(self, level=0, visited=None):
        """Return BOM items as a parent/child tree."""
        if self.is_deleted:
            return []
        visited = set(visited or [])
        if self.id in visited:
            return []
        visited.add(self.id)

        all_items = self.bom_items.order_by('level', 'sort_order', 'id').all()
        children_by_parent = {}
        for item in all_items:
            children_by_parent.setdefault(item.parent_item_id, []).append(item)

        def build_nodes(parent_item_id=None):
            nodes = []
            for item in children_by_parent.get(parent_item_id, []):
                item_data = item.to_dict()
                item_data['children'] = build_nodes(item.id)
                if item.sub_bom and not item_data['children']:
                    item_data['children'] = item.sub_bom.get_tree_structure(level + 1, visited.copy())
                nodes.append(item_data)
            return nodes

        return build_nodes(None)

    def calculate_cost(self, visited=None):
        """计算BOM总成本，统一转为 float，避免 Numeric 字段返回 Decimal 后和旧 float 默认值混算。"""
        visited = set(visited or [])
        if self.id in visited:
            return 0.0
        if self.is_cost_excluded():
            self.material_cost = 0.0
            self.total_cost = 0.0
            return 0.0
        visited.add(self.id)

        def to_float(value):
            if value is None:
                return 0.0
            return float(value)

        root_items = (
            self.bom_items
            .filter(BOMItem.parent_item_id.is_(None))
            .order_by(BOMItem.sort_order, BOMItem.id)
            .all()
        )
        if not root_items:
            root_items = self.bom_items.order_by(BOMItem.sort_order, BOMItem.id).all()

        total = 0.0
        for item in root_items:
            total += item.get_item_cost(visited.copy())

        self.material_cost = total
        self.total_cost = total + to_float(self.labor_cost) + to_float(self.overhead_cost)
        return self.total_cost
    
    def create_version(self, version_note=''):
        """创建新版本"""
        version_count = self.versions.count()
        new_version = BOMVersion(
            bom_id=self.id,
            version_number=f"{format_bom_version(self.version)}-{version_count + 1:04d}",
            version_note=version_note,
            bom_data=self.to_dict(include_items=True),
            created_by=self.created_by
        )
        db.session.add(new_version)
        return new_version
    
    def to_dict(self, include_items=False, include_tree=False):
        def to_float(value, default=0):
            if value is None:
                return default
            return float(value)

        data = {
            'id': self.id,
            'bom_code': self.bom_code,
            'product_name': self.product_name,
            'product_model': self.product_model,
            'product_spec': self.product_spec,
            'version': format_bom_version(self.version),
            'parent_bom_id': self.parent_bom_id,
            'status': self.status,
            'base_quantity': to_float(self.base_quantity),
            'unit': self.unit,
            'total_cost': to_float(self.total_cost),
            'material_cost': to_float(self.material_cost),
            'labor_cost': to_float(self.labor_cost),
            'overhead_cost': to_float(self.overhead_cost),
            'process_route': self.process_route,
            'lead_time': self.lead_time,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'remark': self.remark,
            'is_active': self.is_active,
            'is_deleted': self.is_deleted,
            'deleted_at': utc_isoformat(self.deleted_at),
            'deleted_by': self.deleted_by,
            'approved_by': self.approved_by,
            'approved_at': utc_isoformat(self.approved_at),
            'created_by': self.created_by,
            'created_at': utc_isoformat(self.created_at),
            'updated_at': utc_isoformat(self.updated_at),
        }
        
        if include_items:
            items = []
            for item in self.bom_items.order_by('sort_order'):
                try:
                    items.append(item.to_dict())
                except Exception as e:
                    items.append({
                        'id': item.id,
                        'bom_id': item.bom_id,
                        'material_id': item.material_id,
                        'material_code': item._display_material_code(),
                        'part_version_id': item.part_version_id,
                        'material_name': item.material.material_name if item.material else None,
                        'sub_bom_id': item.sub_bom_id,
                        'sub_bom_code': item.sub_bom.bom_code if item.sub_bom else None,
                        'parent_item_id': item.parent_item_id,
                        'level': item.level,
                        'sort_order': item.sort_order,
                        'quantity': to_float(item.quantity),
                        'unit': item.unit or (item.material.unit if item.material else '个'),
                        'load_warning': f'该明细部分关联数据异常: {str(e)}',
                    })
            data['items'] = items
        
        if include_tree:
            data['tree_structure'] = self.get_tree_structure()
            
        return data

class BOMItem(db.Model):
    """BOM明细项模型"""
    __tablename__ = 'bom_items'
    
    id = db.Column(db.BigInteger, primary_key=True)
    bom_id = db.Column(db.BigInteger, db.ForeignKey('boms.id'), nullable=False, comment='BOM ID')
    material_id = db.Column(db.BigInteger, db.ForeignKey('materials.id'), comment='物料ID')
    part_version_id = db.Column(db.BigInteger, comment='零件版本ID')
    sub_bom_id = db.Column(db.BigInteger, db.ForeignKey('boms.id'), comment='子BOM ID')
    parent_item_id = db.Column(db.BigInteger, db.ForeignKey('bom_items.id'), comment='父项ID')
    
    # 层级和排序
    level = db.Column(db.Integer, default=1, comment='层级')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    item_no = db.Column(db.String(20), comment='项目号')
    
    # 数量信息
    quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='数量')
    unit = db.Column(db.String(20), comment='单位')
    
    # 物料属性
    is_key_material = db.Column(db.Boolean, default=False, comment='是否关键物料')
    is_optional = db.Column(db.Boolean, default=False, comment='是否可选物料')
    usage_rate = db.Column(db.Numeric(5, 4), default=1.0000, comment='损耗率')
    selected_supplier_id = db.Column(db.BigInteger, db.ForeignKey('material_suppliers.id'), comment='选中的物料供应商报价ID')
    selected_supplier_price = db.Column(db.Numeric(12, 4), comment='选中供应商价格')
    
    # 替代物料
    substitute_group = db.Column(db.String(32), comment='替代组')
    substitute_priority = db.Column(db.Integer, default=1, comment='替代优先级')
    
    # 工艺信息
    process_step = db.Column(db.String(64), comment='工序')
    assembly_note = db.Column(db.Text, comment='装配说明')
    
    # 管理信息
    effective_date = db.Column(db.DateTime, comment='生效日期')
    expiry_date = db.Column(db.DateTime, comment='失效日期')
    remark = db.Column(db.Text, comment='备注')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    sub_bom = db.relationship('BOM', foreign_keys=[sub_bom_id])
    parent_item = db.relationship('BOMItem', remote_side=[id], backref='child_items')
    selected_supplier = db.relationship('MaterialSupplier', foreign_keys=[selected_supplier_id])
    
    def __repr__(self):
        return f'<BOMItem {self.id}>'
    
    @staticmethod
    def _to_float(value):
        if value is None:
            return 0.0
        return float(value)

    def get_own_cost(self, visited=None):
        """计算当前明细自身成本，不包含同一BOM下的子节点。"""
        quantity = self._to_float(self.quantity)
        usage_rate = self._to_float(self.usage_rate or 1)
        if self.material:
            price = self._to_float(self.get_unit_price())
            return quantity * price * usage_rate
        if self.sub_bom:
            if self.sub_bom.is_cost_excluded():
                return 0.0
            return quantity * self._to_float(self.sub_bom.calculate_cost(visited)) * usage_rate
        return 0.0

    def get_unit_price(self):
        if not self.material:
            return 0.0
        if self.selected_supplier_price is not None:
            return self.selected_supplier_price
        if self.selected_supplier and self.selected_supplier.status == 'active':
            return self.selected_supplier.price
        default_supplier = self.material.get_default_supplier(self.part_version_id)
        if default_supplier:
            return default_supplier.price
        return 0.0

    def get_supplier_options(self):
        if not self.material:
            return []
        return [
            supplier.to_dict()
            for supplier in self.material.get_supplier_options(self.part_version_id)
        ]

    def get_item_cost(self, visited=None):
        """计算明细树成本：自身成本 + 按父项用量折算后的子节点成本。"""
        if self.bom and self.bom.is_cost_excluded():
            return 0.0
        total = self.get_own_cost(visited)
        children = sorted(
            list(self.child_items or []),
            key=lambda item: ((item.sort_order or 0), item.id or 0)
        )
        child_total = 0.0
        for child in children:
            child_total += child.get_item_cost(visited.copy() if visited else None)
        return total + (self._to_float(self.quantity or 1) * child_total)

    def _display_material_code(self):
        if self.material and self.material.visiray_part_id:
            return self.material.visiray_part_id
        if self.material and self.material.remark and self.material.remark.startswith('VISIRAY_PART_ID:'):
            return self.material.remark.split(':', 1)[1]
        return self.material.material_code if self.material else None

    def _part_version_options(self):
        part_id = self._display_material_code()
        if not part_id:
            return []
        part = VisirayPartNumber.query.get(part_id)
        if not part:
            return []
        versions = (
            VisirayPartNumberVersion.query
            .filter_by(part_id=part.part_id)
            .order_by(VisirayPartNumberVersion.is_current.desc(), VisirayPartNumberVersion.version_no.desc())
            .all()
        )
        return [
            {
                'id': item.id,
                'part_id': item.part_id,
                'version_no': item.version_no,
                'version_number': item.version_no,
                'status': item.status or 'active',
                'is_current': bool(item.is_current),
            }
            for item in versions
        ]

    def to_dict(self):
        def to_float(value, default=0):
            if value is None:
                return default
            return float(value)

        version = None
        if self.part_version_id:
            try:
                version = VisirayPartNumberVersion.query.get(self.part_version_id)
            except Exception:
                version = None

        supplier_options = []
        try:
            supplier_options = self.get_supplier_options()
        except Exception:
            supplier_options = []

        version_options = []
        try:
            version_options = self._part_version_options()
        except Exception:
            version_options = []

        selected_supplier_name = None
        try:
            if self.selected_supplier and self.selected_supplier.supplier:
                selected_supplier_name = self.selected_supplier.supplier.supplier_name
        except Exception:
            selected_supplier_name = None

        try:
            selected_supplier_price = to_float(self.get_unit_price())
        except Exception:
            selected_supplier_price = 0

        try:
            item_cost = float(self.get_item_cost())
        except Exception:
            item_cost = 0

        return {
            'id': self.id,
            'bom_id': self.bom_id,
            'item_type': 'part' if self.material_id else ('sub_bom' if self.sub_bom_id else None),
            'material_id': self.material_id,
            'material_code': self._display_material_code(),
            'part_version_id': self.part_version_id,
            'version_no': version.version_no if version else None,
            'version_status': version.status if version else None,
            'version_options': version_options,
            'material_name': self.material.material_name if self.material else None,
            'sub_bom_id': self.sub_bom_id,
            'sub_bom_code': self.sub_bom.bom_code if self.sub_bom else None,
            'sub_bom_name': self.sub_bom.product_name if self.sub_bom else None,
            'sub_bom_status': self.sub_bom.status if self.sub_bom else None,
            'is_cost_excluded': bool(self.sub_bom and self.sub_bom.is_cost_excluded()),
            'parent_item_id': self.parent_item_id,
            'level': self.level,
            'sort_order': self.sort_order,
            'item_no': self.item_no,
            'quantity': to_float(self.quantity),
            'unit': self.unit or (self.material.unit if self.material else '个'),
            'is_key_material': self.is_key_material,
            'is_optional': self.is_optional,
            'usage_rate': to_float(self.usage_rate),
            'selected_supplier_id': self.selected_supplier_id,
            'selected_supplier_name': selected_supplier_name,
            'selected_supplier_price': selected_supplier_price,
            'supplier_options': supplier_options,
            'has_multiple_suppliers': len(supplier_options) > 1,
            'substitute_group': self.substitute_group,
            'substitute_priority': self.substitute_priority,
            'process_step': self.process_step,
            'assembly_note': self.assembly_note,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'remark': self.remark,
            'is_active': self.is_active,
            'item_cost': item_cost
        }

class BOMVersion(db.Model):
    """BOM版本模型"""
    __tablename__ = 'bom_versions'
    
    id = db.Column(db.BigInteger, primary_key=True)
    bom_id = db.Column(db.BigInteger, db.ForeignKey('boms.id'), nullable=False, comment='BOM ID')
    version_number = db.Column(db.String(16), nullable=False, comment='版本号')
    version_note = db.Column(db.Text, comment='版本说明')
    
    # 版本数据快照
    bom_data = db.Column(db.JSON, comment='BOM数据快照')
    
    # 变更信息
    change_type = db.Column(db.Enum('create', 'update', 'delete', name='change_type'), 
                           default='create', comment='变更类型')
    change_reason = db.Column(db.Text, comment='变更原因')
    
    # 管理信息
    is_current = db.Column(db.Boolean, default=False, comment='是否当前版本')
    created_by = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, comment='创建人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<BOMVersion {self.version_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'bom_id': self.bom_id,
            'version_number': self.version_number,
            'version_note': self.version_note,
            'change_type': self.change_type,
            'change_reason': self.change_reason,
            'is_current': self.is_current,
            'created_by': self.created_by,
            'creator_name': self.creator.name if self.creator else None,
            'created_at': utc_isoformat(self.created_at)
        }






