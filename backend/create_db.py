#!/usr/bin/env python
"""
创建BOM系统数据库
"""

import pymysql
import os

def create_database():
    """创建BOM数据库"""
    try:
        # 数据库连接配置
        host = 'localhost'
        port = 3306
        user = 'test'
        password = 'Visiray88!!'
        database = 'bom_dev'
        
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