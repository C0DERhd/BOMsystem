#!/usr/bin/env python
"""
最终演示：零件号递增功能完整实现
"""

class PartNumberIncrementSystem:
    """零件号递增系统"""
    
    def __init__(self):
        # 模拟数据库存储
        self.database = {
            'generated_numbers': set(),  # 已生成的零件号
            'counters': {}  # 各类别计数器
        }
        
        # 编码规则
        self.category_codes = {
            'custom': 0,      # 定制件: 0-4
            'purchased': 5    # 外购件: 5-9
        }
        
        self.main_category_codes = {
            'optical': 0,      # 光学件: 00-19
            'mechanical': 20,  # 机械件: 20-39
            'electrical': 40,  # 电气/子件: 40-59
            'software': 60,    # 软件: 60-69
            'chemical': 70,    # 化学品: 70-79
            'other': 80        # 其他: 80-99
        }
    
    def apply_part_number(self, part_category, main_category):
        """申请零件号 - 核心功能"""
        print(f"申请零件号: 类别={part_category}, 大类={main_category}")
        
        # 获取编码
        part_category_code = self.category_codes.get(part_category, 0)
        main_category_code = self.main_category_codes.get(main_category, 80)
        
        # 生成零件号
        part_number = self._generate_part_number(part_category_code, main_category_code)
        
        # 保存到"数据库"
        self.database['generated_numbers'].add(part_number)
        
        print(f"生成的零件号: {part_number}")
        return part_number
    
    def _generate_part_number(self, part_category_code, main_category_code):
        """生成零件号的核心逻辑"""
        # 初始化编码参数
        sub_category_code = 0
        product_number = 0
        version_number = 1
        
        # 查找下一个可用的产品编号
        while True:
            # 构造零件号
            part_number = f"{part_category_code}{main_category_code:02d}{sub_category_code:02d}{product_number:04d}{version_number:02d}"
            
            # 检查是否已存在
            if part_number not in self.database['generated_numbers']:
                break
            
            # 递增产品编号
            product_number += 1
            
            # 检查进位
            if product_number > 9999:
                product_number = 0
                sub_category_code += 1
                print(f"    产品编号达到上限，小类编码进位到: {sub_category_code:02d}")
                
                if sub_category_code > 99:
                    sub_category_code = 0
                    main_category_code += 1
                    print(f"    小类编码达到上限，大类编码进位到: {main_category_code:02d}")
                    
                    if not self._is_main_category_valid(main_category_code):
                        main_category_code = self._get_main_category_start_code(main_category_code)
                        part_category_code += 1
                        print(f"    大类编码达到上限，零部件类别编码进位到: {part_category_code}")
                        
                        if part_category_code > 9:
                            raise Exception("所有编码范围已用完")
        
        return part_number
    
    def _is_main_category_valid(self, main_category_code):
        """检查大类编码是否有效"""
        valid_ranges = [
            (0, 19),    # 光学件
            (20, 39),   # 机械件
            (40, 59),   # 电气/子件
            (60, 69),   # 软件
            (70, 79),   # 化学品
            (80, 99)    # 其他
        ]
        
        for range_start, range_end in valid_ranges:
            if main_category_code >= range_start and main_category_code <= range_end:
                return True
        return False
    
    def _get_main_category_start_code(self, main_category_code):
        """获取大类编码的起始值"""
        ranges = [
            (0, 19),    # 光学件
            (20, 39),   # 机械件
            (40, 59),   # 电气/子件
            (60, 69),   # 软件
            (70, 79),   # 化学品
            (80, 99)    # 其他
        ]
        
        for range_start, range_end in ranges:
            if main_category_code >= range_start and main_category_code <= range_end:
                return range_start
        return 80

def demo_increment_function():
    """演示递增功能"""
    print("零件号递增功能完整演示")
    print("=" * 50)
    
    system = PartNumberIncrementSystem()
    
    # 演示1: 连续申请同一类别的零件号
    print("\n1. 连续申请定制件光学件 (生成10个):")
    print("-" * 40)
    for i in range(10):
        part_number = system.apply_part_number('custom', 'optical')
        print(f"  第{i+1}次申请: {part_number}")
    
    # 演示2: 产品编号进位
    print("\n2. 产品编号进位演示:")
    print("-" * 40)
    # 手动添加一些接近进位点的零件号到数据库，模拟已经生成了很多零件号
    print("  预先添加零件号到数据库，模拟已生成了很多零件号...")
    for i in range(9995, 10000):
        test_number = f"00000{i:04d}01"
        system.database['generated_numbers'].add(test_number)
        print(f"    添加: {test_number}")
    
    # 继续申请，展示进位效果
    print("  继续申请零件号，展示进位效果:")
    for i in range(8):
        part_number = system.apply_part_number('custom', 'optical')
        print(f"    申请到的零件号: {part_number}")
    
    # 演示3: 不同类别的申请
    print("\n3. 不同类别的申请:")
    print("-" * 40)
    part_number1 = system.apply_part_number('purchased', 'mechanical')
    print(f"  外购件机械件: {part_number1}")
    
    part_number2 = system.apply_part_number('custom', 'electrical')
    print(f"  定制件电气件: {part_number2}")
    
    print(f"\n总共生成了 {len(system.database['generated_numbers'])} 个不同的零件号")
    
    # 显示最后几个生成的零件号
    print("\n最近生成的零件号:")
    recent_numbers = sorted(list(system.database['generated_numbers']))[-10:]
    for i, number in enumerate(recent_numbers, 1):
        print(f"  {i:2d}. {number}")

if __name__ == '__main__':
    demo_increment_function()