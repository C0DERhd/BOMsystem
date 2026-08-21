import React from 'react';
import { Form, Input, Button, Card, Typography, message } from 'antd';
import { UserOutlined, LockOutlined, UserAddOutlined, MailOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';

const { Title, Text } = Typography;

interface RegisterForm {
  name: string;  // 用户名对应name字段
  email: string;
  username: string;  // 账户对应username字段
  password: string;
  confirm_password: string;
}

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();

  const onFinish = async (values: RegisterForm) => {
    try {
      // 使用主系统的注册API
      const response = await api.post('/auth/register', {
        username: values.username,  // 账户作为username
        email: values.email,
        name: values.name,  // 用户名作为name
        password: values.password
      });
      
      if (response.data.success) {
        message.success('注册成功');
        // 注册成功后跳转到主系统登录页面
        navigate('/login');
      } else {
        message.error(response.data.message || '注册失败');
      }
    } catch (error: any) {
      // 显示具体的错误信息
      message.error(error.response?.data?.message || '注册失败，请稍后重试');
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
            BOM管理系统
          </Title>
          <Text type="secondary">用户注册</Text>
        </div>

        <Form
          name="register"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="name"
            rules={[
              { required: true, message: '请输入用户名' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
            />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder="邮箱"
            />
          </Form.Item>

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
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码长度不能少于6位' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="确认密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              icon={<UserAddOutlined />}
            >
              注册
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Text>
            已有账户？<a onClick={() => navigate('/login')}>立即登录</a>
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default RegisterPage;