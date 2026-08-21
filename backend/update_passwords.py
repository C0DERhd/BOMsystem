#!/usr/bin/env python
"""更新user_account表中的明文密码为哈希格式"""

import os
import sys
from dotenv import load_dotenv
import pymysql
from werkzeug.security import generate_password_hash

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

def update_passwords():
    """更新密码为哈希格式"""
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
        
        # 获取所有用户
        cursor.execute("SELECT username, account, password FROM user_account")
        users = cursor.fetchall()
        
        # 更新每个用户的密码为哈希格式
        for user in users:
            username, account, pwd = user
            # 检查密码是否已经是哈希格式（包含$符号）
            if '$' not in pwd:
                # 生成哈希密码
                hashed_password = generate_password_hash(pwd)
                # 更新数据库
                cursor.execute(
                    "UPDATE user_account SET password = %s WHERE account = %s",
                    (hashed_password, account)
                )
                print(f"用户 {account} 的密码已更新为哈希格式")
            else:
                print(f"用户 {account} 的密码已经是哈希格式")
        
        # 提交事务
        connection.commit()
        
        # 关闭连接
        cursor.close()
        connection.close()
        
        print("\n所有密码更新完成!")
        return True
        
    except Exception as e:
        print(f"更新密码失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    update_passwords()