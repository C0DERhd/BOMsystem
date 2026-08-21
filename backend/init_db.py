#!/usr/bin/env python
"""
数据库初始化脚本
创建基础数据和示例数据
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
from dotenv import load_dotenv
try:
    load_dotenv(encoding='utf-8')
except:
    load_dotenv()

from app import create_app, db
from app.models import User, Role, Permission, MaterialCategory, Material, Supplier, BOM

class Config:
    """配置基类"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    # 直接指定数据库URL，避免环境变量编码问题
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://test:Visiray88!!@192.168.0.2/bom_dev'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """生产环境配置"""
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def init_permissions():
    """初始化权限数据"""
    permissions_data = [
        # 用户管理权限
        {'name': '用户查看', 'code': 'user_read', 'resource': 'user', 'action': 'read'},
        {'name': '用户创建', 'code': 'user_create', 'resource': 'user', 'action': 'create'},
        {'name': '用户更新', 'code': 'user_update', 'resource': 'user', 'action': 'update'},
        {'name': '用户删除', 'code': 'user_delete', 'resource': 'user', 'action': 'delete'},
        {'name': '角色分配', 'code': 'user_role_assign', 'resource': 'user', 'action': 'assign'},
        
        # 物料管理权限
        {'name': '物料查看', 'code': 'material_read', 'resource': 'material', 'action': 'read'},
        {'name': '物料创建', 'code': 'material_create', 'resource': 'material', 'action': 'create'},
        {'name': '物料更新', 'code': 'material_update', 'resource': 'material', 'action': 'update'},
        {'name': '物料删除', 'code': 'material_delete', 'resource': 'material', 'action': 'delete'},
        {'name': '物料分类管理', 'code': 'material_category_manage', 'resource': 'material', 'action': 'category'},
        
        # BOM管理权限
        {'name': 'BOM查看', 'code': 'bom_read', 'resource': 'bom', 'action': 'read'},
        {'name': 'BOM创建', 'code': 'bom_create', 'resource': 'bom', 'action': 'create'},
        {'name': 'BOM更新', 'code': 'bom_update', 'resource': 'bom', 'action': 'update'},
        {'name': 'BOM删除', 'code': 'bom_delete', 'resource': 'bom', 'action': 'delete'},
        {'name': 'BOM审核', 'code': 'bom_approve', 'resource': 'bom', 'action': 'approve'},
        
        # 供应商管理权限
        {'name': '供应商查看', 'code': 'supplier_read', 'resource': 'supplier', 'action': 'read'},
        {'name': '供应商创建', 'code': 'supplier_create', 'resource': 'supplier', 'action': 'create'},
        {'name': '供应商更新', 'code': 'supplier_update', 'resource': 'supplier', 'action': 'update'},
        {'name': '供应商删除', 'code': 'supplier_delete', 'resource': 'supplier', 'action': 'delete'},
        
        # 系统管理权限
        {'name': '系统配置', 'code': 'system_config', 'resource': 'system', 'action': 'config'},
        {'name': '数据导入导出', 'code': 'data_import_export', 'resource': 'system', 'action': 'import_export'},
        # 采购附件权限
        {'name': '采购附件查看', 'code': 'purchase_attachment_read', 'resource': 'purchase', 'action': 'read'},
        {'name': '采购附件上传', 'code': 'purchase_attachment_create', 'resource': 'purchase', 'action': 'create'},
        {'name': '采购附件删除', 'code': 'purchase_attachment_delete', 'resource': 'purchase', 'action': 'delete'},
        {'name': '采购附件下载', 'code': 'purchase_attachment_download', 'resource': 'purchase', 'action': 'download'},
    ]
    
    for perm_data in permissions_data:
        permission = Permission.query.filter_by(code=perm_data['code']).first()
        if not permission:
            permission = Permission(**perm_data)
            db.session.add(permission)
    
    db.session.commit()
    print("权限数据初始化完成")

def init_roles():
    """初始化角色数据"""
    # 获取所有权限
    all_permissions = Permission.query.all()
    
    # 管理员角色 - 拥有所有权限
    admin_role = Role.query.filter_by(code='admin').first()
    if not admin_role:
        admin_role = Role(
            name='管理员',
            code='admin',
            description='系统管理员，拥有所有权限'
        )
        admin_role.permissions = all_permissions
        db.session.add(admin_role)
    
    # BOM管理员角色
    bom_admin_role = Role.query.filter_by(code='bom_admin').first()
    if not bom_admin_role:
        bom_admin_role = Role(
            name='BOM管理员',
            code='bom_admin',
            description='BOM管理员，负责BOM和物料管理'
        )
        # 分配相关权限
        bom_permissions = Permission.query.filter(
            Permission.resource.in_(['bom', 'material', 'supplier'])
        ).all()
        bom_admin_role.permissions = bom_permissions
        db.session.add(bom_admin_role)
    
    # 普通用户角色
    user_role = Role.query.filter_by(code='user').first()
    if not user_role:
        user_role = Role(
            name='普通用户',
            code='user',
            description='普通用户，只有查看权限'
        )
        # 只分配查看权限
        read_permissions = Permission.query.filter(
            Permission.action == 'read'
        ).all()
        user_role.permissions = read_permissions
        db.session.add(user_role)
    
    db.session.commit()
    print("角色数据初始化完成")

def init_users():
    """初始化用户数据"""
    # 创建管理员用户
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_role = Role.query.filter_by(code='admin').first()
        admin_user = User(
            username='admin',
            email='admin@example.com',
            name='系统管理员',
            is_active=True,
            is_verified=True
        )
        admin_user.set_password('admin123')
        if admin_role:
            admin_user.roles.append(admin_role)
        db.session.add(admin_user)
    
    # 创建测试用户
    test_user = User.query.filter_by(username='test').first()
    if not test_user:
        user_role = Role.query.filter_by(code='user').first()
        test_user = User(
            username='test',
            email='test@example.com',
            name='测试用户',
            department='研发部',
            position='工程师',
            is_active=True,
            is_verified=True
        )
        test_user.set_password('test123')
        if user_role:
            test_user.roles.append(user_role)
        db.session.add(test_user)
    
    db.session.commit()
    print("用户数据初始化完成")

def init_material_categories():
    """初始化物料分类数据"""
    categories_data = [
        # 定制件分类
        {
            'category_code': 'CUSTOM_MECH',
            'category_name': '定制机械件',
            'part_type': 1,
            'type_identifier': 0,
            'part_category': 20,
            'classification': 0,
            'description': '定制生产的机械零件'
        },
        {
            'category_code': 'CUSTOM_STRUCT',
            'category_name': '定制结构件',
            'part_type': 1,
            'type_identifier': 0,
            'part_category': 20,
            'classification': 1,
            'description': '定制结构类零件'
        },
        
        # 外购件分类
        {
            'category_code': 'PURCHASE_MECH',
            'category_name': '外购机械件',
            'part_type': 2,
            'type_identifier': 5,
            'part_category': 20,
            'classification': 30,
            'description': '采购的标准机械件'
        },
        {
            'category_code': 'PURCHASE_FASTENER',
            'category_name': '外购紧固件',
            'part_type': 2,
            'type_identifier': 5,
            'part_category': 22,
            'classification': 10,
            'description': '采购的紧固件(螺栓、螺母等)'
        },
    ]
    
    for cat_data in categories_data:
        category = MaterialCategory.query.filter_by(category_code=cat_data['category_code']).first()
        if not category:
            category = MaterialCategory(**cat_data)
            db.session.add(category)
    
    db.session.commit()
    print("物料分类数据初始化完成")

def init_sample_data():
    """初始化示例数据"""
    # 创建示例供应商
    suppliers_data = [
        {
            'supplier_code': 'SUP001',
            'supplier_name': '北京精密机械有限公司',
            'contact_person': '张经理',
            'phone': '010-12345678',
            'email': 'zhang@bjjm.com',
            'city': '北京',
            'supplier_type': 'material',
            'supplier_level': 'A',
            'currency': 'CNY'
        },
        {
            'supplier_code': 'SUP002',
            'supplier_name': '上海标准件厂',
            'contact_person': '李经理',
            'phone': '021-87654321',
            'email': 'li@shbzj.com',
            'city': '上海',
            'supplier_type': 'material',
            'supplier_level': 'B',
            'currency': 'CNY'
        }
    ]
    
    for supplier_data in suppliers_data:
        supplier = Supplier.query.filter_by(supplier_code=supplier_data['supplier_code']).first()
        if not supplier:
            admin_user = User.query.filter_by(username='admin').first()
            supplier_data['created_by'] = str(admin_user.id) if admin_user else '1'
            supplier = Supplier(**supplier_data)
            db.session.add(supplier)
    
    # 创建示例物料
    materials_data = [
        {
            'material_code': '010200010001',
            'material_name': '主轴',
            'specification': '直径50mm，长度200mm',
            'unit': '件',
            'standard_cost': 150.0,
            'material_type': 'custom'
        },
        {
            'material_code': '025220100001',
            'material_name': 'M8×20螺栓',
            'specification': '8级强度',
            'unit': '个',
            'standard_cost': 0.5,
            'material_type': 'purchase'
        }
    ]
    
    for material_data in materials_data:
        material = Material.query.filter_by(material_code=material_data['material_code']).first()
        if not material:
            admin_user = User.query.filter_by(username='admin').first()
            material_data['created_by'] = str(admin_user.id) if admin_user else '1'
            material = Material(**material_data)
            material.parse_material_code()
            db.session.add(material)
    
    db.session.commit()
    print("示例数据初始化完成")

def main():
    """主函数"""
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建完成")
        
        # 初始化基础数据
        init_permissions()
        init_roles()
        init_users()
        init_material_categories()
        init_sample_data()
        
        print("\n数据库初始化完成！")
        print("默认用户账号:")
        print("  管理员: admin / admin123")
        print("  测试用户: test / test123")

if __name__ == '__main__':
    main()