#!/usr/bin/env python
"""测试数据库密码验证"""

from werkzeug.security import check_password_hash

def test_database_password():
    """测试数据库密码验证"""
    print("=== 测试数据库密码验证 ===")
    
    # 数据库中的密码哈希
    password_hash = "pbkdf2:sha256:600000$v3EP5ArM0cCmizhs$62419db588b3f150443d510fd1d460f26983e942c148731716e0e91b3bc08e58"
    password = "unified_test_pass123"
    
    print(f"密码哈希: {password_hash}")
    print(f"测试密码: {password}")
    
    # 验证密码
    is_valid = check_password_hash(password_hash, password)
    print(f"密码验证结果: {is_valid}")
    
    if is_valid:
        print("密码正确!")
    else:
        print("密码错误!")

if __name__ == "__main__":
    test_database_password()