#!/usr/bin/env python
"""测试前端登录流程"""

import requests
import json

def test_frontend_login_flow():
    """测试前端登录流程"""
    base_url = "http://localhost:5000"
    
    print("=== 1. 测试直接访问Visiray登录API ===")
    visiray_login_url = f"{base_url}/api/visiray/login"
    login_data = {
        "account": "wmm",
        "password": "508508"
    }
    
    try:
        response = requests.post(visiray_login_url, json=login_data)
        print(f"直接API访问状态码: {response.status码}")
        print(f"直接API访问响应: {response.json()}")
    except Exception as e:
        print(f"直接API访问失败: {e}")
    
    print("\n=== 2. 测试使用错误的HTTP方法 ===")
    try:
        response = requests.get(visiray_login_url, json=login_data)
        print(f"GET请求状态码: {response.status_code}")
        print(f"GET请求响应: {response.text}")
    except Exception as e:
        print(f"GET请求失败: {e}")
    
    print("\n=== 3. 测试使用错误的密码 ===")
    wrong_login_data = {
        "account": "wmm",
        "password": "wrongpassword"
    }
    
    try:
        response = requests.post(visiray_login_url, json=wrong_login_data)
        print(f"错误密码状态码: {response.status_code}")
        print(f"错误密码响应: {response.json()}")
    except Exception as e:
        print(f"错误密码请求失败: {e}")

if __name__ == "__main__":
    test_frontend_login_flow()
