#!/usr/bin/env python
"""测试采购发票和合同PDF功能"""

import requests
import json

def test_purchase_files():
    """测试采购发票和合同PDF功能"""
    base_url = "http://localhost:5000"
    
    print("=== 测试采购发票和合同PDF功能 ===")
    
    # 测试获取不存在的采购发票
    print("\n1. 测试获取不存在的采购发票")
    try:
        response = requests.get(f"{base_url}/api/visiray/purchase-orders/NONEXISTENT/invoice")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"   请求失败: {e}")
    
    # 测试获取不存在的入库合同
    print("\n2. 测试获取不存在的入库合同")
    try:
        response = requests.get(f"{base_url}/api/visiray/purchase-orders/NONEXISTENT/contract")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"   请求失败: {e}")

if __name__ == "__main__":
    test_purchase_files()