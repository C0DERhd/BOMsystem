import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, message } from 'antd';
import { SaveOutlined, PhoneOutlined, MailOutlined } from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { getCurrentUser, updateUserInfo } from '@/store/slices/authSlice';

const { Title } = Typography;

const ProfilePage: React.FC = () => {
  const [form] = Form.useForm();
  const dispatch = useAppDispatch();
  const { user, loading } = useAppSelector((state) => state.auth);

  useEffect(() => {
    if (user) {
      form.setFieldsValue({
        name: user.name,
        email: user.email,
        phone: user.phone,
      });
    }
  }, [user, form]);

  const onFinish = async (values: any) => {
    try {
      if (user) {
        // 更新用户信息
        await dispatch(updateUserInfo({ userId: user.id, data: values })).unwrap();
        message.success('个人信息更新成功');
        
        // 重新获取用户信息
        dispatch(getCurrentUser());
      }
    } catch (error) {
      message.error('更新失败: ' + (error as Error).message);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={3} style={{ marginBottom: '24px' }}>个人资料</Title>
        
        <Card title="基本信息" size="small">
          <Form
            form={form}
            layout="vertical"
            onFinish={onFinish}
            disabled={loading}
          >
            <Form.Item
              name="name"
              label="姓名"
              rules={[{ required: true, message: '请输入姓名' }]}
            >
              <Input placeholder="请输入姓名" />
            </Form.Item>
            
            <Form.Item
              name="email"
              label="邮箱"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '请输入有效的邮箱地址' }
              ]}
            >
              <Input placeholder="请输入邮箱" prefix={<MailOutlined />} />
            </Form.Item>
            
            <Form.Item
              name="phone"
              label="电话"
            >
              <Input placeholder="请输入电话" prefix={<PhoneOutlined />} />
            </Form.Item>
            
            <Form.Item>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={loading}
                icon={<SaveOutlined />}
              >
                保存信息
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </Card>
    </div>
  );
};

export default ProfilePage;