#!/usr/bin/env python
"""完整测试Visiray登录流程"""

import requests
import json

def test_complete_login_flow():
    """完整测试Visiray登录流程"""
    base_url = "http://localhost:5000"
    
    print("=== 完整测试Visiray登录流程 ===")
    
    # 1. 检查API端点是否可访问
    print("\n1. 检查API端点是否可访问")
    try:
        response = requests.options(f"{base_url}/api/visiray/login")
        print(f"   OPTIONS请求状态码: {response.status_code}")
        print(f"   允许的方法: {response.headers.get('Allow', '未知')}")
    except Exception as e:
        print(f"   OPTIONS请求失败: {e}")
    
    # 2. 使用正确的账户和密码登录
    print("\n2. 使用正确的账户和密码登录")
    login_data = {
        "account": "wmm",
        "password": "508508"
    }
    
    try:
        response = requests.post(f"{base_url}/api/visiray/login", json=login_data)
        print(f"   登录请求状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   登录成功: {response.json()}")
        else:
            print(f"   登录失败: {response.json()}")
    except Exception as e:
        print(f"   登录请求失败: {e}")
    
    # 3. 使用错误的密码登录
    print("\n3. 使用错误的密码登录")
    wrong_login_data = {
        "account": "wmm",
        "password": "wrongpassword"
    }
    
    try:
        response = requests.post(f"{base_url}/api/visiray/login", json=wrong_login_data)
        print(f"   错误密码请求状态码: {response.status_code}")
        if response.status_code == 401:
            print(f"   正确返回401错误: {response.json()}")
        else:
            print(f"   意外响应: {response.json()}")
    except Exception as e:
        print(f"   错误密码请求失败: {e}")
    
    # 4. 使用不存在的账户登录
    print("\n4. 使用不存在的账户登录")
    non_existent_login_data = {
        "account": "nonexistent",
        "password": "anypassword"
    }
    
    try:
        response = requests.post(f"{base_url}/api/visiray/login", json=non_existent_login_data)
        print(f"   不存在账户请求状态码: {response.status_code}")
        if response.status_code == 401:
            print(f"   正确返回401错误: {response.json()}")
        else:
            print(f"   意外响应: {response.json()}")
    except Exception as e:
        print(f"   不存在账户请求失败: {e}")
    
    # 5. 使用GET方法访问（应该返回405）
    print("\n5. 使用GET方法访问（应该返回405）")
    try:
        response = requests.get(f"{base_url}/api/visiray/login")
        print(f"   GET请求状态码: {response.status_code}")
        if response.status_code == 405:
            print("   正确返回405错误")
        else:
            print(f"   意外响应: {response.text}")
    except Exception as e:
        print(f"   GET请求失败: {e}")

if __name__ == "__main__":
    test_complete_login_flow()