#!/usr/bin/env python
"""测试Visiray数据库连接"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.visiray import VisirayPartNumber, VisirayInventory, VisirayStockInRecord, VisirayStockOutRecord, VisirayPurchaseReceivingVoucher, VisiraySupplierInformation
import pymysql
from dotenv import load_dotenv
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()
load_dotenv(os.path.join(project_dir, '.env'))

def test_visiray_connection():
    """测试Visiray数据库连接"""
    try:
        # 从环境变量获取数据库连接信息
        db_url = os.getenv('VISIRAY_DATABASE_URL', 'mysql+pymysql://test:Visiray88!!@192.168.0.2:3306/visiray')
        
        # 解析数据库连接信息
        # 格式: mysql+pymysql://user:password@host:port/database
        parts = db_url.split('://')[1].split('@')
        user_pass = parts[0].split(':')
        host_port_db = parts[1].split('/')
        
        user = user_pass[0]
        password = user_pass[1]
        host = host_port_db[0].split(':')[0]
        port = int(host_port_db[0].split(':')[1]) if ':' in host_port_db[0] else 3306
        database = host_port_db[1]
        
        print(f"连接信息:")
        print(f"  用户: {user}")
        print(f"  密码: {'*' * len(password)}")
        print(f"  主机: {host}")
        print(f"  端口: {port}")
        print(f"  数据库: {database}")
        
        # 测试连接到Visiray数据库
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        
        print("数据库连接成功")
        
        # 创建游标对象
        cursor = connection.cursor()
        
        # 检查各个表结构
        tables = [
            'inventory_management',
            'stock_in_record', 
            'stock_out_record',
            'purchase_receiving_voucher',
            'supplier_information',
            'part_number'
        ]
        
        for table in tables:
            try:
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                print(f"\n{table}表结构:")
                for column in columns:
                    print(f"  {column[0]} {column[1]} {column[2]} {column[3]} {column[4]} {column[5]}")
            except Exception as e:
                print(f"获取{table}表结构失败: {e}")
        
        # 关闭连接
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"数据库连接失败: {e}")

if __name__ == '__main__':
    test_visiray_connection()