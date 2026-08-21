#!/usr/bin/env python
"""测试密码哈希和验证"""

from werkzeug.security import generate_password_hash, check_password_hash

def test_password_hashing():
    """测试密码哈希和验证"""
    print("=== 测试密码哈希和验证 ===")
    
    # 测试密码
    password = "unified_test_pass123"
    
    # 生成密码哈希
    password_hash = generate_password_hash(password)
    print(f"原始密码: {password}")
    print(f"密码哈希: {password_hash}")
    
    # 验证密码
    is_valid = check_password_hash(password_hash, password)
    print(f"密码验证结果: {is_valid}")
    
    # 验证错误密码
    is_invalid = check_password_hash(password_hash, "wrong_password")
    print(f"错误密码验证结果: {is_invalid}")

if __name__ == "__main__":
    test_password_hashing()