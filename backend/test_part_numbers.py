import requests
import json

# 测试获取零件号列表
def test_get_part_numbers():
    url = "http://localhost:5000/api/visiray/part-numbers"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_get_part_numbers()