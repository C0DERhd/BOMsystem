#!/usr/bin/env python
"""测试Visiray用户登录"""

import requests
import json

def test_visiray_login():
    """测试Visiray用户登录"""
    url = "http://localhost:5000/api/visiray/login"
    
    # 使用您注册的账户信息
    data = {
        "account": "zhanchaowang",
        "password": "您注册时设置的密码"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200 and response.json().get('success'):
            print("登录成功!")
        else:
            print("登录失败!")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_visiray_login()