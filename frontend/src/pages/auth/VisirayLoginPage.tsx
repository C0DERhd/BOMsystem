import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch } from '@/store/hooks';
import { login } from '@/store/slices/authSlice';
import api from '@/services/api';

const { Title, Text } = Typography;

const VisirayLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { account: string; password: string }) => {
    try {
      setLoading(true);
      // 使用主系统的登录API
      const response = await api.post('/auth/login', {
        username: values.account,
        password: values.password
      });
      
      if (response.data.success) {
        // 创建符合authSlice要求的认证数据结构
        const authData = {
          user: response.data.data.user,
          access_token: response.data.data.access_token,
          refresh_token: response.data.data.refresh_token,
          permissions: response.data.data.permissions
        };
        
        // 更新Redux store中的认证状态
        dispatch(login.fulfilled(authData, 'auth/login', { 
          username: values.account, 
          password: values.password 
        }));
        
        message.success('登录成功');
        // 跳转到系统概览页面
        navigate('/dashboard');
      } else {
        message.error(response.data.message || '登录失败');
      }
    } catch (error: any) {
      // 统一显示"账户或密码错误"提示
      message.error('账户或密码错误');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card 
        style={{ 
          width: '100%',
          maxWidth: 450,
          padding: 24,
          borderRadius: 8,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ color: '#1890ff', marginBottom: 8 }}>
            Visiray系统
          </Title>
          <Text type="secondary">请登录您的账户</Text>
        </div>

        <Form
          name="visiray_login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="account"
            rules={[
              { required: true, message: '请输入账户' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="账户"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              icon={<LoginOutlined />}
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Text>
            还没有账户？<a onClick={() => navigate('/register')}>立即注册</a>
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default VisirayLoginPage;