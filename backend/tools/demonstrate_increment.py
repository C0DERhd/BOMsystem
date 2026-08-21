#!/usr/bin/env python
"""
演示零件号递增功能的完整实现
"""

class PartNumberGenerator:
    """零件号生成器"""
    
    def __init__(self):
        # 模拟数据库中已存在的零件号
        self.existing_numbers = set()
        # 当前生成参数
        self.current_params = {
            'part_category_code': 0,
            'main_category_code': 0,
            'sub_category_code': 0,
            'product_number': 0,
            'version_number': 1
        }
    
    def generate_next_part_number(self, part_category_code=None, main_category_code=None):
        """生成下一个零件号"""
        # 如果提供了新的类别参数，更新当前参数
        if part_category_code is not None:
            self.current_params['part_category_code'] = part_category_code
        if main_category_code is not None:
            self.current_params['main_category_code'] = main_category_code
        
        # 生成零件号
        part_number = self._create_part_number()
        
        # 添加到已存在集合中
        self.existing_numbers.add(part_number)
        
        # 递增产品编号
        self.current_params['product_number'] += 1
        
        # 检查是否需要进位
        if self.current_params['product_number'] > 9999:
            self._carry_over()
        
        return part_number
    
    def _create_part_number(self):
        """创建零件号"""
        params = self.current_params
        return f"{params['part_category_code']}{params['main_category_code']:02d}{params['sub_category_code']:02d}{params['product_number']:04d}{params['version_number']:02d}"
    
    def _carry_over(self):
        """处理进位"""
        # 重置产品编号
        self.current_params['product_number'] = 0
        # 小类编码加1
        self.current_params['sub_category_code'] += 1
        print(f"    产品编号达到上限，小类编码进位到: {self.current_params['sub_category_code']:02d}")
        
        # 检查小类编码是否需要进位
        if self.current_params['sub_category_code'] > 99:
            self.current_params['sub_category_code'] = 0
            self.current_params['main_category_code'] += 1
            print(f"    小类编码达到上限，大类编码进位到: {self.current_params['main_category_code']:02d}")
            
            # 检查大类编码是否需要进位
            if not self._is_main_category_valid(self.current_params['main_category_code']):
                self.current_params['main_category_code'] = self._get_main_category_start_code(self.current_params['main_category_code'])
                self.current_params['part_category_code'] += 1
                print(f"    大类编码达到上限，零部件类别编码进位到: {self.current_params['part_category_code']}")
    
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

def demonstrate_increment():
    """演示递增功能"""
    print("零件号递增功能完整演示")
    print("=" * 50)
    
    generator = PartNumberGenerator()
    
    # 演示1: 正常递增
    print("\n1. 正常递增 (生成15个零件号):")
    print("-" * 30)
    for i in range(15):
        part_number = generator.generate_next_part_number()
        print(f"{i+1:2d}. {part_number}")
    
    # 演示2: 产品编号进位
    print("\n2. 产品编号进位演示:")
    print("-" * 30)
    # 手动设置接近进位点
    generator.current_params['product_number'] = 9997
    for i in range(6):
        part_number = generator.generate_next_part_number()
        print(f"{i+1:2d}. {part_number}")
    
    # 演示3: 不同类别的递增
    print("\n3. 不同类别的递增:")
    print("-" * 30)
    # 重置并切换到外购件机械件
    generator.current_params = {
        'part_category_code': 5,  # 外购件
        'main_category_code': 20, # 机械件
        'sub_category_code': 0,
        'product_number': 0,
        'version_number': 1
    }
    for i in range(5):
        part_number = generator.generate_next_part_number()
        print(f"{i+1:2d}. {part_number}")
    
    print(f"\n总共生成了 {len(generator.existing_numbers)} 个不同的零件号")

if __name__ == '__main__':
    demonstrate_increment()