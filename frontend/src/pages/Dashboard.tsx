import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Typography, message } from 'antd';
import {
  BarsOutlined,
  TeamOutlined,
  DatabaseOutlined,
  LoginOutlined,
  LogoutOutlined,
  ShoppingCartOutlined,
  RiseOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';

const { Title, Text } = Typography;

interface StatCardProps {
  title: string;
  value: number;
  suffix?: string;
  prefix?: React.ReactNode;
  color?: string;
  onClick?: () => void;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, suffix, prefix, color = '#1890ff', onClick }) => (
  <Card hoverable onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
    <Statistic
      title={title}
      value={value}
      suffix={suffix}
      prefix={prefix}
      valueStyle={{ color }}
    />
  </Card>
);

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalBOMs: 0,
    totalSuppliers: 0,
    totalInbound: 0,
    totalOutbound: 0,
    totalPurchase: 0
  });
  const [loading, setLoading] = useState(true);

  // 获取统计数据
  const fetchStats = async () => {
    try {
      setLoading(true);
      // 获取仪表盘统计数据
      const response = await api.get('/visiray/dashboard/stats');
      if (response.data.success) {
        const data = response.data.data;
        setStats({
          totalBOMs: data.total_inventory_items, // 使用库存项目总数作为BOM总数
          totalSuppliers: data.total_suppliers,
          totalInbound: data.total_inbound_records,
          totalOutbound: data.total_outbound_records,
          totalPurchase: data.total_purchase_orders
        });
      } else {
        message.error(response.data.message || '获取统计数据失败');
      }
    } catch (error) {
      console.error('获取统计数据失败:', error);
      message.error('获取统计数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          系统概览
        </Title>
        <Text type="secondary">
          欢迎回来！这里是您的工作概览
        </Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={4}>
          <StatCard
            title="BOM总数"
            value={stats.totalBOMs}
            prefix={<BarsOutlined />}
            color="#1890ff"
            onClick={() => navigate('/inventory')}
          />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <StatCard
            title="入库记录"
            value={stats.totalInbound}
            prefix={<LoginOutlined />}
            color="#52c41a"
            onClick={() => navigate('/inbound')}
          />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <StatCard
            title="出库记录"
            value={stats.totalOutbound}
            prefix={<LogoutOutlined />}
            color="#ff4d4f"
            onClick={() => navigate('/outbound')}
          />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <StatCard
            title="采购单数"
            value={stats.totalPurchase}
            prefix={<ShoppingCartOutlined />}
            color="#1890ff"
            onClick={() => navigate('/purchase-orders')}
          />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <StatCard
            title="供应商数量"
            value={stats.totalSuppliers}
            prefix={<TeamOutlined />}
            color="#faad14"
            onClick={() => navigate('/suppliers')}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 快速导航 */}
        <Col xs={24} lg={24}>
          <Card 
            title="快速导航" 
            style={{ height: '400px' }}
          >
            <Row gutter={[16, 16]}>
              {/* 第一行 */}
              <Col span={6}>
                <Card 
                  hoverable 
                  onClick={() => navigate('/inventory')}
                  style={{ textAlign: 'center', cursor: 'pointer' }}
                >
                  <DatabaseOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
                  <div>库存管理</div>
                </Card>
              </Col>
              <Col span={6}>
                <Card 
                  hoverable 
                  onClick={() => navigate('/inbound')}
                  style={{ textAlign: 'center', cursor: 'pointer' }}
                >
                  <LoginOutlined style={{ fontSize: '32px', color: '#52c41a' }} />
                  <div>入库操作</div>
                </Card>
              </Col>
              <Col span={6}>
                <Card 
                  hoverable 
                  onClick={() => navigate('/outbound')}
                  style={{ textAlign: 'center', cursor: 'pointer' }}
                >
                  <LogoutOutlined style={{ fontSize: '32px', color: '#ff4d4f' }} />
                  <div>出库操作</div>
                </Card>
              </Col>
              <Col span={6}>
                <Card 
                  hoverable 
                  onClick={() => navigate('/purchase-orders')}
                  style={{ textAlign: 'center', cursor: 'pointer' }}
                >
                  <ShoppingCartOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
                  <div>采购单</div>
                </Card>
              </Col>
              
              {/* 第二行 */}
              <Col span={6}>
                <Card 
                  hoverable 
                  onClick={() => navigate('/suppliers')}
                  style={{ textAlign: 'center', cursor: 'pointer' }}
                >
                  <TeamOutlined style={{ fontSize: '32px', color: '#faad14' }} />
                  <div>供应商信息</div>
                </Card>
              </Col>
              <Col span={6}>
                <Card 
                  hoverable 
                  onClick={() => navigate('/dashboard/inventory')}
                  style={{ textAlign: 'center', cursor: 'pointer' }}
                >
                  <DatabaseOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
                  <div>库存仪表盘</div>
                </Card>
              </Col>
              <Col span={6}>
                <Card 
                  hoverable 
                  onClick={() => navigate('/dashboard/purchase')}
                  style={{ textAlign: 'center', cursor: 'pointer' }}
                >
                  <ShoppingCartOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
                  <div>采购仪表盘</div>
                </Card>
              </Col>
              <Col span={6}>
                <Card 
                  hoverable 
                  onClick={() => navigate('/dashboard/supplier')}
                  style={{ textAlign: 'center', cursor: 'pointer' }}
                >
                  <RiseOutlined style={{ fontSize: '32px', color: '#722ed1' }} />
                  <div>供应商仪表盘</div>
                </Card>
              </Col>

            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;