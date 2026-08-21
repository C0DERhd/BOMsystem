import os
import sys
import requests

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_avatar_upload():
    """测试头像上传功能"""
    # 先登录获取认证信息
    login_url = "http://localhost:5000/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    test_file_path = "test_avatar.png"
    
    try:
        # 登录
        login_response = session.post(login_url, json=login_data)
        print(f"Login Status Code: {login_response.status_code}")
        login_result = login_response.json()
        print(f"Login Response: {login_result}")
        
        if not login_result.get('success'):
            print("Login failed")
            return
            
        # 获取访问令牌
        access_token = login_result['data']['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # 创建一个模拟的PNG文件
        with open(test_file_path, "wb") as f:
            # 写入PNG文件头（模拟PNG文件）
            f.write(b'\x89PNG\r\n\x1a\n')
            # 添加一些模拟数据
            f.write(b'This is a test PNG file content')
        
        # 准备文件上传
        upload_url = "http://localhost:5000/api/users/1/avatar"
        files = {'avatar': (test_file_path, open(test_file_path, 'rb'), 'image/png')}
        
        # 发送POST请求
        response = session.post(upload_url, files=files, headers=headers)
        
        print(f"Upload Status Code: {response.status_code}")
        try:
            print(f"Upload Response: {response.json()}")
        except:
            print(f"Upload Response Text: {response.text}")
        
        # 清理测试文件
        files['avatar'][1].close()
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        
    except Exception as e:
        print(f"Error: {e}")
        if os.path.exists(test_file_path):
            try:
                os.remove(test_file_path)
            except:
                pass

if __name__ == "__main__":
    test_avatar_upload()