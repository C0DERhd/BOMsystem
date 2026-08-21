#!/usr/bin/env python
"""
创建Visiray数据库
"""

try:
    import pymysql
except ImportError:
    print("错误: 无法导入 pymysql 模块")
    print("请确保已安装 PyMySQL: pip install PyMySQL")
    sys.exit(1)

import sys
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

def create_database():
    """创建Visiray数据库"""
    try:
        # 从环境变量获取数据库连接信息
        db_url = os.getenv('DEV_DATABASE_URL', 'mysql+pymysql://test:Visiray88!!@192.168.0.2:3306/visiray')
        
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
        
        # 连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"数据库 '{database}' 创建成功或已存在")
            
            # 使用数据库
            cursor.execute(f"USE `{database}`")
            
            # 显示数据库中的表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"\n数据库 '{database}' 中的表:")
            if tables:
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("  (无表)")
        
        connection.close()
        print("\n数据库设置完成!")
        return True
        
    except Exception as e:
        print(f"创建数据库失败: {e}")
        return False

if __name__ == '__main__':
    create_database()