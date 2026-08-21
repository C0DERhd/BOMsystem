import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Typography, List, Tag, Space, Spin } from 'antd';
import {
  ShoppingCartOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { Bar } from '@ant-design/plots';
import api from '@/services/api';

const { Title, Text } = Typography;

const PurchaseDashboard: React.FC = () => {
  const [stats, setStats] = useState({
    totalPurchaseValue: 0,
    pendingOrders: 0,
    completedOrders: 0,
    suppliers: 0
  });
  
  const [purchaseStats, setPurchaseStats] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(true);

  const [recentOrders] = useState([
    {
      id: 1,
      orderNo: 'PO20230501001',
      supplier: '精密机械厂',
      amount: 2550.00,
      date: '2023-05-01',
      status: 'completed'
    },
    {
      id: 2,
      orderNo: 'PO20230502002',
      supplier: '通用零件厂',
      amount: 3750.00,
      date: '2023-05-02',
      status: 'pending'
    },
    {
      id: 3,
      orderNo: 'PO20230503003',
      supplier: '电子元件厂',
      amount: 1200.00,
      date: '2023-05-03',
      status: 'shipped'
    }
  ]);

  const [suppliers] = useState([
    {
      id: 1,
      name: '精密机械厂',
      contact: '张经理',
      phone: '13800138001',
      rating: 4.8,
      status: 'active'
    },
    {
      id: 2,
      name: '通用零件厂',
      contact: '李主管',
      phone: '13800138002',
      rating: 4.5,
      status: 'active'
    }
  ]);

  // 获取采购仪表盘统计数据
  const fetchPurchaseDashboardStats = async () => {
    try {
      setLoading(true);
      const response = await api.get('/visiray/dashboard/stats');
      if (response.data.success) {
        setStats({
          totalPurchaseValue: response.data.data.total_purchase_orders * 1000, // 示例计算
          pendingOrders: 8, // 这些数据需要从后端获取
          completedOrders: response.data.data.total_purchase_orders,
          suppliers: response.data.data.total_suppliers
        });
      }
    } catch (error) {
      console.error('获取采购仪表盘统计数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取采购统计数据
  const fetchPurchaseStats = async () => {
    try {
      setChartLoading(true);
      const response = await api.get('/visiray/dashboard/purchase/stats');
      if (response.data.success) {
        setPurchaseStats(response.data.data);
      }
    } catch (error) {
      console.error('获取采购统计数据失败:', error);
    } finally {
      setChartLoading(false);
    }
  };

  useEffect(() => {
    fetchPurchaseDashboardStats();
    fetchPurchaseStats();
  }, []);

  const getStatusTag = (status: string) => {
    const statusMap = {
      completed: { color: 'green', text: '已完成' },
      pending: { color: 'orange', text: '待处理' },
      shipped: { color: 'blue', text: '已发货' },
      delayed: { color: 'red', text: '已延迟' }
    };
    const statusInfo = statusMap[status as keyof typeof statusMap] || statusMap.pending;
    return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>;
  };

  // 柱状图配置 - 采购订单状态分布
  const statusBarConfig = {
    data: Object.entries(purchaseStats.status_stats || {}).map(([status, count]) => ({
      status,
      count
    })),
    xField: 'count',
    yField: 'status',
    seriesField: 'status',
    legend: { position: 'top-left' },
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          采购仪表盘
        </Title>
        <Text type="secondary">
          实时监控采购订单和供应商状态
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
                title="采购总金额"
                value={stats.totalPurchaseValue}
                prefix={<DollarOutlined />}
                suffix="元"
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
                title="待处理订单"
                value={stats.pendingOrders}
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
                title="已完成订单"
                value={stats.completedOrders}
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
                title="合作供应商"
                value={stats.suppliers}
                prefix={<ShoppingCartOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 采购订单状态分布 */}
        <Col xs={24} lg={12}>
          <Card 
            title="采购订单状态分布" 
            style={{ height: '400px' }}
          >
            {chartLoading ? (
              <Spin />
            ) : Object.keys(purchaseStats.status_stats || {}).length > 0 ? (
              <Bar {...statusBarConfig} />
            ) : (
              <Text type="secondary">暂无数据</Text>
            )}
          </Card>
        </Col>

        {/* 供应商信息 */}
        <Col xs={24} lg={12}>
          <Card 
            title="重要供应商"
            style={{ height: '400px' }}
          >
            <List
              itemLayout="horizontal"
              dataSource={suppliers}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    title={item.name}
                    description={
                      <Space direction="vertical">
                        <Text type="secondary">联系人: {item.contact} | 电话: {item.phone}</Text>
                        <Text>评分: {item.rating} | 状态: <Tag color={item.status === 'active' ? 'green' : 'red'}>{item.status === 'active' ? '合作中' : '已暂停'}</Tag></Text>
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

export default PurchaseDashboard;