import requests
import json

# 测试登录错误提示
def test_login_error():
    url = "http://localhost:5000/api/visiray/login"
    
    # 错误的登录数据
    data = {
        "account": "wrong_account",
        "password": "wrong_password"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login_error()