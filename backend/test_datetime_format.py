#!/usr/bin/env python
"""测试日期时间格式化"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从模型导入
from app.models.visiray import VisirayPartNumber

def test_datetime_format():
    """测试日期时间格式化"""
    print("测试日期时间格式化")
    print("=" * 50)
    
    # 创建一个测试记录
    test_record = VisirayPartNumber(
        part_id="00000000001",
        category="custom",
        main_type="optical",
        sub_type="light_source",
        created_at=datetime.now()
    )
    
    # 获取字典格式的数据
    data = test_record.to_dict()
    print(f"原始创建时间: {test_record.created_at}")
    print(f"格式化后的创建时间: {data['created_at']}")
    
    # 验证格式是否符合要求 (YYYY-MM-DD HH:MM:SS)
    if data['created_at']:
        try:
            # 尝试解析日期时间字符串
            parsed_time = datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
            print(f"解析成功，日期时间对象: {parsed_time}")
            print("✓ 日期时间格式正确")
        except ValueError as e:
            print(f"✗ 日期时间格式错误: {e}")
    else:
        print("✗ 创建时间为空")

if __name__ == '__main__':
    test_datetime_format()