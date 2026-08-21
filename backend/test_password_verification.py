#!/usr/bin/env python
"""测试密码验证逻辑"""

from werkzeug.security import check_password_hash, generate_password_hash

def test_password_verification():
    """测试密码验证逻辑"""
    # wmm用户的密码哈希
    password_hash = "pbkdf2:sha256:600000$ROSU4ZikULSRiXCC$085fb94d2ccfbf6ea19d878abe3a38ec59238eb87cf108029f818ff366ee2859"
    plain_password = "508508"
    
    print("=== 测试密码验证 ===")
    print(f"密码哈希: {password_hash}")
    print(f"明文密码: {plain_password}")
    
    # 验证密码
    is_valid = check_password_hash(password_hash, plain_password)
    print(f"密码验证结果: {is_valid}")
    
    if is_valid:
        print("密码正确！")
    else:
        print("密码错误！")

if __name__ == "__main__":
    test_password_verification()