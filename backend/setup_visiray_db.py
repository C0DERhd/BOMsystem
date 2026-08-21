#!/usr/bin/env python
"""设置Visiray数据库表"""

import os
import sys
from dotenv import load_dotenv
import pymysql

# 加载环境变量
load_dotenv()

def setup_visiray_db():
    """设置Visiray数据库表"""
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
        
        # 连接到Visiray数据库
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
        
        # 创建表的SQL语句
        create_table_sqls = [
            """
            CREATE TABLE IF NOT EXISTS inventory_management (
                goods_id BIGINT PRIMARY KEY,
                goods_name VARCHAR(200) NOT NULL,
                supplier VARCHAR(200),
                product_model VARCHAR(100),
                goods_type VARCHAR(100),
                in_quantity INT DEFAULT 0,
                out_quantity INT DEFAULT 0,
                stock_quantity INT DEFAULT 0,
                unit VARCHAR(20),
                shelf_location VARCHAR(50),
                in_record TEXT,
                out_record TEXT,
                attachments VARCHAR(500),
                purchase_invoice VARCHAR(200),
                invoice_info TEXT,
                parent_record BIGINT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS stock_in_record (
                in_record VARCHAR(50) PRIMARY KEY,
                goods_id BIGINT,
                supplier_name VARCHAR(200),
                quantity INT,
                unit VARCHAR(20),
                in_date DATE,
                operator VARCHAR(50),
                shelf_location VARCHAR(50),
                goods_type VARCHAR(100),
                supplier VARCHAR(200),
                product_model VARCHAR(100),
                parent_record VARCHAR(50),
                inbound_type VARCHAR(20) DEFAULT '入库'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS stock_out_record (
                out_record_id BIGINT PRIMARY KEY AUTO_INCREMENT,
                goods_id BIGINT,
                goods_name VARCHAR(200),
                quantity INT,
                out_date DATE,
                operator VARCHAR(50),
                shelf_location VARCHAR(50),
                outbound_type VARCHAR(20) DEFAULT '出库'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS purchase_receiving_voucher (
                id INT PRIMARY KEY AUTO_INCREMENT,
                purchase_order_no VARCHAR(50) NOT NULL,
                product_code VARCHAR(50) NOT NULL,
                product_name VARCHAR(100) NOT NULL,
                quantity DECIMAL(10,2) NOT NULL,
                unit VARCHAR(20) NOT NULL,
                product_type VARCHAR(50),
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
                receiving_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT '待入库',
                supplier VARCHAR(100),
                invoice_no LONGBLOB,
                contract_pdf LONGBLOB
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS purchase_order_attachments (
                id INT PRIMARY KEY AUTO_INCREMENT,
                purchase_order_no VARCHAR(50) NOT NULL,
                stored_filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                content_type VARCHAR(100),
                file_size BIGINT,
                uploaded_by BIGINT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS supplier_information (
                id INT PRIMARY KEY AUTO_INCREMENT,
                supplier_code VARCHAR(50) UNIQUE NOT NULL,
                supplier_name VARCHAR(200) NOT NULL,
                phone VARCHAR(30),
                email VARCHAR(150),
                address VARCHAR(300),
                contact_person VARCHAR(100),
                position VARCHAR(100),
                coordinator VARCHAR(100),
                purchase_voucher_ref VARCHAR(50),
                stock_in_record TEXT,
                remarks TEXT,
                operator_name VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS part_number (
                part_id VARCHAR(50) PRIMARY KEY,
                category VARCHAR(100),
                main_type VARCHAR(100),
                sub_type VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        # 执行创建表的SQL语句
        for i, sql in enumerate(create_table_sqls):
            try:
                cursor.execute(sql)
                print(f"表 {i+1} 创建成功")
            except Exception as e:
                print(f"创建表 {i+1} 失败: {e}")
        
        # 提交事务
        connection.commit()
        
        # 显示数据库中的所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\n数据库 '{database}' 中的表:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 关闭连接
        cursor.close()
        connection.close()
        
        print("\n数据库表设置完成!")
        return True
        
    except Exception as e:
        print(f"设置数据库失败: {e}")
        return False

if __name__ == '__main__':
    setup_visiray_db()