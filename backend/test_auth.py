import requests
import json

# 测试登录和注册功能
def test_auth():
    try:
        print("测试登录和注册功能...")
        
        # 测试注册
        print("\n1. 测试注册功能:")
        register_url = "http://localhost:5000/api/auth/register-user"
        register_data = {
            "username": "testuser",
            "account": "testuser123",
            "password": "testpassword123"
        }
        
        response = requests.post(register_url, json=register_data)
        print(f"注册响应状态码: {response.status_code}")
        print(f"注册响应内容: {response.json()}")
        
        # 测试登录
        print("\n2. 测试登录功能:")
        login_url = "http://localhost:5000/api/auth/login"
        login_data = {
            "username": "testuser123",
            "password": "testpassword123"
        }
        
        response = requests.post(login_url, json=login_data)
        print(f"登录响应状态码: {response.status_code}")
        print(f"登录响应内容: {response.json()}")
        
        print("\n所有测试完成!")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_auth()