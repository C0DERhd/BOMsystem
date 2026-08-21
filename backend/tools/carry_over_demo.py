#!/usr/bin/env python
"""
演示产品编号达到9999时的进位效果
"""

class PartNumberIncrementSystem:
    """零件号递增系统"""
    
    def __init__(self):
        # 模拟数据库存储
        self.database = {
            'generated_numbers': set(),  # 已生成的零件号
        }
    
    def apply_part_number(self, part_category_code, main_category_code):
        """申请零件号 - 核心功能"""
        # 生成零件号
        part_number = self._generate_part_number(part_category_code, main_category_code)
        
        # 保存到"数据库"
        self.database['generated_numbers'].add(part_number)
        
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
                print(f"    产品编号达到上限(9999)，小类编码从{sub_category_code-1:02d}进位到{sub_category_code:02d}")
                
                if sub_category_code > 99:
                    sub_category_code = 0
                    main_category_code += 1
                    print(f"    小类编码达到上限(99)，大类编码从{main_category_code-1:02d}进位到{main_category_code:02d}")
                    
                    if main_category_code > 99:
                        main_category_code = 0
                        part_category_code += 1
                        print(f"    大类编码达到上限(99)，零部件类别编码从{part_category_code-1}进位到{part_category_code}")
                        
                        if part_category_code > 9:
                            raise Exception("所有编码范围已用完")
        
        return part_number

def demo_carry_over():
    """演示进位效果"""
    print("产品编号进位效果演示")
    print("=" * 50)
    
    system = PartNumberIncrementSystem()
    
    # 演示1: 产品编号从9995到进位
    print("\n1. 产品编号从9995到进位:")
    print("-" * 30)
    
    # 预先添加9995-9999的零件号到数据库
    for i in range(9995, 10000):
        test_number = f"00000{i:04d}01"
        system.database['generated_numbers'].add(test_number)
        print(f"  预先添加: {test_number}")
    
    # 申请下一个零件号，应该会进位
    print("  申请下一个零件号:")
    next_number = system.apply_part_number(0, 0)
    print(f"  生成的零件号: {next_number}")
    
    # 再申请几个零件号
    for i in range(3):
        part_number = system.apply_part_number(0, 0)
        print(f"  第{i+1}次申请: {part_number}")
    
    # 演示2: 小类编码进位
    print("\n2. 小类编码进位演示:")
    print("-" * 30)
    
    # 预先添加小类编码99的产品编号9995-9999
    for i in range(9995, 10000):
        test_number = f"00099{i:04d}01"
        system.database['generated_numbers'].add(test_number)
    
    # 申请下一个零件号，应该会进位到小类编码00，大类编码+1
    print("  当前已存在零件号:")
    print("    00099999501")
    print("    00099999601")
    print("    00099999701")
    print("    00099999801")
    print("    00099999901")
    print("  申请下一个零件号:")
    next_number = system.apply_part_number(0, 0)
    print(f"  生成的零件号: {next_number}")
    print("  进位效果: 小类编码从99进位到00，产品编号重置为0000")
    
    # 演示3: 完整的进位链
    print("\n3. 完整的进位链示例:")
    print("-" * 30)
    print("  零件号格式: 类别(1)+大类(2)+小类(2)+产品编号(4)+版本(2)")
    print("  示例: 00000999901 -> 00001000001")
    print("        类别不变，大类不变，小类从00进位到01")
    print("        产品编号从9999重置为0000")
    
    # 演示4: 实际连续申请展示进位
    print("\n4. 实际连续申请展示进位:")
    print("-" * 30)
    # 创建新的系统实例
    system2 = PartNumberIncrementSystem()
    
    # 申请几个零件号
    print("  连续申请5个零件号:")
    for i in range(5):
        part_number = system2.apply_part_number(1, 20)  # 外购件机械件
        print(f"    {i+1}. {part_number}")
    
    # 模拟产品编号接近进位
    print("  模拟产品编号接近进位:")
    # 手动添加一些零件号到数据库
    for i in range(9997, 10000):
        test_number = f"12000{i:04d}01"
        system2.database['generated_numbers'].add(test_number)
    
    # 继续申请，展示进位
    print("  继续申请3个零件号，展示进位效果:")
    for i in range(3):
        part_number = system2.apply_part_number(1, 20)
        print(f"    {i+1}. {part_number}")

if __name__ == '__main__':
    demo_carry_over()