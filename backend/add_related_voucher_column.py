#!/usr/bin/env python
"""添加stock_in_record表的related_voucher列"""

import os
import sys
from dotenv import load_dotenv
import pymysql

# 加载环境变量
load_dotenv()

def add_related_voucher_column():
    """添加stock_in_record表的related_voucher列"""
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
        
        # 检查related_voucher列是否已存在
        cursor.execute("SHOW COLUMNS FROM stock_in_record LIKE 'related_voucher'")
        result = cursor.fetchone()
        
        if result:
            print("related_voucher列已存在")
        else:
            # 添加related_voucher列
            alter_sql = "ALTER TABLE stock_in_record ADD COLUMN related_voucher LONGBLOB"
            cursor.execute(alter_sql)
            print("related_voucher列添加成功")
        
        # 提交事务
        connection.commit()
        
        # 关闭连接
        cursor.close()
        connection.close()
        
        print("\n数据库表结构更新完成!")
        return True
        
    except Exception as e:
        print(f"更新数据库失败: {e}")
        return False

if __name__ == '__main__':
    add_related_voucher_column()