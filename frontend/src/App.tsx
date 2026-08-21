import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';

import { store } from '@/store';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { getCurrentUser } from '@/store/slices/authSlice';

import Layout from '@/components/Layout';
import LoginPage from '@/pages/auth/LoginPage';
import RegisterPage from '@/pages/auth/RegisterPage';
import VisirayLoginPage from '@/pages/auth/VisirayLoginPage';  // 添加这一行
import Dashboard from '@/pages/Dashboard';
import BOMManagement from '@/pages/bom/BOMManagement';
import MaterialManagement from '@/pages/material/MaterialManagement';
import SupplierManagement from '@/pages/supplier/SupplierManagement';
import SupplierPriceManagement from '@/pages/supplier/SupplierPriceManagement';
import PartNumberApplicationPage from '@/pages/supplier/PartNumberApplicationPage';
import PartNumberRuleManagementPage from '@/pages/partNumber/PartNumberRuleManagementPage';
import PartNumberVersionManagementPage from '@/pages/partNumber/PartNumberVersionManagementPage';
import ContractNumberApplicationPage from '@/pages/contract/ContractNumberApplicationPage';
import InventoryManagement from '@/pages/inventory/InventoryManagement';
import InboundRecords from '@/pages/inbound/InboundRecords';
import OutboundRecords from '@/pages/outbound/OutboundRecords';
import PurchaseOrders from '@/pages/purchase/PurchaseOrders';
import InventoryDashboard from '@/pages/dashboard/inventory/InventoryDashboard';
import PurchaseDashboard from '@/pages/dashboard/purchase/PurchaseDashboard';
import SupplierDashboard from '@/pages/dashboard/supplier/SupplierDashboard';
import ProtectedRoute from '@/components/ProtectedRoute';
import ProfilePage from '@/pages/user/ProfilePage';

import './App.css';

// 设置dayjs为中文
dayjs.locale('zh-cn');

const AppContent: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isAuthenticated, loading } = useAppSelector((state) => state.auth);
  const { theme: appTheme } = useAppSelector((state) => state.ui);

  useEffect(() => {
    // 如果已登录，获取当前用户信息
    if (isAuthenticated) {
      dispatch(getCurrentUser());
    }
  }, [dispatch, isAuthenticated]);

  const themeConfig = {
    algorithm: appTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1890ff',
      borderRadius: 6,
    },
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        加载中...
      </div>
    );
  }

  return (
    <ConfigProvider 
      locale={zhCN} 
      theme={themeConfig}
    >
      <Router>
        <Routes>
          {/* 公开路由 */}
          <Route 
            path="/login" 
            element={
              isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
            } 
          />
          <Route 
            path="/visiray-login" 
            element={
              isAuthenticated ? <Navigate to="/dashboard" replace /> : <VisirayLoginPage />
            } 
          />
          <Route 
            path="/register" 
            element={
              isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />
            } 
          />
          
          {/* 受保护的路由 */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/inventory" element={<InventoryManagement />} />
              <Route path="/inbound" element={<InboundRecords />} />
              <Route path="/outbound" element={<OutboundRecords />} />
              <Route path="/purchase-orders" element={<PurchaseOrders />} />
              <Route path="/suppliers" element={<SupplierManagement />} />
              <Route path="/supplier-prices" element={<SupplierPriceManagement />} />
              <Route path="/part-number-application" element={<PartNumberApplicationPage />} />
              <Route path="/part-number-rules" element={<PartNumberRuleManagementPage />} />
              <Route path="/part-number-versions" element={<PartNumberVersionManagementPage />} />
              <Route path="/contract-number-application" element={<ContractNumberApplicationPage />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/bom/*" element={<BOMManagement />} />
              <Route path="/dashboard/inventory" element={<InventoryDashboard />} />
              <Route path="/dashboard/purchase" element={<PurchaseDashboard />} />
              <Route path="/dashboard/supplier" element={<SupplierDashboard />} />
            </Route>
          </Route>
          
          {/* 默认重定向 */}
          <Route 
            path="/" 
            element={<Navigate to="/dashboard" replace />} 
          />
          
          {/* 404页面 */}
          <Route 
            path="*" 
            element={
              <div style={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center', 
                height: '100vh' 
              }}>
                <h1>404 - 页面未找到</h1>
              </div>
            } 
          />
        </Routes>
      </Router>
    </ConfigProvider>
  );
};

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <AppContent />
    </Provider>
  );
};

export default App;


