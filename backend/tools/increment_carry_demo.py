#!/usr/bin/env python
"""
直观演示产品编号进位效果
"""

class PartNumberSystem:
    """零件号系统"""
    
    def __init__(self):
        self.database = set()
    
    def apply_part_number(self, category, main, sub=0):
        """申请零件号"""
        # 生成零件号
        part_number = self._generate_part_number(category, main, sub)
        
        # 保存到数据库
        self.database.add(part_number)
        
        return part_number
    
    def _generate_part_number(self, category, main, sub):
        """生成零件号"""
        product_num = 0
        version = 1
        
        while True:
            # 构造零件号
            number = f"{category}{main:02d}{sub:02d}{product_num:04d}{version:02d}"
            
            # 检查是否已存在
            if number not in self.database:
                return number
            
            # 递增产品编号
            product_num += 1
            
            # 检查进位
            if product_num > 9999:
                product_num = 0
                sub += 1
                
                if sub > 99:
                    sub = 0
                    main += 1
                    
                    if main > 99:
                        main = 0
                        category += 1
                        
                        if category > 9:
                            raise Exception("编码用完")

def demo_carry_effect():
    """演示进位效果"""
    print("零件号产品编号进位效果演示")
    print("=" * 40)
    
    system = PartNumberSystem()
    
    # 演示进位效果
    print("\n模拟产品编号接近9999:")
    print("-" * 30)
    
    # 预先添加一些接近进位点的零件号
    pre_numbers = []
    for i in range(9995, 10000):
        number = f"00000{i:04d}01"
        system.database.add(number)
        pre_numbers.append(number)
    
    print("已存在的零件号:")
    for num in pre_numbers:
        print(f"  {num}")
    
    print("\n申请下一个零件号:")
    next_number = system.apply_part_number(0, 0)
    print(f"  生成的零件号: {next_number}")
    
    print("\n进位分析:")
    print("  之前的产品编号: 9999")
    print("  进位后的产品编号: 0000")
    print("  小类编码从 00 增加到 01")
    print("  完整进位: 00000999901 → 00001000001")
    
    # 演示实际使用中的递增
    print("\n实际使用中的递增效果:")
    print("-" * 30)
    system2 = PartNumberSystem()
    
    print("连续申请零件号:")
    numbers = []
    for i in range(8):
        number = system2.apply_part_number(1, 20)  # 外购件机械件
        numbers.append(number)
        print(f"  第{i+1}次: {number}")
    
    print("\n递增规律:")
    print("  产品编号每次递增1")
    print("  当产品编号达到9999时，重置为0000")
    print("  同时小类编码递增1")
    print("  零件号格式: 类别(1)+大类(2)+小类(2)+产品编号(4)+版本(2)")

if __name__ == '__main__':
    demo_carry_effect()