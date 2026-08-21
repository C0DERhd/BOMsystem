#!/usr/bin/env python
"""测试前端与后端API通信"""

import requests
import json

def test_frontend_api():
    """测试前端API调用"""
    try:
        # 测试登录API
        url = "http://localhost:8001/api/auth/login"
        
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
            print("前端API调用成功!")
            return True
        else:
            print("前端API调用失败!")
            return False
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_frontend_api()