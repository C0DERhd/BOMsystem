#!/usr/bin/env python
"""测试重新调整后的注册功能"""

import requests
import json

def test_rearranged_registration():
    """测试重新调整后的注册功能"""
    base_url = "http://localhost:5000"
    
    print("=== 测试重新调整后的注册功能 ===")
    
    # 注册新用户，按照新的字段对应关系
    register_data = {
        "username": "test_account_123",  # 账户对应username字段
        "email": "test_account@example.com",
        "name": "测试用户名",  # 用户名对应name字段
        "password": "test_account_pass123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/register", json=register_data)
        print(f"注册状态码: {response.status_code}")
        if response.status_code == 201:
            print("注册成功!")
            user_data = response.json()['data']['user']
            print(f"  数据库username字段: {user_data['username']}")
            print(f"  数据库name字段: {user_data['name']}")
            print(f"  邮箱: {user_data['email']}")
        else:
            print(f"注册失败: {response.json()}")
    except Exception as e:
        print(f"注册请求失败: {e}")
    
    # 登录新注册的用户
    print("\n=== 测试登录新注册的用户 ===")
    login_data = {
        "username": "test_account_123",  # 使用账户登录
        "password": "test_account_pass123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"登录状态码: {response.status_code}")
        if response.status_code == 200:
            print("登录成功!")
            user_data = response.json()['data']['user']
            print(f"  登录用户名: {user_data['username']}")
            print(f"  显示姓名: {user_data['name']}")
        else:
            print(f"登录失败: {response.json()}")
    except Exception as e:
        print(f"登录请求失败: {e}")

if __name__ == "__main__":
    test_rearranged_registration()