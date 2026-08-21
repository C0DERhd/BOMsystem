import React from 'react';
import { Card, Typography, Table, Space, Button, Input } from 'antd';
import { SearchOutlined, PlusOutlined } from '@ant-design/icons';

const { Title } = Typography;

const MaterialManagement: React.FC = () => {
  // 模拟数据
  const dataSource = [
    {
      key: '1',
      materialCode: '0102000501230',
      materialName: '定制机械件A',
      category: '机械件',
      unit: '个',
      spec: 'M8×20',
      supplier: '精密机械厂',
      status: '启用'
    },
    {
      key: '2',
      materialCode: '0252035045600',
      materialName: '外购机械件B',
      category: '机械件',
      unit: '个',
      spec: 'Φ10×50',
      supplier: '通用零件厂',
      status: '启用'
    },
    {
      key: '3',
      materialCode: '0103001000015',
      materialName: '定制电子件C',
      category: '电子件',
      unit: '个',
      spec: '2.54mm间距',
      supplier: '电子元件厂',
      status: '停用'
    }
  ];

  const columns = [
    {
      title: '物料编码',
      dataIndex: 'materialCode',
      key: 'materialCode',
    },
    {
      title: '物料名称',
      dataIndex: 'materialName',
      key: 'materialName',
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
    },
    {
      title: '规格',
      dataIndex: 'spec',
      key: 'spec',
    },
    {
      title: '供应商',
      dataIndex: 'supplier',
      key: 'supplier',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space size="middle">
          <a>查看详情</a>
          <a>编辑</a>
        </Space>
      ),
    },
  ];

  return (
    <Card>
      <div style={{ marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0, display: 'inline-block' }}>物料管理</Title>
        <div style={{ float: 'right' }}>
          <Space>
            <Input placeholder="搜索物料" prefix={<SearchOutlined />} style={{ width: 200 }} />
            <Button type="primary" icon={<PlusOutlined />}>新增物料</Button>
          </Space>
        </div>
      </div>
      
      <Table dataSource={dataSource} columns={columns} pagination={{ pageSize: 10 }} />
    </Card>
  );
};

export default MaterialManagement;