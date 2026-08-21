from datetime import datetime
from app import db

class Supplier(db.Model):
    """供应商模型"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.BigInteger, primary_key=True)
    supplier_code = db.Column(db.String(32), unique=True, nullable=False, comment='供应商代码')
    supplier_name = db.Column(db.String(128), nullable=False, comment='供应商名称')
    supplier_name_en = db.Column(db.String(128), comment='英文名称')
    
    # 联系信息
    contact_person = db.Column(db.String(64), comment='联系人')
    phone = db.Column(db.String(20), comment='电话')
    mobile = db.Column(db.String(20), comment='手机')
    fax = db.Column(db.String(20), comment='传真')
    email = db.Column(db.String(120), comment='邮箱')
    website = db.Column(db.String(255), comment='网站')
    
    # 地址信息
    country = db.Column(db.String(64), comment='国家')
    province = db.Column(db.String(64), comment='省份')
    city = db.Column(db.String(64), comment='城市')
    address = db.Column(db.Text, comment='详细地址')
    postal_code = db.Column(db.String(20), comment='邮政编码')
    
    # 企业信息
    legal_person = db.Column(db.String(64), comment='法人代表')
    registered_capital = db.Column(db.Numeric(15, 2), comment='注册资本')
    business_license = db.Column(db.String(64), comment='营业执照号')
    tax_number = db.Column(db.String(64), comment='税号')
    
    # 供应商分类
    supplier_type = db.Column(db.Enum('material', 'service', 'equipment', 'other', name='supplier_type'), 
                             default='material', comment='供应商类型')
    supplier_level = db.Column(db.Enum('A', 'B', 'C', 'D', name='supplier_level'), 
                              default='C', comment='供应商等级')
    
    # 认证信息
    iso_certification = db.Column(db.String(255), comment='ISO认证')
    quality_certification = db.Column(db.Text, comment='质量认证')
    
    # 财务信息
    payment_terms = db.Column(db.String(64), comment='付款条件')
    currency = db.Column(db.String(3), default='CNY', comment='结算币种')
    credit_limit = db.Column(db.Numeric(15, 2), comment='信用额度')
    
    # 交付信息
    lead_time = db.Column(db.Integer, comment='标准交期(天)')
    delivery_terms = db.Column(db.String(64), comment='交货条件')
    
    # 评估信息
    quality_rating = db.Column(db.Numeric(3, 2), comment='质量评分')
    delivery_rating = db.Column(db.Numeric(3, 2), comment='交期评分')
    service_rating = db.Column(db.Numeric(3, 2), comment='服务评分')
    overall_rating = db.Column(db.Numeric(3, 2), comment='综合评分')
    
    # 状态管理
    status = db.Column(db.Enum('active', 'inactive', 'blacklist', name='supplier_status'), 
                      default='active', comment='供应商状态')
    cooperation_status = db.Column(db.Enum('potential', 'cooperation', 'terminated', name='cooperation_status'), 
                                  default='potential', comment='合作状态')
    
    # 管理信息
    remark = db.Column(db.Text, comment='备注')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_by = db.Column(db.BigInteger, db.ForeignKey('users.id'), comment='创建人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<Supplier {self.supplier_name}>'
    
    def get_supplied_materials_count(self):
        """获取供应物料数量"""
        return self.material_suppliers.filter_by(status='active').count()
    
    def calculate_overall_rating(self):
        """计算综合评分"""
        ratings = [self.quality_rating, self.delivery_rating, self.service_rating]
        valid_ratings = [r for r in ratings if r is not None]
        if valid_ratings:
            self.overall_rating = sum(valid_ratings) / len(valid_ratings)
        return self.overall_rating
    
    def to_dict(self, include_materials=False):
        data = {
            'id': self.id,
            'supplier_code': self.supplier_code,
            'supplier_name': self.supplier_name,
            'supplier_name_en': self.supplier_name_en,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'mobile': self.mobile,
            'fax': self.fax,
            'email': self.email,
            'website': self.website,
            'country': self.country,
            'province': self.province,
            'city': self.city,
            'address': self.address,
            'postal_code': self.postal_code,
            'legal_person': self.legal_person,
            'registered_capital': float(self.registered_capital) if self.registered_capital else None,
            'business_license': self.business_license,
            'tax_number': self.tax_number,
            'supplier_type': self.supplier_type,
            'supplier_level': self.supplier_level,
            'iso_certification': self.iso_certification,
            'quality_certification': self.quality_certification,
            'payment_terms': self.payment_terms,
            'currency': self.currency,
            'credit_limit': float(self.credit_limit) if self.credit_limit else None,
            'lead_time': self.lead_time,
            'delivery_terms': self.delivery_terms,
            'quality_rating': float(self.quality_rating) if self.quality_rating else None,
            'delivery_rating': float(self.delivery_rating) if self.delivery_rating else None,
            'service_rating': float(self.service_rating) if self.service_rating else None,
            'overall_rating': float(self.overall_rating) if self.overall_rating else None,
            'status': self.status,
            'cooperation_status': self.cooperation_status,
            'remark': self.remark,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'materials_count': self.get_supplied_materials_count()
        }
        
        if include_materials:
            data['materials'] = [ms.to_dict() for ms in self.material_suppliers]
            
        return data