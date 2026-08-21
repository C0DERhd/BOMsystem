#!/usr/bin/env python
"""测试头像上传功能"""

import os
import sys
import json
import requests

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_avatar_upload():
    """测试头像上传"""
    try:
        # 先登录获取token
        login_url = "http://127.0.0.1:5000/api/auth/login"
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        login_response = requests.post(login_url, json=login_data)
        if login_response.status_code != 200:
            print("登录失败!")
            return False
            
        auth_data = login_response.json()
        access_token = auth_data['data']['access_token']
        
        # 准备测试图片文件
        # 创建一个简单的测试图片
        import base64
        
        # 创建一个简单的PNG图片数据
        test_image_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        
        # 保存为临时文件
        with open("test_avatar.png", "wb") as f:
            f.write(test_image_data)
        
        # 上传头像
        upload_url = "http://127.0.0.1:5000/api/users/1/avatar"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        with open("test_avatar.png", "rb") as f:
            files = {'avatar': ('test_avatar.png', f, 'image/png')}
            response = requests.post(upload_url, headers=headers, files=files)
        
        print(f"上传状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        # 清理临时文件
        os.remove("test_avatar.png")
        
        if response.status_code == 200:
            print("头像上传成功!")
            return True
        else:
            print("头像上传失败!")
            return False
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 清理临时文件
        if os.path.exists("test_avatar.png"):
            os.remove("test_avatar.png")
        return False

if __name__ == '__main__':
    test_avatar_upload()