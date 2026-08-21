#!/usr/bin/env python
"""测试Visiray登录API的错误方法"""

import requests
import json

def test_visiray_login_get():
    """测试使用GET方法访问Visiray登录API"""
    base_url = "http://localhost:5000"
    
    # 测试使用GET方法访问Visiray登录API
    print("=== 测试使用GET方法访问Visiray登录API ===")
    visiray_login_url = f"{base_url}/api/visiray/login"
    
    try:
        response = requests.get(visiray_login_url)
        print(f"GET请求Visiray登录状态码: {response.status_code}")
        print(f"GET请求Visiray登录响应头: {dict(response.headers)}")
        print(f"GET请求Visiray登录响应内容: {response.text}")
    except Exception as e:
        print(f"GET请求Visiray登录失败: {e}")

if __name__ == "__main__":
    test_visiray_login_get()