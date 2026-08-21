import React from 'react';
import { Outlet } from 'react-router-dom';
import { Layout as AntLayout, Menu, Avatar, Dropdown, Button, Space, Typography } from 'antd';
import {
  DashboardOutlined,
  BarsOutlined,
  InboxOutlined,
  TeamOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DatabaseOutlined,
  LoginOutlined,
  FileDoneOutlined,
  FileSearchOutlined,
  ShoppingCartOutlined,
  FileAddOutlined,
  AppstoreOutlined,
  ApartmentOutlined,
  DollarOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { logout } from '@/store/slices/authSlice';
import { toggleSidebar } from '@/store/slices/uiSlice';
import { usePermissions, PERMISSIONS } from '@/hooks/usePermissions';
import Permission from './Permission';

const { Header, Sider, Content } = AntLayout;
const { Title } = Typography;

const Layout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  
  const { user } = useAppSelector((state) => state.auth);
  const { sidebarCollapsed } = useAppSelector((state) => state.ui);
  const { hasPermission, isAdmin } = usePermissions();

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  const menuItems = [
    hasPermission(PERMISSIONS.BOM_READ) ? {
      key: '/bom',
      icon: <ApartmentOutlined />,
      label: 'BOM管理',
      onClick: () => navigate('/bom')
    } : null,
    {
      key: '/inventory',
      icon: <DatabaseOutlined />,
      label: '库存管理',
      onClick: () => navigate('/inventory')
    },
    {
      key: '/inbound',
      icon: <LoginOutlined />,
      label: '入库操作',
      onClick: () => navigate('/inbound')
    },
    {
      key: '/outbound',
      icon: <LogoutOutlined />,
      label: '出库操作',
      onClick: () => navigate('/outbound')
    },
    hasPermission(PERMISSIONS.SUPPLIER_READ) ? {
      key: '/suppliers',
      icon: <TeamOutlined />,
      label: '供应商信息',
      onClick: () => navigate('/suppliers')
    } : null,
    hasPermission(PERMISSIONS.SUPPLIER_READ) ? {
      key: '/supplier-prices',
      icon: <DollarOutlined />,
      label: '供应商报价管理',
      onClick: () => navigate('/supplier-prices')
    } : null,
    isAdmin() ? {
      key: '/part-number-application',
      icon: <FileAddOutlined />,
      label: '零件号申请/管理',
      onClick: () => navigate('/part-number-application')
    } : null,
    isAdmin() ? {
      key: '/part-number-versions',
      icon: <BarsOutlined />,
      label: '零件版本管理',
      onClick: () => navigate('/part-number-versions')
    } : null,
    isAdmin() ? {
      key: '/part-number-rules',
      icon: <SettingOutlined />,
      label: '零件号规则管理',
      onClick: () => navigate('/part-number-rules')
    } : null,
    {
      key: '/purchase-orders',
      icon: <ShoppingCartOutlined />,
      label: '采购单',
      onClick: () => navigate('/purchase-orders')
    },
    isAdmin() ? {
      key: '/contract-number-application',
      icon: <FileDoneOutlined />,
      label: '合同号申请',
      onClick: () => navigate('/contract-number-application')
    } : null,
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
      children: [
        {
          key: '/dashboard/inventory',
          icon: <DatabaseOutlined />,
          label: '库存仪表盘',
          onClick: () => navigate('/dashboard/inventory')
        },
        {/*{
          key: '/dashboard/purchase',
          icon: <ShoppingCartOutlined />,
          label: '采购仪表盘',
          onClick: () => navigate('/dashboard/purchase')
        },
        {
          key: '/dashboard/supplier',
          icon: <TeamOutlined />,
          label: '供应商仪表盘',
          onClick: () => navigate('/dashboard/supplier')
        }*/}
      ]
    }
  ].filter(Boolean) as any;

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => navigate('/profile')
    },
    {
      type: 'divider' as const
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout
    }
  ];

  const getSelectedKeys = () => {
    const path = location.pathname;
    if (path.startsWith('/bom')) return ['/bom'];
    if (path.startsWith('/inventory')) return ['/inventory'];
    if (path.startsWith('/inbound')) return ['/inbound'];
    if (path.startsWith('/outbound')) return ['/outbound'];
    if (path.startsWith('/purchase-orders')) return ['/purchase-orders'];
    if (path.startsWith('/supplier-prices')) return ['/supplier-prices'];
    if (path.startsWith('/suppliers')) return ['/suppliers'];
    if (path.startsWith('/part-number-application')) return ['/part-number-application'];
    if (path.startsWith('/part-number-rules')) return ['/part-number-rules'];
    if (path.startsWith('/part-number-versions')) return ['/part-number-versions'];
    if (path.startsWith('/contract-number-application')) return ['/contract-number-application'];
    if (path.startsWith('/dashboard/inventory')) return ['/dashboard', '/dashboard/inventory'];
    if (path.startsWith('/dashboard/purchase')) return ['/dashboard', '/dashboard/purchase'];
    if (path.startsWith('/dashboard/supplier')) return ['/dashboard', '/dashboard/supplier'];
    if (path.startsWith('/dashboard')) return ['/dashboard'];
    return [path];
  };

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={sidebarCollapsed}
        width={240}
        style={{
          background: '#001529'
        }}
      >
        <div style={{
          height: '64px',
          margin: '16px',
          background: 'linear-gradient(135deg, #1890ff 0%, #0050b3 100%)',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
          cursor: 'pointer'
        }}
        onClick={() => navigate('/dashboard')}
        >
          <Title 
            level={4} 
            style={{ 
              color: 'white', 
              margin: 0,
              fontSize: sidebarCollapsed ? '16px' : '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontWeight: 'bold',
              textShadow: '0 2px 4px rgba(0,0,0,0.3)'
            }}
          >
            <AppstoreOutlined style={{ fontSize: sidebarCollapsed ? '16px' : '20px' }} />
            {sidebarCollapsed ? '' : 'BOM管理系统'}
          </Title>
        </div>
        
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={getSelectedKeys()}
          items={menuItems}
          style={{ borderRight: 0 }}
        />
      </Sider>

      <AntLayout>
        <Header style={{
          padding: '0 16px',
          background: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}>
          <Space>
            <Button
              type="text"
              icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => dispatch(toggleSidebar())}
              style={{
                fontSize: '16px',
                width: 40,
                height: 40
              }}
            />
          </Space>

          <Space>
            <Dropdown 
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              arrow
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar 
                  size="default" 
                  icon={<UserOutlined />}
                  style={{ backgroundColor: '#1890ff' }}
                />
                <span>{user?.name || '用户'}</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        <Content style={{
          margin: '16px',
          padding: '24px',
          background: '#fff',
          borderRadius: '8px',
          overflow: 'auto'
        }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

export default Layout;
