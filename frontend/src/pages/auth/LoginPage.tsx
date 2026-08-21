import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Divider, Space } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { login } from '@/store/slices/authSlice';
import { LoginForm } from '@/types';

const { Title, Text } = Typography;

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { loading } = useAppSelector((state) => state.auth);
  const [ssoEnabled, setSSOEnabled] = useState(false);

  const onFinish = async (values: LoginForm) => {
    try {
      const result = await dispatch(login(values));
      if (login.fulfilled.match(result)) {
        message.success('登录成功');
        navigate('/dashboard');
      }
    } catch (error: any) {
      // 统一显示"账户或密码错误"提示
      message.error('账户或密码错误');
    }
  };

  const handleSSOLogin = () => {
    // TODO: 实现SSO登录
    window.location.href = '/api/auth/sso/redirect';
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
            BOM管理系统
          </Title>
          <Text type="secondary">请登录您的账户</Text>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
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

          {ssoEnabled && (
            <>
              <Divider>
                <Text type="secondary">或</Text>
              </Divider>
              
              <Form.Item>
                <Button
                  block
                  onClick={handleSSOLogin}
                >
                  SSO单点登录
                </Button>
              </Form.Item>
            </>
          )}
        </Form>

        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Space direction="vertical" size="small">
            <Text type="secondary">
              还没有账户？<a onClick={() => navigate('/register')}>立即注册</a>
            </Text>
            <Text type="secondary">
              测试账号: admin / admin123
            </Text>
            <Text type="secondary">
              普通账号: test / test123
            </Text>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;