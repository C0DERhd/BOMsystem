import requests
import json

# 测试后端 API 连接
def test_connection():
    try:
        print("测试后端 API 连接...")
        
        # 测试根路径
        response = requests.get("http://localhost:5000/")
        print(f"根路径状态码: {response.status_code}")
        
        # 测试登录路径
        response = requests.options("http://localhost:5000/api/auth/login")
        print(f"登录 OPTIONS 状态码: {response.status_code}")
        print(f"Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}")
        
        # 测试注册路径
        response = requests.options("http://localhost:5000/api/auth/register")
        print(f"注册 OPTIONS 状态码: {response.status_code}")
        print(f"Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}")
        
        print("\n所有测试完成!")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_connection()
