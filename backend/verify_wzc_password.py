#!/usr/bin/env python
"""验证wzc用户密码"""

from werkzeug.security import check_password_hash

def verify_wzc_password():
    """验证wzc用户密码"""
    # 从数据库中获取的密码哈希
    password_hash = "pbkdf2:sha256:600000$LcVvywIvL7l1vR7E$3d6fade57aafa0c7727d003c6e18af8d674c5aee7243e753cd5063ceb6009f5f"
    password = "778296"
    
    print("验证wzc用户密码:")
    print(f"  密码哈希: {password_hash}")
    print(f"  测试密码: {password}")
    
    # 验证密码
    is_valid = check_password_hash(password_hash, password)
    print(f"  密码验证结果: {is_valid}")
    
    if is_valid:
        print("  密码正确!")
    else:
        print("  密码错误!")

if __name__ == "__main__":
    verify_wzc_password()