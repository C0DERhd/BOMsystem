#!/usr/bin/env python
"""测试登录API"""

import requests
import json

def test_login_apis():
    """测试不同的登录API"""
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
    
    # 测试Visiray登录API
    print("\n=== 测试Visiray登录API ===")
    visiray_login_url = f"{base_url}/api/visiray/login"
    visiray_login_data = {
        "account": "testuser123",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(visiray_login_url, json=visiray_login_data)
        print(f"Visiray登录状态码: {response.status_code}")
        print(f"Visiray登录响应: {response.json()}")
    except Exception as e:
        print(f"Visiray登录请求失败: {e}")
        
    # 测试错误的请求方法
    print("\n=== 测试错误的请求方法 ===")
    try:
        response = requests.get(visiray_login_url, json=visiray_login_data)
        print(f"GET请求Visiray登录状态码: {response.status_code}")
        print(f"GET请求Visiray登录响应: {response.json()}")
    except Exception as e:
        print(f"GET请求Visiray登录失败: {e}")

if __name__ == "__main__":
    test_login_apis()