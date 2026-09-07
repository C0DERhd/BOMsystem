from app import db
from datetime import datetime
import json

class VisirayInventory(db.Model):
    """Visiray库存管理模型"""
    __tablename__ = 'inventory_management'
    __bind_key__ = 'visiray'
    
    goods_id = db.Column(db.BigInteger, primary_key=True)
    goods_name = db.Column(db.String(200), nullable=False)
    supplier = db.Column(db.String(200))
    product_model = db.Column(db.String(100))
    goods_type = db.Column(db.String(100))
    in_quantity = db.Column(db.Integer)
    out_quantity = db.Column(db.Integer)
    stock_quantity = db.Column(db.Integer)
    unit = db.Column(db.String(20))
    shelf_location = db.Column(db.String(50))
    in_record = db.Column(db.Text)
    out_record = db.Column(db.Text)
    attachments = db.Column(db.String(500))
    purchase_invoice = db.Column(db.String(200))
    invoice_info = db.Column(db.Text)
    parent_record = db.Column(db.BigInteger)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'goods_id': self.goods_id,
            'goods_name': self.goods_name,
            'supplier': self.supplier,
            'product_model': self.product_model,
            'goods_type': self.goods_type,
            'in_quantity': self.in_quantity,
            'out_quantity': self.out_quantity,
            'stock_quantity': self.stock_quantity,
            'unit': self.unit,
            'shelf_location': self.shelf_location,
            'in_record': self.in_record,
            'out_record': self.out_record,
            'attachments': self.attachments,
            'purchase_invoice': self.purchase_invoice,
            'invoice_info': self.invoice_info,
            'parent_record': self.parent_record
        }

class VisirayVersionInventory(db.Model):
    """按零件版本汇总的库存模型，一个版本对应一条总库存。"""
    __tablename__ = 'inventory_management_versioned'
    __bind_key__ = 'visiray'

    id = db.Column(db.BigInteger, primary_key=True)
    goods_id = db.Column(db.BigInteger, nullable=False)
    part_version_id = db.Column(db.BigInteger, nullable=False)
    goods_name = db.Column(db.String(200), nullable=False)
    supplier = db.Column(db.String(200))
    product_model = db.Column(db.String(100))
    goods_type = db.Column(db.String(100))
    in_quantity = db.Column(db.Integer)
    out_quantity = db.Column(db.Integer)
    stock_quantity = db.Column(db.Integer)
    unit = db.Column(db.String(20))
    shelf_location = db.Column(db.String(50))
    in_record = db.Column(db.Text)
    out_record = db.Column(db.Text)
    attachments = db.Column(db.String(500))
    purchase_invoice = db.Column(db.String(200))
    invoice_info = db.Column(db.Text)
    parent_record = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'goods_id': self.goods_id,
            'part_version_id': self.part_version_id,
            'goods_name': self.goods_name,
            'supplier': self.supplier,
            'product_model': self.product_model,
            'goods_type': self.goods_type,
            'in_quantity': self.in_quantity,
            'out_quantity': self.out_quantity,
            'stock_quantity': self.stock_quantity,
            'unit': self.unit,
            'shelf_location': self.shelf_location,
            'in_record': self.in_record,
            'out_record': self.out_record,
            'attachments': self.attachments,
            'purchase_invoice': self.purchase_invoice,
            'invoice_info': self.invoice_info,
            'parent_record': self.parent_record,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'inventory_type': 'versioned',
            'inventory_record_id': self.id,
        }

class VisirayStockInRecord(db.Model):
    """Visiray入库记录模型"""
    __tablename__ = 'stock_in_record'
    __bind_key__ = 'visiray'
    
    # 使用in_record作为主键
    in_record = db.Column(db.String(50), primary_key=True)
    goods_id = db.Column(db.BigInteger)
    supplier_name = db.Column(db.String(200))
    quantity = db.Column(db.Integer)
    unit = db.Column(db.String(20))
    in_date = db.Column(db.Date)
    operator = db.Column(db.String(50))
    shelf_location = db.Column(db.String(50))
    goods_type = db.Column(db.String(100))
    supplier = db.Column(db.String(200))
    product_model = db.Column(db.String(100))
    parent_record = db.Column(db.String(50))
    inbound_type = db.Column(db.String(20), default='入库')  # 添加入库类型字段，默认为'入库'
    related_voucher = db.Column(db.String(100))  # 修改为VARCHAR(100)类型，用于存储采购单号
    part_version_id = db.Column(db.BigInteger)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'in_record': self.in_record,
            'goods_id': self.goods_id,
            'supplier_name': self.supplier_name,
            'quantity': self.quantity,
            'unit': self.unit,
            'in_date': self.in_date.strftime('%Y-%m-%d') if self.in_date else None,
            'operator': self.operator,
            'shelf_location': self.shelf_location,
            'goods_type': self.goods_type,
            'supplier': self.supplier,
            'product_model': self.product_model,
            'parent_record': self.parent_record,
            'inbound_type': self.inbound_type,
            'related_voucher': self.related_voucher,  # 修改为直接返回采购单号
            'part_version_id': self.part_version_id
        }

class VisirayStockOutRecord(db.Model):
    """Visiray出库记录模型"""
    __tablename__ = 'stock_out_record'
    __bind_key__ = 'visiray'
    
    out_record_id = db.Column(db.BigInteger, primary_key=True)
    goods_id = db.Column(db.BigInteger)
    goods_name = db.Column(db.String(200))
    quantity = db.Column(db.Integer)
    out_date = db.Column(db.Date)
    operator = db.Column(db.String(50))
    shelf_location = db.Column(db.String(50))
    outbound_type = db.Column(db.String(20), default='出库')  # 添加出库类型字段，默认为'出库'
    part_version_id = db.Column(db.BigInteger)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'out_record_id': self.out_record_id,
            'goods_id': self.goods_id,
            'goods_name': self.goods_name,
            'quantity': self.quantity,
            'out_date': self.out_date.strftime('%Y-%m-%d') if self.out_date else None,
            'operator': self.operator,
            'shelf_location': self.shelf_location,
            'outbound_type': self.outbound_type,
            'part_version_id': self.part_version_id
        }

class VisirayPurchaseReceivingVoucher(db.Model):
    """Visiray采购入库单模型"""
    __tablename__ = 'purchase_receiving_voucher'
    __bind_key__ = 'visiray'
    
    # 根据实际数据库表结构调整
    id = db.Column(db.Integer, primary_key=True)  # 主键ID
    purchase_order_no = db.Column(db.String(50))  # 采购单号
    product_code = db.Column(db.String(50))  # 产品编码（对应货品编号）
    product_name = db.Column(db.String(100))  # 产品名称（对应货品名称）
    quantity = db.Column(db.Numeric(10, 2))  # 数量（对应采购数量）
    unit = db.Column(db.String(20))  # 单位
    product_type = db.Column(db.String(50))  # 产品类型（对应货品类型）
    unit_price = db.Column(db.Numeric(10, 2))  # 单价（对应采购单价）
    total_price = db.Column(db.Numeric(12, 2), server_default=db.text("quantity * unit_price"))  # 总价（计算字段）
    receiving_time = db.Column(db.DateTime)  # 收货时间（对应入库时间）
    status = db.Column(db.String(20))  # 状态
    supplier = db.Column(db.String(100))  # 供应商
    invoice_no = db.Column(db.String(50))  # 发票号（对应采购发票）- 修改为VARCHAR(50)类型，仅存储文件名
    contract_pdf = db.Column(db.String(50))  # 添加数据库中存在的contract_pdf字段 - 修改为VARCHAR(50)类型，仅存储文件名
    part_version_id = db.Column(db.BigInteger)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'purchase_order_no': self.purchase_order_no,
            'goods_id': self.product_code,  # 映射为货品编号
            'goods_name': self.product_name,  # 映射为货品名称
            'purchase_quantity': float(self.quantity) if self.quantity else None,  # 映射为采购数量
            'unit': self.unit,
            'goods_type': self.product_type,  # 映射为货品类型
            'purchase_price': float(self.unit_price) if self.unit_price else None,  # 映射为采购单价
            'total_price': float(self.total_price) if self.total_price else None,
            'inbound_time': self.receiving_time.strftime('%Y-%m-%d') if self.receiving_time else None,  # 映射为入库时间
            'status': self.status,
            'supplier': self.supplier,
            'purchase_invoice': self.invoice_no,  # 映射为采购发票文件名
            'contract_pdf': self.contract_pdf,  # 映射为入库合同文件名
            'part_version_id': self.part_version_id
        }

class VisirayPurchaseAttachment(db.Model):
    __tablename__ = 'purchase_order_attachments'
    __bind_key__ = 'visiray'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    purchase_order_no = db.Column(db.String(50), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(100))
    file_size = db.Column(db.BigInteger)
    uploaded_by = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'purchase_order_no': self.purchase_order_no,
            'original_filename': self.original_filename,
            'content_type': self.content_type,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class VisirayContractNumberRecord(db.Model):
    __tablename__ = 'contract_number_records'
    __bind_key__ = 'visiray'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False)
    seq = db.Column(db.Integer, nullable=False)
    contract_no = db.Column(db.String(50), nullable=False, unique=True)
    subject = db.Column(db.String(200), nullable=False)
    supplier = db.Column(db.String(200))
    related_order_no = db.Column(db.String(100))
    purchase_content = db.Column(db.Text)
    quantity = db.Column(db.Numeric(18, 4))
    amount = db.Column(db.Numeric(18, 2))
    attachment_file = db.Column(db.String(255))
    attachment_name = db.Column(db.String(255))
    remark = db.Column(db.Text)
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'seq': self.seq,
            'contract_no': self.contract_no,
            'subject': self.subject,
            'supplier': self.supplier,
            'related_order_no': self.related_order_no,
            'purchase_content': self.purchase_content,
            'quantity': float(self.quantity) if self.quantity is not None else None,
            'amount': float(self.amount) if self.amount is not None else None,
            'attachment_file': self.attachment_file,
            'attachment_name': self.attachment_name,
            'remark': self.remark,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class VisiraySupplierInformation(db.Model):
    """Visiray供应商信息表模型"""
    __tablename__ = 'supplier_information'
    __bind_key__ = 'visiray'
    
    # 根据实际数据库表结构调整
    id = db.Column(db.Integer, primary_key=True)  # 主键ID
    supplier_code = db.Column(db.String(50), unique=True)  # 供应商编号
    supplier_name = db.Column(db.String(200))  # 供应商名称
    phone = db.Column(db.String(30))  # 联系电话
    email = db.Column(db.String(150))  # 邮箱
    address = db.Column(db.String(300))  # 联系地址
    contact_person = db.Column(db.String(100))  # 联系人
    position = db.Column(db.String(100))  # 职务
    coordinator = db.Column(db.String(100))  # 协调人（对应对接人）
    purchase_voucher_ref = db.Column(db.String(50))  # 采购凭证参考（对应采购入库单）
    stock_in_record = db.Column(db.Text)  # 入库记录
    remarks = db.Column(db.Text)  # 备注
    operator_name = db.Column(db.String(100))  # 操作员名称
    created_at = db.Column(db.DateTime)  # 创建时间
    updated_at = db.Column(db.DateTime)  # 更新时间
    
    def to_dict(self):
        """转换为字典"""
        return {
            'supplier_code': self.supplier_code,
            'supplier_name': self.supplier_name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'contact_person': self.contact_person,
            'position': self.position,
            'liaison': self.coordinator,  # 映射为对接人
            'purchase_orders': self.purchase_voucher_ref,  # 映射为采购入库单
            'inbound_records': self.stock_in_record,  # 映射为入库记录
            'remark': self.remarks  # 映射为备注
        }

class VisirayPartNumber(db.Model):
    """Visiray零件号信息表模型"""
    __tablename__ = 'part_number'
    __bind_key__ = 'visiray'
    
    part_id = db.Column(db.String(50), primary_key=True, comment='零件号')
    category = db.Column(db.String(100), comment='零部件类别')
    main_type = db.Column(db.String(100), comment='大类')
    sub_type = db.Column(db.String(100), comment='小类')
    part_name = db.Column(db.String(200))
    unit = db.Column(db.String(20))
    standard_cost = db.Column(db.Numeric(12, 4), default=0.0000)
    remark = db.Column(db.String(500), comment='备注')
    current_version_id = db.Column(db.BigInteger, comment='当前默认版本ID')
    created_by = db.Column(db.BigInteger)
    created_by_name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'part_id': self.part_id,
            'category': self.category,
            'main_type': self.main_type,
            'sub_type': self.sub_type,
            'part_name': self.part_name,
            'unit': self.unit,
            'standard_cost': float(self.standard_cost) if self.standard_cost else 0,
            'remark': self.remark,
            'current_version_id': self.current_version_id,
            'created_by': self.created_by,
            'created_by_name': self.created_by_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class VisirayPartNumberVersion(db.Model):
    """零件号下的版本记录，版本号为手工输入的四位数字字符串。"""
    __tablename__ = 'part_number_versions'
    __bind_key__ = 'visiray'

    id = db.Column(db.BigInteger, primary_key=True)
    part_id = db.Column(db.String(50), nullable=False)
    version_no = db.Column(db.String(4), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    is_current = db.Column(db.Boolean, default=False)
    remark = db.Column(db.String(500))
    created_by = db.Column(db.BigInteger)
    created_by_name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'part_id': self.part_id,
            'version_no': self.version_no,
            'version_number': self.version_no,
            'status': self.status or 'active',
            'is_current': bool(self.is_current),
            'remark': self.remark,
            'created_by': self.created_by,
            'created_by_name': self.created_by_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class VisirayPartNumberRule(db.Model):
    """Configurable rule used by the part number application flow."""
    __tablename__ = 'part_number_rule'
    __bind_key__ = 'visiray'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rule_name = db.Column(db.String(100), nullable=False)
    prefix = db.Column(db.String(20), default='')
    config_json = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    remark = db.Column(db.String(500))
    created_by = db.Column(db.BigInteger)
    updated_by = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def get_config(self):
        try:
            return json.loads(self.config_json or '{}')
        except Exception:
            return {}

    def set_config(self, value):
        self.config_json = json.dumps(value or {}, ensure_ascii=False)

    def to_dict(self):
        return {
            'id': self.id,
            'rule_name': self.rule_name,
            'prefix': self.prefix or '',
            'config': self.get_config(),
            'is_active': bool(self.is_active),
            'remark': self.remark,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class VisirayUserAccount(db.Model):
    """Visiray用户账户模型"""
    __tablename__ = 'user_account'
    __bind_key__ = 'visiray'
    
    username = db.Column(db.String(50), nullable=False, comment='用户名')
    account = db.Column(db.String(50), primary_key=True, nullable=False, comment='账户')
    password = db.Column(db.String(255), nullable=False, comment='密码')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'username': self.username,
            'account': self.account
            # 注意：不返回密码字段
        }
