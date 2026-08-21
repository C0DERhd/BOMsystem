import os
import sys
import requests
import time

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_full_avatar_flow():
    """测试完整的头像上传和显示流程"""
    # 先登录获取认证信息
    login_url = "http://localhost:5000/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    test_file_path = "test_avatar.png"
    
    try:
        print("1. 用户登录...")
        # 登录
        login_response = session.post(login_url, json=login_data)
        print(f"   登录状态码: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print("   登录失败")
            return
            
        login_result = login_response.json()
        if not login_result.get('success'):
            print("   登录失败:", login_result.get('message'))
            return
            
        # 获取访问令牌
        access_token = login_result['data']['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        print("2. 获取当前用户信息...")
        # 获取当前用户信息
        me_url = "http://localhost:5000/api/auth/me"
        me_response = session.get(me_url, headers=headers)
        me_result = me_response.json()
        user_id = me_result['data']['user']['id']
        print(f"   当前用户ID: {user_id}")
        print(f"   当前头像URL: {me_result['data']['user']['avatar']}")
        
        print("3. 创建测试图片文件...")
        # 创建一个模拟的PNG文件
        with open(test_file_path, "wb") as f:
            # 写入PNG文件头（模拟PNG文件）
            f.write(b'\x89PNG\r\n\x1a\n')
            # 添加一些模拟数据
            f.write(b'This is a test PNG file content for avatar upload')
        
        print("4. 上传头像...")
        # 准备文件上传
        upload_url = f"http://localhost:5000/api/users/{user_id}/avatar"
        files = {'avatar': (test_file_path, open(test_file_path, 'rb'), 'image/png')}
        
        # 发送POST请求
        response = session.post(upload_url, files=files, headers=headers)
        
        print(f"   上传状态码: {response.status_code}")
        if response.status_code != 200:
            print("   上传失败")
            return
            
        try:
            upload_result = response.json()
            print(f"   上传结果: {upload_result}")
            
            if not upload_result.get('success'):
                print("   上传失败:", upload_result.get('message'))
                return
                
            avatar_url = upload_result['data']['avatar_url']
            print(f"   新头像URL: {avatar_url}")
            
        except Exception as e:
            print(f"   解析上传响应失败: {e}")
            return
        
        # 关闭文件
        files['avatar'][1].close()
        
        print("5. 重新获取用户信息验证头像更新...")
        # 重新获取用户信息
        time.sleep(1)  # 等待一下确保数据库更新
        me_response2 = session.get(me_url, headers=headers)
        me_result2 = me_response2.json()
        print(f"   更新后的头像URL: {me_result2['data']['user']['avatar']}")
        
        if me_result2['data']['user']['avatar'] == avatar_url:
            print("   ✓ 头像更新成功并同步到用户信息")
        else:
            print("   ✗ 头像未正确同步到用户信息")
        
        print("6. 验证文件可访问性...")
        # 验证文件可访问性
        file_response = session.get(f"http://localhost:5000{avatar_url}")
        print(f"   文件访问状态码: {file_response.status_code}")
        
        if file_response.status_code == 200:
            print("   ✓ 头像文件可正常访问")
        else:
            print("   ✗ 头像文件无法访问")
            
        print("\n测试完成!")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            try:
                os.remove(test_file_path)
            except:
                pass

if __name__ == "__main__":
    test_full_avatar_flow()