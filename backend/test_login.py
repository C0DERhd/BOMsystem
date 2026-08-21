#!/usr/bin/env python
"""测试登录功能"""

import os
import sys
import json
import requests

# 测试登录功能
def test_login_function():
    url = "http://localhost:5000/api/visiray/login"
    
    # 登录数据
    data = {
        "account": "test123",
        "password": "password123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login_function()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_login():
    """测试登录"""
    try:
        # API端点
        url = "http://127.0.0.1:5000/api/auth/login"
        
        # 准备测试数据
        data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        # 发送POST请求
        response = requests.post(url, json=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("登录成功!")
            return True
        else:
            print("登录失败!")
            return False
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_login()