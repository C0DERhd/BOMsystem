import React, { useEffect, useState } from 'react';
import { Button, Card, Empty, Form, Input, Modal, Space, Table, Tag, Typography, message } from 'antd';
import { EyeOutlined, PlusOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons';

import authService from '@/services/auth';
import api from '@/services/api';

const { Title } = Typography;

interface SupplierInfo {
  id?: number;
  supplier_code: string;
  supplier_name?: string;
  phone?: string;
  email?: string;
  address?: string;
  contact_person?: string;
  position?: string;
  liaison?: string;
  purchase_orders?: string;
  inbound_records?: string;
  remark?: string;
  source?: 'suppliers' | 'supplier_information';
}

const SupplierManagement: React.FC = () => {
  const [dataSource, setDataSource] = useState<SupplierInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [modalApi, modalContextHolder] = Modal.useModal();
  const isAdmin = authService.isAdmin();

  const getErrorMessage = (error: any, fallback: string) => (
    error?.response?.data?.message || error?.message || fallback
  );

  const fetchSupplierData = async (page = 1, keyword = searchKeyword) => {
    setLoading(true);
    try {
      const response = await api.get('/visiray/suppliers', {
        params: {
          page,
          per_page: pagination.pageSize,
          keyword: keyword || undefined,
        },
      });

      if (response.data.success) {
        const data = response.data.data;
        setDataSource(data.items || []);
        setPagination((prev) => ({
          ...prev,
          current: data.current_page || page,
          total: data.total || 0,
        }));
      } else {
        message.error(response.data.message || '获取供应商信息失败');
      }
    } catch (error) {
      message.error(getErrorMessage(error, '获取供应商信息失败'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSupplierData(1, '');
  }, []);

  const showCreateModal = () => {
    form.resetFields();
    setIsModalVisible(true);
  };

  const showDetailModal = (record: SupplierInfo) => {
    modalApi.info({
      title: '供应商详情',
      width: 640,
      content: (
        <div>
          <p><strong>供应商编号：</strong>{record.supplier_code || '-'}</p>
          <p><strong>供应商名称：</strong>{record.supplier_name || '-'}</p>
          <p><strong>联系电话：</strong>{record.phone || '-'}</p>
          <p><strong>邮箱：</strong>{record.email || '-'}</p>
          <p><strong>联系地址：</strong>{record.address || '-'}</p>
          <p><strong>联系人：</strong>{record.contact_person || '-'}</p>
          <p><strong>职务：</strong>{record.position || '-'}</p>
          <p><strong>对接人：</strong>{record.liaison || '-'}</p>
          <p><strong>采购入库单：</strong>{record.purchase_orders || '-'}</p>
          <p><strong>入库记录：</strong>{record.inbound_records || '-'}</p>
          <p><strong>备注：</strong>{record.remark || '-'}</p>
        </div>
      ),
    });
  };

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      const response = await api.post('/visiray/suppliers', values);

      if (response.data.success) {
        message.success(response.data.message || '供应商信息创建成功');
        setIsModalVisible(false);
        form.resetFields();
        fetchSupplierData(1, searchKeyword);
      } else {
        message.error(response.data.message || '创建供应商信息失败');
      }
    } catch (error: any) {
      if (!error?.errorFields) {
        message.error(getErrorMessage(error, '创建供应商信息失败'));
      }
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '供应商编号', dataIndex: 'supplier_code', key: 'supplier_code', width: 150 },
    { title: '供应商名称', dataIndex: 'supplier_name', key: 'supplier_name', width: 220 },
    { title: '联系电话', dataIndex: 'phone', key: 'phone', width: 140, render: (text: string) => text || '-' },
    { title: '邮箱', dataIndex: 'email', key: 'email', width: 180, render: (text: string) => text || '-' },
    { title: '联系人', dataIndex: 'contact_person', key: 'contact_person', width: 120, render: (text: string) => text || '-' },
    { title: '对接人', dataIndex: 'liaison', key: 'liaison', width: 120, render: (text: string) => text || '-' },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 120,
      render: (value: SupplierInfo['source']) => (
        value === 'suppliers' ? <Tag color="blue">供应商主表</Tag> : <Tag>旧供应商信息</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right' as const,
      width: 120,
      render: (_: unknown, record: SupplierInfo) => (
        <Button type="link" icon={<EyeOutlined />} onClick={() => showDetailModal(record)} style={{ padding: 0 }}>
          查看详情
        </Button>
      ),
    },
  ];

  return (
    <Card>
      {modalContextHolder}
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>供应商信息</Title>
        <Space>
          <Input
            allowClear
            placeholder="搜索供应商编号、名称、联系人"
            prefix={<SearchOutlined />}
            style={{ width: 280 }}
            value={searchKeyword}
            onChange={(event) => setSearchKeyword(event.target.value)}
            onPressEnter={() => fetchSupplierData(1, searchKeyword)}
          />
          <Button icon={<ReloadOutlined />} onClick={() => fetchSupplierData(pagination.current, searchKeyword)}>
            刷新
          </Button>
          {isAdmin && (
            <Button type="primary" icon={<PlusOutlined />} onClick={showCreateModal}>
              新增供应商
            </Button>
          )}
        </Space>
      </div>

      <Table
        dataSource={dataSource}
        columns={columns}
        loading={loading}
        rowKey="supplier_code"
        scroll={{ x: 1170 }}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          onChange: (page) => fetchSupplierData(page, searchKeyword),
          showSizeChanger: false,
        }}
        locale={{ emptyText: <Empty description="暂无供应商数据" /> }}
      />

      <Modal
        title="新增供应商"
        open={isModalVisible}
        onOk={handleCreate}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
        confirmLoading={loading}
        width={640}
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          <Form.Item name="supplier_code" label="供应商编号" rules={[{ required: true, message: '请输入供应商编号' }]}>
            <Input placeholder="请输入供应商编号" />
          </Form.Item>
          <Form.Item name="supplier_name" label="供应商名称" rules={[{ required: true, message: '请输入供应商名称' }]}>
            <Input placeholder="请输入供应商名称" />
          </Form.Item>
          <Form.Item name="phone" label="联系电话">
            <Input placeholder="请输入联系电话" />
          </Form.Item>
          <Form.Item name="email" label="邮箱">
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item name="address" label="联系地址">
            <Input.TextArea rows={2} placeholder="请输入联系地址" />
          </Form.Item>
          <Form.Item name="contact_person" label="联系人">
            <Input placeholder="请输入联系人" />
          </Form.Item>
          <Form.Item name="position" label="职务">
            <Input placeholder="请输入职务" />
          </Form.Item>
          <Form.Item name="coordinator" label="对接人">
            <Input placeholder="请输入对接人" />
          </Form.Item>
          <Form.Item name="remarks" label="备注">
            <Input.TextArea rows={3} placeholder="请输入备注" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default SupplierManagement;
