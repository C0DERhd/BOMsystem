import React, { useState } from 'react';
import { Card, Form, Select, Input, Button, message, Row, Col, Divider } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

const { Option } = Select;

const PartNumberApplication: React.FC = () => {
  const [form] = Form.useForm();
  const [partCategory, setPartCategory] = useState<string | null>(null);
  const [mainCategory, setMainCategory] = useState<string | null>(null);
  const [subCategory, setSubCategory] = useState<string | null>(null);
  const [isMainCategoryDisabled, setIsMainCategoryDisabled] = useState(true);
  const [isSubCategoryDisabled, setIsSubCategoryDisabled] = useState(true);

  // 大类选项
  const mainCategoryOptions = [
    { value: 'optical', label: '光学件' },
    { value: 'mechanical', label: '机械件' },
    { value: 'electrical', label: '电气/子件' },
    { value: 'software', label: '软件' },
    { value: 'chemical', label: '化学品' },
    { value: 'other', label: '其他' }
  ];

  // 小类选项，根据零部件类别和大类动态变化
  const getSubCategoryOptions = () => {
    if (!partCategory || !mainCategory) return [];

    // 光学件
    if (mainCategory === 'optical') {
      return [
        { value: 'light_source', label: '光源器件' },
        { value: 'light_transmission', label: '光传输器件' },
        { value: 'lens_prism', label: '光学透镜/棱镜' },
        { value: 'optical_filter', label: '光学滤光片' },
        { value: 'optical_sensor', label: '光学传感器' },
        { value: 'light_modulator', label: '光调制器件' },
        { value: 'display_imaging', label: '显示与成像' },
        { value: 'optical_other', label: '其他类' }
      ];
    }

    // 机械件
    if (mainCategory === 'mechanical') {
      if (partCategory === 'purchased') {
        return [
          { value: 'non_standard', label: '非标机械类' },
          { value: 'transmission', label: '传动类' },
          { value: 'fasteners', label: '标准紧固件' },
          { value: 'spring', label: '弹簧类' },
          { value: 'net_filter', label: '网及筛滤器材' },
          { value: 'mechanical_other', label: '其他类' }
        ];
      } else if (partCategory === 'custom') {
        return [
          { value: 'iron_steel', label: '铁、刚、合金钢' },
          { value: 'copper_aluminum', label: '铜、铝、镁、锌、锡、镍、谦、钛等及其合金' },
          { value: 'other_metal', label: '其他金属' },
          { value: 'plastic', label: '常用塑料类' },
          { value: 'rubber', label: '常用橡胶类' },
          { value: 'glass_ceramic', label: '玻璃、陶瓷等' },
          { value: 'material_other', label: '其他' },
          { value: 'reserved', label: '预留' }
        ];
      }
    }

    // 电气/子件
    if (mainCategory === 'electrical') {
      if (partCategory === 'purchased') {
        return [
          { value: 'passive', label: '被动元件类' },
          { value: 'semiconductor', label: '半导体器件类' },
          { value: 'electromechanical', label: '机电与连接类' },
          { value: 'structure', label: '结构件类' },
          { value: 'power', label: '电源与储能类' },
          { value: 'sensor', label: '传感器类' },
          { value: 'optical_display', label: '光学与显示类' },
          { value: 'electrical_other', label: '其他类' }
        ];
      } else if (partCategory === 'custom') {
        return [
          { value: 'custom_power', label: '定制电源与储能' },
          { value: 'custom_control', label: '定制控制与驱动' },
          { value: 'custom_sensor', label: '定制传感与检测' },
          { value: 'custom_signal', label: '定制信号与通信' },
          { value: 'custom_pcb', label: '定制PCB与功能子版' },
          { value: 'custom_heat', label: '定制散热与结构件' },
          { value: 'custom_electromechanical', label: '定制机电与光电部件' },
          { value: 'custom_electrical_other', label: '其他定制电气件' }
        ];
      }
    }

    // 软件
    if (mainCategory === 'software') {
      return [
        { value: 'system_software', label: '系统与基础软件' },
        { value: 'office_software', label: '通用办公软件' },
        { value: 'security_software', label: '安全与管理软件' },
        { value: 'engineering_software', label: '工程与研发通用软件' },
        { value: 'development_tools', label: '开发工具' },
        { value: 'software_other', label: '其他外购软件' }
      ];
    }

    // 化学品
    if (mainCategory === 'chemical') {
      return [
        { value: 'inorganic', label: '基础无机化学品' },
        { value: 'organic', label: '有机化学品' },
        { value: 'polymer', label: '聚合物与树脂' },
        { value: 'reagent', label: '试剂与实验室化学品' },
        { value: 'functional', label: '功能化学品' },
        { value: 'material_chemical', label: '材料化学品' },
        { value: 'hazardous', label: '危险化学品' },
        { value: 'chemical_other', label: '其他化学品' }
      ];
    }

    // 其他大类不提供小类选项
    return [];
  };

  // 处理零部件类别变化
  const handlePartCategoryChange = (value: string) => {
    setPartCategory(value);
    setMainCategory(null);
    setSubCategory(null);
    form.setFieldsValue({ mainCategory: null, subCategory: null });
    
    if (value) {
      setIsMainCategoryDisabled(false);
      setIsSubCategoryDisabled(true);
    } else {
      setIsMainCategoryDisabled(true);
      setIsSubCategoryDisabled(true);
    }
  };

  // 处理大类变化
  const handleMainCategoryChange = (value: string) => {
    setMainCategory(value);
    setSubCategory(null);
    form.setFieldsValue({ subCategory: null });
    
    if (value && value !== 'other') {
      setIsSubCategoryDisabled(false);
    } else {
      setIsSubCategoryDisabled(true);
    }
  };

  // 处理小类变化
  const handleSubCategoryChange = (value: string) => {
    setSubCategory(value);
  };

  // 提交表单
  const onFinish = (values: any) => {
    console.log('Received values:', values);
    message.success('零件号申请已提交！');
    form.resetFields();
    setPartCategory(null);
    setMainCategory(null);
    setSubCategory(null);
    setIsMainCategoryDisabled(true);
    setIsSubCategoryDisabled(true);
  };

  return (
    <Card title="零件号一键申请" style={{ marginTop: 20 }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="partCategory"
              label="零部件类别"
              rules={[{ required: true, message: '请选择零部件类别!' }]}
            >
              <Select
                placeholder="请选择零部件类别"
                onChange={handlePartCategoryChange}
              >
                <Option value="custom">定制件</Option>
                <Option value="purchased">外购件</Option>
              </Select>
            </Form.Item>
          </Col>
          
          <Col span={8}>
            <Form.Item
              name="mainCategory"
              label="大类"
              rules={[{ required: true, message: '请选择大类!' }]}
            >
              <Select
                placeholder="请选择大类"
                onChange={handleMainCategoryChange}
                disabled={isMainCategoryDisabled}
              >
                {mainCategoryOptions.map(option => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          
          <Col span={8}>
            <Form.Item
              name="subCategory"
              label="小类"
              rules={[{ required: mainCategory !== 'other' && mainCategory !== null, message: '请选择小类!' }]}
            >
              <Select
                placeholder="请选择小类"
                onChange={handleSubCategoryChange}
                disabled={isSubCategoryDisabled}
              >
                {getSubCategoryOptions().map(option => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>
        
        <Divider />
        
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="partName"
              label="零件名称"
              rules={[{ required: true, message: '请输入零件名称!' }]}
            >
              <Input placeholder="请输入零件名称" />
            </Form.Item>
          </Col>
          
          <Col span={12}>
            <Form.Item
              name="partDescription"
              label="零件描述"
            >
              <Input.TextArea placeholder="请输入零件描述" rows={2} />
            </Form.Item>
          </Col>
        </Row>
        
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="supplier"
              label="供应商"
            >
              <Input placeholder="请输入供应商" />
            </Form.Item>
          </Col>
          
          <Col span={8}>
            <Form.Item
              name="material"
              label="材料"
            >
              <Input placeholder="请输入材料" />
            </Form.Item>
          </Col>
          
          <Col span={8}>
            <Form.Item
              name="specification"
              label="规格"
            >
              <Input placeholder="请输入规格" />
            </Form.Item>
          </Col>
        </Row>
        
        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>
            申请零件号
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default PartNumberApplication;