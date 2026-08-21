#!/usr/bin/env python
"""测试统一用户认证系统"""

import requests
import json

def test_unified_auth_system():
    """测试统一用户认证系统"""
    base_url = "http://localhost:5000"
    
    print("=== 测试统一用户认证系统 ===")
    
    # 1. 使用主系统注册API注册新用户
    print("\n1. 使用主系统注册API注册新用户")
    register_data = {
        "username": "unified_test_user",
        "email": "unified_test@example.com",
        "name": "统一认证测试用户",
        "password": "unified_test_pass123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/register", json=register_data)
        print(f"   注册状态码: {response.status_code}")
        if response.status_code == 201:
            print("   注册成功!")
        else:
            print(f"   注册失败: {response.json()}")
    except Exception as e:
        print(f"   注册请求失败: {e}")
    
    # 2. 使用主系统登录API登录
    print("\n2. 使用主系统登录API登录")
    login_data = {
        "username": "unified_test_user",
        "password": "unified_test_pass"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"   登录状态码: {response.status_code}")
        if response.status_code == 200:
            print("   登录成功!")
            print(f"   用户信息: {response.json()['data']['user']['username']}")
        else:
            print(f"   登录失败: {response.json()}")
    except Exception as e:
        print(f"   登录请求失败: {e}")
    
    # 3. 验证用户已添加到主系统数据库
    print("\n3. 验证用户已添加到主系统数据库")
    try:
        import pymysql
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='778296',
            database='bom_dev'
        )
        cursor = connection.cursor()
        cursor.execute("SELECT username, name, email FROM users WHERE username='unified_test_user'")
        user = cursor.fetchone()
        if user:
            print(f"   数据库中找到用户: {user[0]} ({user[1]}) - {user[2]}")
        else:
            print("   数据库中未找到用户")
        connection.close()
    except Exception as e:
        print(f"   数据库查询失败: {e}")

if __name__ == "__main__":
    test_unified_auth_system()