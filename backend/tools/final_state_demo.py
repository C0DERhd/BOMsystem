#!/usr/bin/env python
"""
最终状态保持功能演示
"""

import json
import os

class PartNumberAppState:
    """零件号申请页面状态管理"""
    
    def __init__(self, storage_file="part_number_state.json"):
        self.storage_file = storage_file
        self.state = {
            'partCategory': '',
            'mainCategory': '',
            'subCategory': '',
            'generatedPartNumbers': [],
            'currentPartNumber': ''
        }
        self.load_state()
    
    def save_state(self):
        """保存状态到文件"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            print(f"状态已保存到 {self.storage_file}")
        except Exception as e:
            print(f"保存状态失败: {e}")
    
    def load_state(self):
        """从文件加载状态"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
                print(f"状态已从 {self.storage_file} 加载")
                return True
            except Exception as e:
                print(f"加载状态失败: {e}")
        return False
    
    def update_category(self, part_category=None, main_category=None, sub_category=None):
        """更新类别选择"""
        if part_category is not None:
            self.state['partCategory'] = part_category
        if main_category is not None:
            self.state['mainCategory'] = main_category
        if sub_category is not None:
            self.state['subCategory'] = sub_category
        self.save_state()
    
    def generate_part_number(self):
        """生成零件号"""
        # 简单的零件号生成逻辑
        category_code = '0' if self.state['partCategory'] == 'custom' else '5'
        main_code = '00' if self.state['mainCategory'] == 'optical' else \
                   '20' if self.state['mainCategory'] == 'mechanical' else '40'
        sub_code = '00'
        product_num = str(len(self.state['generatedPartNumbers'])).zfill(4)
        version = '01'
        
        new_part_number = f"{category_code}{main_code}{sub_code}{product_num}{version}"
        
        self.state['currentPartNumber'] = new_part_number
        self.state['generatedPartNumbers'].append(new_part_number)
        self.save_state()
        
        return new_part_number
    
    def clear_state(self):
        """清空状态"""
        self.state = {
            'partCategory': '',
            'mainCategory': '',
            'subCategory': '',
            'generatedPartNumbers': [],
            'currentPartNumber': ''
        }
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        print("状态已清空")
    
    def get_state(self):
        """获取当前状态"""
        return self.state.copy()
    
    def display_state(self):
        """显示当前状态"""
        print("\n当前页面状态:")
        print("-" * 30)
        print(f"零部件类别: {self.state['partCategory']}")
        print(f"大类: {self.state['mainCategory']}")
        print(f"小类: {self.state['subCategory']}")
        print(f"当前零件号: {self.state['currentPartNumber']}")
        print(f"已生成零件号数量: {len(self.state['generatedPartNumbers'])}")
        if self.state['generatedPartNumbers']:
            print("已生成的零件号:")
            for i, number in enumerate(self.state['generatedPartNumbers'], 1):
                print(f"  {i}. {number}")

def demo_state_persistence():
    """演示状态保持功能"""
    print("零件号申请页面状态保持功能演示")
    print("=" * 40)
    
    # 创建状态管理器
    app_state = PartNumberAppState()
    
    # 演示1: 初始状态
    print("\n1. 初始状态:")
    app_state.display_state()
    
    # 演示2: 选择类别并生成零件号
    print("\n2. 选择类别并生成零件号:")
    app_state.update_category(part_category='custom', main_category='optical', sub_category='lens_prism')
    print("选择类别: 定制件/光学件/透镜类")
    
    # 生成几个零件号
    for i in range(3):
        part_number = app_state.generate_part_number()
        print(f"  生成零件号 {i+1}: {part_number}")
    
    app_state.display_state()
    
    # 演示3: 模拟页面刷新/切换后恢复状态
    print("\n3. 模拟页面刷新/切换后恢复状态:")
    print("创建新的状态管理器实例...")
    new_app_state = PartNumberAppState()
    new_app_state.display_state()
    
    # 演示4: 继续操作
    print("\n4. 继续操作 - 生成更多零件号:")
    for i in range(2):
        part_number = new_app_state.generate_part_number()
        print(f"  生成零件号 {len(new_app_state.get_state()['generatedPartNumbers'])}: {part_number}")
    
    new_app_state.display_state()
    
    # 演示5: 更改类别
    print("\n5. 更改类别:")
    new_app_state.update_category(part_category='purchased', main_category='mechanical')
    print("更改类别为: 外购件/机械件")
    new_app_state.display_state()
    
    # 演示6: 清空状态
    print("\n6. 清空状态:")
    new_app_state.clear_state()
    new_app_state.display_state()
    
    print("\n演示完成!")

if __name__ == '__main__':
    demo_state_persistence()