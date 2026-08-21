import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Typography, List, Tag, Space, Spin } from 'antd';
import {
  DatabaseOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  StockOutlined,
  AlertOutlined
} from '@ant-design/icons';
import { Bar } from '@ant-design/plots';
import api from '@/services/api';

const { Title, Text } = Typography;

const InventoryDashboard: React.FC = () => {
  const [stats, setStats] = useState({
    totalInventoryValue: 0,
    totalItems: 0,
    lowStockItems: 0,
    overStockItems: 0
  });
  
  const [topInventoryItems, setTopInventoryItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(true);

  const [recentActivities] = useState([
    {
      id: 1,
      type: '入库',
      material: '定制机械件A',
      quantity: 50,
      time: '2小时前',
      status: 'success'
    },
    {
      id: 2,
      type: '出库',
      material: '外购机械件B',
      quantity: 30,
      time: '4小时前',
      status: 'info'
    },
    {
      id: 3,
      type: '盘点',
      material: '通用螺丝C',
      quantity: 1000,
      time: '6小时前',
      status: 'warning'
    }
  ]);

  const [lowStockItems] = useState([
    {
      id: 1,
      materialCode: '0102000501230',
      materialName: '定制机械件A',
      currentStock: 5,
      minStock: 10,
      warehouse: 'A仓库'
    },
    {
      id: 2,
      materialCode: '0252035045600',
      materialName: '外购机械件B',
      currentStock: 8,
      minStock: 15,
      warehouse: 'B仓库'
    }
  ]);

  // 获取仪表盘统计数据
  const fetchDashboardStats = async () => {
    try {
      setLoading(true);
      const response = await api.get('/visiray/dashboard/stats');
      if (response.data.success) {
        setStats({
          totalInventoryValue: response.data.data.total_inventory_value,
          totalItems: response.data.data.total_inventory_items,
          lowStockItems: 23, // 这些数据需要从后端获取
          overStockItems: 5
        });
      }
    } catch (error) {
      console.error('获取仪表盘统计数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取库存最多的货品
  const fetchTopInventoryItems = async () => {
    try {
      setChartLoading(true);
      const response = await api.get('/visiray/dashboard/inventory/top-items');
      if (response.data.success) {
        setTopInventoryItems(response.data.data);
      }
    } catch (error) {
      console.error('获取库存统计失败:', error);
    } finally {
      setChartLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardStats();
    fetchTopInventoryItems();
  }, []);

  const getStatusTag = (status: string) => {
    const statusMap = {
      success: { color: 'green', text: '完成' },
      info: { color: 'blue', text: '进行中' },
      warning: { color: 'orange', text: '预警' },
      error: { color: 'red', text: '异常' }
    };
    const statusInfo = statusMap[status as keyof typeof statusMap] || statusMap.info;
    return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>;
  };

  // 柱状图配置
  const barConfig = {
    data: topInventoryItems,
    xField: 'stock_quantity',
    yField: 'goods_name',
    seriesField: 'goods_name',
    legend: { position: 'top-left' },
    color: '#1890ff',
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          库存仪表盘
        </Title>
        <Text type="secondary">
          实时监控库存状态和变动情况
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
                title="库存总价值"
                value={stats.totalInventoryValue}
                prefix={<DatabaseOutlined />}
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
                title="物料种类"
                value={stats.totalItems}
                prefix={<StockOutlined />}
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
                title="低库存物料"
                value={stats.lowStockItems}
                prefix={<ArrowDownOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
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
                title="超储物料"
                value={stats.overStockItems}
                prefix={<ArrowUpOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 库存最多的货品柱状图 */}
        <Col xs={24} lg={12}>
          <Card 
            title="库存最多的货品" 
            style={{ height: '400px' }}
          >
            {chartLoading ? (
              <Spin />
            ) : topInventoryItems.length > 0 ? (
              <Bar {...barConfig} />
            ) : (
              <Text type="secondary">暂无数据</Text>
            )}
          </Card>
        </Col>

        {/* 低库存预警 */}
        <Col xs={24} lg={12}>
          <Card 
            title="低库存预警"
            style={{ height: '400px' }}
          >
            <List
              itemLayout="horizontal"
              dataSource={lowStockItems}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    title={item.materialName}
                    description={
                      <Space direction="vertical">
                        <Text type="secondary">物料编码: {item.materialCode}</Text>
                        <Text type="danger">当前库存: {item.currentStock} | 最低库存: {item.minStock}</Text>
                        <Text type="secondary">仓库: {item.warehouse}</Text>
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

export default InventoryDashboard;