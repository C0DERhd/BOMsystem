#!/usr/bin/env python
"""测试主系统注册和登录功能"""

import requests
import json

def test_main_system_auth():
    """测试主系统注册和登录功能"""
    base_url = "http://localhost:5000"
    
    # 1. 测试注册新用户
    print("=== 1. 测试注册新用户 ===")
    register_url = f"{base_url}/api/auth/register"
    register_data = {
        "username": "testuser_main",
        "email": "testuser_main@example.com",
        "name": "主系统测试用户",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(register_url, json=register_data)
        print(f"注册状态码: {response.status_code}")
        print(f"注册响应: {response.json()}")
    except Exception as e:
        print(f"注册请求失败: {e}")
    
    # 2. 测试登录新注册的用户
    print("\n=== 2. 测试登录新注册的用户 ===")
    login_url = f"{base_url}/api/auth/login"
    login_data = {
        "username": "testuser_main",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        print(f"登录状态码: {response.status_code}")
        print(f"登录响应: {response.json()}")
    except Exception as e:
        print(f"登录请求失败: {e}")

if __name__ == "__main__":
    test_main_system_auth()