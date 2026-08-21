#!/usr/bin/env python
"""
模拟零件号递增过程
"""

class PartNumberGenerator:
    """零件号生成器"""
    
    def __init__(self, part_category_code, main_category_code):
        self.part_category_code = part_category_code
        self.main_category_code = main_category_code
        self.sub_category_code = 0
        self.product_number = 0
        self.version_number = 1
        self.generated_numbers = []
    
    def generate_next(self):
        """生成下一个零件号"""
        # 格式化为11位数字：零部件类别(1位) + 大类(2位) + 小类(2位) + 产品编号(4位) + 版本号(2位)
        part_number = f"{self.part_category_code}{self.main_category_code:02d}{self.sub_category_code:02d}{self.product_number:04d}{self.version_number:02d}"
        self.generated_numbers.append(part_number)
        
        # 递增产品编号
        self.product_number += 1
        
        # 检查是否需要进位
        if self.product_number > 9999:
            self.product_number = 0
            self.sub_category_code += 1
            print(f"    产品编号达到上限，小类编码进位到: {self.sub_category_code:02d}")
            
            if self.sub_category_code > 99:
                self.sub_category_code = 0
                self.main_category_code += 1
                print(f"    小类编码达到上限，大类编码进位到: {self.main_category_code:02d}")
                
                # 检查大类编码范围（简化演示）
                if self.main_category_code > 99:
                    self.main_category_code = 0
                    self.part_category_code += 1
                    print(f"    大类编码达到上限，零部件类别编码进位到: {self.part_category_code}")
                    
                    if self.part_category_code > 9:
                        print("    所有编码已用完!")
                        return None
        
        return part_number
    
    def generate_sequence(self, count):
        """生成一系列零件号"""
        print(f"生成 {count} 个零件号:")
        print(f"初始编码 - 零部件类别: {self.part_category_code}, 大类: {self.main_category_code:02d}, 小类: {self.sub_category_code:02d}, 产品编号: {self.product_number:04d}")
        print("-" * 60)
        
        for i in range(count):
            part_number = self.generate_next()
            if part_number is None:
                print("无法生成更多零件号：所有编码已用完")
                break
            
            print(f"{i+1:2d}. {part_number}")
            
            # 特殊情况标记
            if self.product_number == 1 and i > 0:
                print(f"    -> 产品编号重置并进位")
            elif self.sub_category_code == 1 and self.product_number == 0 and i > 0:
                print(f"    -> 小类编码重置并进位")
        
        print("-" * 60)
        print(f"共生成 {len(self.generated_numbers)} 个零件号")
        return self.generated_numbers

def simulate_different_scenarios():
    """模拟不同场景"""
    print("=" * 70)
    print("零件号递增过程模拟")
    print("=" * 70)
    
    # 场景1: 正常递增
    print("\n1. 正常递增场景 (生成25个零件号):")
    generator1 = PartNumberGenerator(0, 0)  # 定制件光学件
    numbers1 = generator1.generate_sequence(25)
    
    # 场景2: 产品编号进位
    print("\n2. 产品编号进位场景 (从9990开始生成20个零件号):")
    generator2 = PartNumberGenerator(5, 20)  # 外购件机械件
    generator2.product_number = 9990
    numbers2 = generator2.generate_sequence(20)
    
    # 场景3: 小类编码进位
    print("\n3. 小类编码进位场景 (从小类编码99，产品编号9990开始生成30个零件号):")
    generator3 = PartNumberGenerator(0, 40)  # 定制件电气件
    generator3.sub_category_code = 99
    generator3.product_number = 9990
    numbers3 = generator3.generate_sequence(30)
    
    print("\n" + "=" * 70)
    print("模拟完成!")

def analyze_part_number_structure(part_number):
    """分析零件号结构"""
    if len(part_number) != 11 or not part_number.isdigit():
        print(f"无效的零件号: {part_number}")
        return
    
    print(f"\n零件号 {part_number} 的结构分析:")
    print(f"  零部件类别编码 (1位): {part_number[0]}")
    print(f"  大类编码 (2位): {part_number[1:3]}")
    print(f"  小类编码 (2位): {part_number[3:5]}")
    print(f"  产品编号 (4位): {part_number[5:9]}")
    print(f"  版本号 (2位): {part_number[9:11]}")

if __name__ == '__main__':
    simulate_different_scenarios()
    
    # 分析几个示例零件号的结构
    print("\n零件号结构分析:")
    print("-" * 30)
    sample_numbers = ["00000000001", "00000999901", "52000000001"]
    for number in sample_numbers:
        analyze_part_number_structure(number)