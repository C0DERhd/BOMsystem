#!/usr/bin/env python
"""测试wzc账户登录"""

import requests
import json

def test_wzc_login():
    """测试wzc账户登录"""
    base_url = "http://localhost:5000"
    
    print("测试wzc账户登录:")
    
    # 使用主系统登录API登录
    login_data = {
        "username": "wzc",
        "password": "778296"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"  登录状态码: {response.status_code}")
        if response.status_code == 200:
            print("  登录成功!")
            user_data = response.json()['data']['user']
            print(f"  用户名: {user_data['username']}")
            print(f"  姓名: {user_data['name']}")
            print(f"  邮箱: {user_data['email']}")
        else:
            print(f"  登录失败: {response.json()}")
    except Exception as e:
        print(f"  登录请求失败: {e}")

if __name__ == "__main__":
    test_wzc_login()