import React, { useState, useEffect } from 'react';

// 模拟零件号申请页面组件
const PartNumberApplicationDemo: React.FC = () => {
  // 状态定义
  const [partCategory, setPartCategory] = useState<string>('');
  const [mainCategory, setMainCategory] = useState<string>('');
  const [subCategory, setSubCategory] = useState<string>('');
  const [generatedPartNumbers, setGeneratedPartNumbers] = useState<string[]>([]);
  const [currentPartNumber, setCurrentPartNumber] = useState<string>('');

  // 模拟数据
  const partCategories = [
    { value: 'custom', label: '定制件' },
    { value: 'purchased', label: '外购件' }
  ];

  const mainCategories = [
    { value: 'optical', label: '光学件' },
    { value: 'mechanical', label: '机械件' },
    { value: 'electrical', label: '电气/子件' }
  ];

  // 模拟生成零件号
  const generatePartNumber = () => {
    // 简单的零件号生成逻辑
    const categoryCode = partCategory === 'custom' ? '0' : '5';
    const mainCode = mainCategory === 'optical' ? '00' : 
                    mainCategory === 'mechanical' ? '20' : '40';
    const subCode = '00';
    const productNum = generatedPartNumbers.length.toString().padStart(4, '0');
    const version = '01';
    
    const newPartNumber = `${categoryCode}${mainCode}${subCode}${productNum}${version}`;
    
    setCurrentPartNumber(newPartNumber);
    setGeneratedPartNumbers(prev => [...prev, newPartNumber]);
  };

  // 页面加载时恢复状态
  useEffect(() => {
    const savedState = localStorage.getItem('partNumberDemoState');
    if (savedState) {
      try {
        const state = JSON.parse(savedState);
        setPartCategory(state.partCategory || '');
        setMainCategory(state.mainCategory || '');
        setSubCategory(state.subCategory || '');
        setGeneratedPartNumbers(state.generatedPartNumbers || []);
        setCurrentPartNumber(state.currentPartNumber || '');
      } catch (e) {
        console.error('恢复状态失败:', e);
      }
    }
  }, []);

  // 状态变化时保存到localStorage
  useEffect(() => {
    const state = {
      partCategory,
      mainCategory,
      subCategory,
      generatedPartNumbers,
      currentPartNumber
    };
    localStorage.setItem('partNumberDemoState', JSON.stringify(state));
  }, [partCategory, mainCategory, subCategory, generatedPartNumbers, currentPartNumber]);

  // 清空状态
  const clearState = () => {
    setPartCategory('');
    setMainCategory('');
    setSubCategory('');
    setGeneratedPartNumbers([]);
    setCurrentPartNumber('');
    localStorage.removeItem('partNumberDemoState');
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>零件号申请页面状态保持演示</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <h2>选择类别</h2>
        <div style={{ marginBottom: '10px' }}>
          <label>零部件类别: </label>
          <select 
            value={partCategory} 
            onChange={(e) => setPartCategory(e.target.value)}
            style={{ marginLeft: '10px', padding: '5px' }}
          >
            <option value="">请选择</option>
            {partCategories.map(cat => (
              <option key={cat.value} value={cat.value}>{cat.label}</option>
            ))}
          </select>
        </div>
        
        <div style={{ marginBottom: '10px' }}>
          <label>大类: </label>
          <select 
            value={mainCategory} 
            onChange={(e) => setMainCategory(e.target.value)}
            disabled={!partCategory}
            style={{ marginLeft: '10px', padding: '5px' }}
          >
            <option value="">请选择</option>
            {mainCategories.map(cat => (
              <option key={cat.value} value={cat.value}>{cat.label}</option>
            ))}
          </select>
        </div>
        
        <div style={{ marginBottom: '10px' }}>
          <label>小类: </label>
          <select 
            value={subCategory} 
            onChange={(e) => setSubCategory(e.target.value)}
            disabled={!mainCategory}
            style={{ marginLeft: '10px', padding: '5px' }}
          >
            <option value="">请选择</option>
            <option value="type1">类型1</option>
            <option value="type2">类型2</option>
            <option value="type3">类型3</option>
          </select>
        </div>
      </div>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={generatePartNumber} 
          disabled={!partCategory || !mainCategory}
          style={{ padding: '10px 20px', backgroundColor: '#1890ff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          申请零件号
        </button>
        
        <button 
          onClick={clearState}
          style={{ marginLeft: '10px', padding: '10px 20px', backgroundColor: '#ff4d4f', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          清空状态
        </button>
      </div>
      
      {currentPartNumber && (
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f0f2f5', borderRadius: '4px' }}>
          <h3>生成的零件号:</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
            {currentPartNumber}
          </div>
        </div>
      )}
      
      {generatedPartNumbers.length > 0 && (
        <div>
          <h3>已生成的零件号列表:</h3>
          <ul style={{ listStyleType: 'none', padding: 0 }}>
            {generatedPartNumbers.map((number, index) => (
              <li key={index} style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>
                {index + 1}. {number}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#e6f7ff', borderRadius: '4px' }}>
        <h3>状态保持说明:</h3>
        <ul>
          <li>选择的类别会在页面刷新或切换后保持</li>
          <li>已生成的零件号列表会持久保存</li>
          <li>状态保存在浏览器的localStorage中</li>
          <li>可以点击"清空状态"按钮重置所有状态</li>
        </ul>
      </div>
    </div>
  );
};

export default PartNumberApplicationDemo;