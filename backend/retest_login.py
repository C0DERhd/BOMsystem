#!/usr/bin/env python
"""重新测试登录流程"""

import requests
import json

def retest_login():
    """重新测试登录流程"""
    base_url = "http://localhost:5000"
    
    print("=== 重新测试登录流程 ===")
    
    # 先注册一个新用户
    print("\n1. 注册新用户")
    register_data = {
        "username": "login_test_user",
        "email": "login_test@example.com",
        "name": "登录测试用户",
        "password": "login_test_pass123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/register", json=register_data)
        print(f"   注册状态码: {response.status_code}")
        if response.status_code == 201:
            print("   注册成功!")
        else:
            print(f"   注册失败: {response.json()}")
            return
    except Exception as e:
        print(f"   注册请求失败: {e}")
        return
    
    # 立即尝试登录
    print("\n2. 登录新注册的用户")
    login_data = {
        "username": "login_test_user",
        "password": "login_test_pass123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"   登录状态码: {response.status_code}")
        print(f"   登录响应: {response.json()}")
    except Exception as e:
        print(f"   登录请求失败: {e}")

if __name__ == "__main__":
    retest_login()