#!/usr/bin/env python
"""测试Visiray登录API"""

import requests
import json

def test_visiray_login():
    """测试Visiray登录API"""
    base_url = "http://localhost:5000/api"
    
    # 测试不存在的用户
    print("=== 测试Visiray登录不存在的用户 ===")
    login_url = f"{base_url}/visiray/login"
    login_data = {
        "account": "nonexistent",
        "password": "wrongpassword"
    }
    
    try:
        login_response = requests.post(login_url, json=login_data)
        print(f"登录状态码: {login_response.status_code}")
        print(f"登录响应: {login_response.json()}")
        
        if login_response.status_code == 401:
            print("正确拒绝了不存在的用户!")
        else:
            print("存在问题，应该拒绝不存在的用户!")
    except Exception as e:
        print(f"登录请求失败: {e}")
        
    # 测试存在的用户
    print("\n=== 测试Visiray登录存在的用户 ===")
    login_data = {
        "account": "wzc",  # 这个用户在Visiray数据库中不存在
        "password": "778296"
    }
    
    try:
        login_response = requests.post(login_url, json=login_data)
        print(f"登录状态码: {login_response.status_code}")
        print(f"登录响应: {login_response.json()}")
        
        if login_response.status_code == 401:
            print("正确拒绝了不存在于Visiray数据库的用户!")
        else:
            print("存在问题，应该拒绝不存在于Visiray数据库的用户!")
    except Exception as e:
        print(f"登录请求失败: {e}")

if __name__ == "__main__":
    test_visiray_login()