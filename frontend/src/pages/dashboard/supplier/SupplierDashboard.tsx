import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Typography, List, Tag, Space, Rate, Spin } from 'antd';
import {
  TeamOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  StarOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { Pie } from '@ant-design/plots';
import api from '@/services/api';

const { Title, Text } = Typography;

const SupplierDashboard: React.FC = () => {
  const [stats, setStats] = useState({
    totalSuppliers: 0,
    activeSuppliers: 0,
    pendingSuppliers: 0,
    avgRating: 0
  });
  
  const [supplierStats, setSupplierStats] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(true);

  const [suppliers] = useState([
    {
      id: 1,
      name: '精密机械厂',
      contact: '张经理',
      phone: '13800138001',
      rating: 4.8,
      cooperationYears: 5,
      status: 'active',
      recentOrder: 'PO20230501001'
    },
    {
      id: 2,
      name: '通用零件厂',
      contact: '李主管',
      phone: '13800138002',
      rating: 4.5,
      cooperationYears: 3,
      status: 'active',
      recentOrder: 'PO20230502002'
    },
    {
      id: 3,
      name: '电子元件厂',
      contact: '王工程师',
      phone: '13800138003',
      rating: 4.2,
      cooperationYears: 2,
      status: 'pending',
      recentOrder: 'PO20230503003'
    }
  ]);

  const [evaluations] = useState([
    {
      id: 1,
      supplier: '精密机械厂',
      orderNo: 'PO20230501001',
      deliveryTime: '按时',
      quality: '优秀',
      service: '良好',
      overall: 4.8,
      date: '2023-05-01'
    },
    {
      id: 2,
      supplier: '通用零件厂',
      orderNo: 'PO20230502002',
      deliveryTime: '延迟1天',
      quality: '良好',
      service: '一般',
      overall: 4.0,
      date: '2023-05-02'
    }
  ]);

  // 获取供应商仪表盘统计数据
  const fetchSupplierDashboardStats = async () => {
    try {
      setLoading(true);
      const response = await api.get('/visiray/dashboard/stats');
      if (response.data.success) {
        setStats({
          totalSuppliers: response.data.data.total_suppliers,
          activeSuppliers: 42, // 这些数据需要从后端获取
          pendingSuppliers: 3,
          avgRating: 4.6
        });
      }
    } catch (error) {
      console.error('获取供应商仪表盘统计数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取供应商统计数据
  const fetchSupplierStats = async () => {
    try {
      setChartLoading(true);
      const response = await api.get('/visiray/dashboard/supplier/stats');
      if (response.data.success) {
        setSupplierStats(response.data.data);
      }
    } catch (error) {
      console.error('获取供应商统计数据失败:', error);
    } finally {
      setChartLoading(false);
    }
  };

  useEffect(() => {
    fetchSupplierDashboardStats();
    fetchSupplierStats();
  }, []);

  // 饼图配置 - 供应商状态分布
  const pieConfig = {
    data: [
      { type: '合作中', value: stats.activeSuppliers },
      { type: '待审核', value: stats.pendingSuppliers },
      { type: '已暂停', value: stats.totalSuppliers - stats.activeSuppliers - stats.pendingSuppliers }
    ],
    angleField: 'value',
    colorField: 'type',
    label: {
      text: 'value',
      formatter: (v: any) => `${v}个`,
    },
    legend: { color: { title: false } },
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          供应商仪表盘
        </Title>
        <Text type="secondary">
          实时监控供应商合作状态和绩效评估
        </Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            {loading ? (
              <Spin />
            ) : (
              <Statistic
                title="供应商总数"
                value={stats.totalSuppliers}
                prefix={<TeamOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            {loading ? (
              <Spin />
            ) : (
              <Statistic
                title="合作中供应商"
                value={stats.activeSuppliers}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            {loading ? (
              <Spin />
            ) : (
              <Statistic
                title="待审核供应商"
                value={stats.pendingSuppliers}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            {loading ? (
              <Spin />
            ) : (
              <Statistic
                title="平均评分"
                value={stats.avgRating}
                prefix={<StarOutlined />}
                precision={1}
                valueStyle={{ color: '#722ed1' }}
              />
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 供应商状态分布 */}
        <Col xs={24} lg={12}>
          <Card 
            title="供应商状态分布" 
            style={{ height: '400px' }}
          >
            {chartLoading ? (
              <Spin />
            ) : (
              <Pie {...pieConfig} />
            )}
          </Card>
        </Col>

        {/* 最近评估 */}
        <Col xs={24} lg={12}>
          <Card 
            title="最近供应商评估"
            style={{ height: '400px' }}
          >
            <List
              itemLayout="horizontal"
              dataSource={evaluations}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    title={item.supplier}
                    description={
                      <Space direction="vertical">
                        <Text type="secondary">订单号: {item.orderNo} | 日期: {item.date}</Text>
                        <Space>
                          <Text>交期: {item.deliveryTime}</Text>
                          <Text>质量: {item.quality}</Text>
                          <Text>服务: {item.service}</Text>
                        </Space>
                        <Space>
                          <Text>综合评分:</Text>
                          <Rate disabled defaultValue={item.overall} allowHalf style={{ fontSize: 12 }} />
                          <Text type="secondary">{item.overall}分</Text>
                        </Space>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default SupplierDashboard;