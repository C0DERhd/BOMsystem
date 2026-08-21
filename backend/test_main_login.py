#!/usr/bin/env python
"""测试主系统登录API"""

import requests
import json

def test_main_login():
    """测试主系统登录API"""
    base_url = "http://localhost:5000"
    
    # 测试主系统登录API
    print("=== 测试主系统登录API ===")
    main_login_url = f"{base_url}/api/auth/login"
    main_login_data = {
        "username": "test",
        "password": "test123"
    }
    
    try:
        response = requests.post(main_login_url, json=main_login_data)
        print(f"主系统登录状态码: {response.status_code}")
        print(f"主系统登录响应: {response.json()}")
    except Exception as e:
        print(f"主系统登录请求失败: {e}")

if __name__ == "__main__":
    test_main_login()