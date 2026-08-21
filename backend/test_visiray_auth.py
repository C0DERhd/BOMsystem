#!/usr/bin/env python
"""测试Visiray注册和登录功能"""

import requests
import json

def test_visiray_register_and_login():
    """测试Visiray注册和登录功能"""
    base_url = "http://localhost:5000/api"
    
    # 测试注册
    print("=== 测试Visiray注册 ===")
    register_url = f"{base_url}/visiray/register"
    register_data = {
        "username": "testuser",
        "account": "testuser123",
        "password": "testpass123",
        "confirm_password": "testpass123"
    }
    
    try:
        register_response = requests.post(register_url, json=register_data)
        print(f"注册状态码: {register_response.status_code}")
        print(f"注册响应: {register_response.json()}")
    except Exception as e:
        print(f"注册请求失败: {e}")
        
    # 测试登录
    print("\n=== 测试Visiray登录 ===")
    login_url = f"{base_url}/visiray/login"
    login_data = {
        "account": "testuser123",
        "password": "testpass123"
    }
    
    try:
        login_response = requests.post(login_url, json=login_data)
        print(f"登录状态码: {login_response.status_code}")
        print(f"登录响应: {login_response.json()}")
    except Exception as e:
        print(f"登录请求失败: {e}")

if __name__ == "__main__":
    test_visiray_register_and_login()