#!/usr/bin/env python
"""
完整的零件号递增功能演示
"""

class PartNumberGenerator:
    """零件号生成器"""
    
    def __init__(self):
        self.generated_numbers = set()
        self.request_count = 0
    
    def apply_part_number(self, category_code, main_code, sub_code=0):
        """申请零件号"""
        self.request_count += 1
        print(f"第{self.request_count}次申请零件号")
        
        # 生成零件号
        part_number = self._generate_number(category_code, main_code, sub_code)
        
        # 保存并返回
        self.generated_numbers.add(part_number)
        print(f"  生成的零件号: {part_number}")
        return part_number
    
    def _generate_number(self, category_code, main_code, sub_code):
        """生成零件号"""
        product_number = 0
        version = 1
        
        # 查找下一个可用的产品编号
        while True:
            # 构造零件号
            number = f"{category_code}{main_code:02d}{sub_code:02d}{product_number:04d}{version:02d}"
            
            # 检查是否已存在
            if number not in self.generated_numbers:
                return number
            
            # 递增产品编号
            product_number += 1
            
            # 检查进位
            if product_number > 9999:
                product_number = 0
                sub_code += 1
                print(f"  产品编号达到上限，小类编码进位到: {sub_code:02d}")
                
                if sub_code > 99:
                    sub_code = 0
                    main_code += 1
                    print(f"  小类编码达到上限，大类编码进位到: {main_code:02d}")
                    
                    if main_code > 99:
                        main_code = 0
                        category_code += 1
                        print(f"  大类编码达到上限，类别编码进位到: {category_code}")
                        
                        if category_code > 9:
                            raise Exception("所有编码范围已用完")

def demo_complete_increment():
    """完整演示递增功能"""
    print("完整的零件号递增功能演示")
    print("=" * 50)
    
    generator = PartNumberGenerator()
    
    # 演示1: 基本递增
    print("\n1. 基本递增演示:")
    print("-" * 20)
    for i in range(5):
        generator.apply_part_number(0, 0)  # 定制件光学件
    
    # 演示2: 产品编号进位
    print("\n2. 产品编号进位演示:")
    print("-" * 20)
    # 预先添加一些接近进位点的零件号
    for i in range(9997, 10000):
        test_number = f"00000{i:04d}01"
        generator.generated_numbers.add(test_number)
        print(f"  预先添加: {test_number}")
    
    # 申请下一个零件号，展示进位
    print("  申请下一个零件号:")
    generator.apply_part_number(0, 0)
    
    # 再申请几个
    for i in range(3):
        generator.apply_part_number(0, 0)
    
    # 演示3: 小类编码进位
    print("\n3. 小类编码进位演示:")
    print("-" * 20)
    # 预先添加小类编码99的接近进位点的零件号
    for i in range(9997, 10000):
        test_number = f"00099{i:04d}01"
        generator.generated_numbers.add(test_number)
    
    print("  当前已存在:")
    print("    00099999701")
    print("    00099999801")
    print("    00099999901")
    
    print("  申请下一个零件号:")
    generator.apply_part_number(0, 0)
    
    # 演示4: 连续申请展示完整流程
    print("\n4. 连续申请展示完整流程:")
    print("-" * 20)
    # 创建新的生成器
    gen2 = PartNumberGenerator()
    
    print("  连续申请20个零件号:")
    numbers = []
    for i in range(20):
        number = gen2.apply_part_number(5, 20)  # 外购件机械件
        numbers.append(number)
    
    print(f"\n  生成的零件号列表:")
    for i, number in enumerate(numbers, 1):
        print(f"    {i:2d}. {number}")
    
    # 展示进位点
    print("\n  进位点分析:")
    carry_points = []
    for i in range(len(numbers) - 1):
        current = int(numbers[i][5:9])  # 产品编号部分
        next_num = int(numbers[i+1][5:9])
        if next_num < current:  # 发生了进位
            carry_points.append((i+1, numbers[i], numbers[i+1]))
    
    if carry_points:
        for index, before, after in carry_points:
            print(f"    第{index}次申请发生进位:")
            print(f"      进位前: {before}")
            print(f"      进位后: {after}")
    else:
        print("    本次申请未发生进位")

if __name__ == '__main__':
    demo_complete_increment()