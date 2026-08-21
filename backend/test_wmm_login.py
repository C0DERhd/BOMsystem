#!/usr/bin/env python
"""测试wmm账户登录"""

import requests
import json

def test_wmm_login():
    """测试wmm账户登录"""
    base_url = "http://localhost:5000"
    
    # 测试Visiray登录API
    print("=== 测试wmm账户登录 ===")
    visiray_login_url = f"{base_url}/api/visiray/login"
    login_data = {
        "account": "wmm",
        "password": "508508"
    }
    
    try:
        response = requests.post(visiray_login_url, json=login_data)
        print(f"登录状态码: {response.status_code}")
        print(f"登录响应: {response.json()}")
    except Exception as e:
        print(f"登录请求失败: {e}")

if __name__ == "__main__":
    test_wmm_login()