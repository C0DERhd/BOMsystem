#!/usr/bin/env python
"""模拟前端登录过程"""

import requests
import json

def simulate_frontend_login():
    """模拟前端登录过程"""
    base_url = "http://localhost:5000"
    
    # 模拟前端发送的请求
    print("=== 模拟前端登录过程 ===")
    login_url = f"{base_url}/api/visiray/login"
    login_data = {
        "account": "wmm",
        "password": "508508"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.post(login_url, json=login_data, headers=headers)
        print(f"请求URL: {login_url}")
        print(f"请求方法: POST")
        print(f"请求头: {headers}")
        print(f"请求数据: {login_data}")
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应数据: {response.json()}")
        
        if response.status_code == 200:
            print("登录成功！")
        else:
            print("登录失败！")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    simulate_frontend_login()