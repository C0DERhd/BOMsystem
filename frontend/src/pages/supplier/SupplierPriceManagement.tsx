import React, { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { EditOutlined, PlusOutlined, ReloadOutlined, SearchOutlined, StopOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

import authService from '@/services/auth';
import api from '@/services/api';

const { Title, Text } = Typography;
const dateFormat = 'YYYY-MM-DD';

interface PartOption {
  part_id: string;
  part_name?: string;
  main_type?: string;
  sub_type?: string;
  versions?: {
    id: number;
    version_no: string;
    status: 'active' | 'obsolete';
    is_current: boolean;
  }[];
}

interface SupplierOption {
  supplier_code: string;
  supplier_name?: string;
}

interface SupplierPrice {
  id: number;
  part_id?: string;
  material_code?: string;
  material_name?: string;
  part_version_id?: number;
  version_no?: string;
  version_status?: string;
  supplier_code?: string;
  supplier_name?: string;
  supplier_part_no?: string;
  price: number;
  currency: string;
  price_date?: string;
  valid_from?: string;
  valid_to?: string;
  is_primary: boolean;
  lead_time?: number;
  min_order_qty?: number;
  status: 'active' | 'inactive';
  remark?: string;
}

const formatDate = (value?: string) => {
  if (!value) return '-';
  const parsed = dayjs(value);
  return parsed.isValid() ? parsed.format(dateFormat) : value;
};

const SupplierPriceManagement: React.FC = () => {
  const [form] = Form.useForm();
  const [items, setItems] = useState<SupplierPrice[]>([]);
  const [parts, setParts] = useState<PartOption[]>([]);
  const [suppliers, setSuppliers] = useState<SupplierOption[]>([]);
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [optionsLoading, setOptionsLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<SupplierPrice | null>(null);
  const [selectedPartOption, setSelectedPartOption] = useState<PartOption | undefined>();
  const optionsRequestRef = React.useRef(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const isAdmin = authService.isAdmin();
  const selectedPartId = Form.useWatch('part_id', form) as string | undefined;
  const selectedPart = useMemo(
    () => parts.find((item) => item.part_id === selectedPartId) ||
      (selectedPartOption?.part_id === selectedPartId ? selectedPartOption : undefined),
    [parts, selectedPartId, selectedPartOption]
  );

  const partOptions = useMemo(
    () => parts.map((item) => ({
      value: item.part_id,
      label: `${item.part_id} - ${item.part_name || item.sub_type || item.main_type || ''}`,
    })),
    [parts]
  );

  const versionOptions = useMemo(
    () => [
      { value: '', label: '通用报价' },
      ...((selectedPart?.versions || []).map((version) => ({
        value: String(version.id),
        label: `${version.version_no}${version.is_current ? ' 当前' : ''}${version.status === 'obsolete' ? ' 已废弃' : ''}`,
      }))),
    ],
    [selectedPart]
  );

  const supplierOptions = useMemo(
    () => suppliers.map((item) => ({
      value: item.supplier_code,
      label: `${item.supplier_code} - ${item.supplier_name || ''}`,
    })),
    [suppliers]
  );

  const fetchOptions = async (params: { part_keyword?: string; supplier_keyword?: string } = {}) => {
    const requestId = ++optionsRequestRef.current;
    try {
      setOptionsLoading(true);
      const response = await api.get('/visiray/supplier-price-options', { params });
      // Search requests can finish out of order. Only the newest response may
      // replace the option lists, otherwise a stale result can hide a pasted
      // exact part number and make its version selector appear disabled.
      if (requestId === optionsRequestRef.current && response.data.success) {
        const nextParts = response.data.data.parts || [];
        const currentPartId = form.getFieldValue('part_id') as string | undefined;
        const preservedPart = currentPartId
          ? selectedPartOption?.part_id === currentPartId
            ? selectedPartOption
            : parts.find((item) => item.part_id === currentPartId)
          : undefined;
        if (preservedPart && !nextParts.some((item: PartOption) => item.part_id === preservedPart.part_id)) {
          nextParts.unshift(preservedPart);
        }
        setParts(nextParts);
        setSuppliers(response.data.data.suppliers || []);
      }
    } finally {
      if (requestId === optionsRequestRef.current) {
        setOptionsLoading(false);
      }
    }
  };

  const fetchPrices = async (page = pagination.current, searchValue = keyword) => {
    try {
      setLoading(true);
      const response = await api.get('/visiray/supplier-prices', {
        params: {
          page,
          per_page: pagination.pageSize,
          keyword: searchValue || undefined,
        },
      });
      if (response.data.success) {
        const data = response.data.data;
        setItems(data.items || []);
        setPagination((prev) => ({
          ...prev,
          current: data.current_page || page,
          total: data.total || 0,
        }));
      }
    } catch (error: any) {
      message.error(error?.response?.data?.message || error?.message || '获取供应商报价失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOptions().catch((error) => {
      message.error(error?.response?.data?.message || error?.message || '获取选项失败');
    });
    fetchPrices(1, '');
  }, []);

  const openCreate = () => {
    setEditingItem(null);
    setSelectedPartOption(undefined);
    fetchOptions().catch((error) => {
      message.error(error?.response?.data?.message || error?.message || '获取选项失败');
    });
    form.resetFields();
    form.setFieldsValue({
      currency: 'CNY',
      status: 'active',
      price_date: dayjs(),
      is_primary: false,
      part_version_id: '',
    });
    setModalOpen(true);
  };

  const openEdit = (record: SupplierPrice) => {
    setEditingItem(record);
    fetchOptions({ part_keyword: record.part_id || undefined }).catch((error) => {
      message.error(error?.response?.data?.message || error?.message || '获取选项失败');
    });
    form.resetFields();
    const recordPart = parts.find((item) => item.part_id === record.part_id);
    setSelectedPartOption(recordPart);
    form.setFieldsValue({
      part_id: record.part_id,
      part_version_id: record.part_version_id ? String(record.part_version_id) : '',
      supplier_code: record.supplier_code,
      supplier_part_no: record.supplier_part_no,
      price: record.price,
      currency: record.currency || 'CNY',
      price_date: record.price_date ? dayjs(record.price_date) : undefined,
      valid_from: record.valid_from ? dayjs(record.valid_from) : undefined,
      valid_to: record.valid_to ? dayjs(record.valid_to) : undefined,
      is_primary: record.is_primary,
      lead_time: record.lead_time,
      min_order_qty: record.min_order_qty,
      status: record.status || 'active',
      remark: record.remark,
    });
    setModalOpen(true);
  };

  const buildPayload = (values: any) => ({
    ...values,
    part_version_id: values.part_version_id || undefined,
    price_date: values.price_date ? values.price_date.format(dateFormat) : undefined,
    valid_from: values.valid_from ? values.valid_from.format(dateFormat) : undefined,
    valid_to: values.valid_to ? values.valid_to.format(dateFormat) : undefined,
  });

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const payload = buildPayload(values);
      if (editingItem) {
        await api.put(`/visiray/supplier-prices/${editingItem.id}`, payload);
        message.success('供应商报价已更新');
      } else {
        await api.post('/visiray/supplier-prices', payload);
        message.success('供应商报价已创建');
      }
      setModalOpen(false);
      form.resetFields();
      fetchOptions().catch(() => undefined);
      fetchPrices(editingItem ? pagination.current : 1, keyword);
    } catch (error: any) {
      if (!error?.errorFields) {
        message.error(error?.response?.data?.message || error?.message || '保存供应商报价失败');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDisable = async (record: SupplierPrice) => {
    try {
      await api.delete(`/visiray/supplier-prices/${record.id}`);
      message.success('供应商报价已停用');
      fetchPrices(pagination.current, keyword);
    } catch (error: any) {
      message.error(error?.response?.data?.message || error?.message || '停用供应商报价失败');
    }
  };

  const columns = [
    {
      title: '零件号',
      dataIndex: 'part_id',
      key: 'part_id',
      width: 170,
      render: (value: string, record: SupplierPrice) => (
        <Space direction="vertical" size={0}>
          <Text>{value || '-'}</Text>
          <Text type="secondary">{record.material_name || record.material_code || '-'}</Text>
          <Text type="secondary">{record.version_no ? `版本 ${record.version_no}` : '通用报价'}</Text>
        </Space>
      ),
    },
    {
      title: '供应商',
      dataIndex: 'supplier_name',
      key: 'supplier_name',
      width: 180,
      render: (value: string, record: SupplierPrice) => (
        <Space direction="vertical" size={0}>
          <Text>{value || '-'}</Text>
          <Text type="secondary">{record.supplier_code || '-'}</Text>
        </Space>
      ),
    },
    { title: '供应商料号', dataIndex: 'supplier_part_no', key: 'supplier_part_no', width: 140, render: (value: string) => value || '-' },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 120,
      render: (value: number, record: SupplierPrice) => `${record.currency || 'CNY'} ${Number(value || 0).toFixed(4)}`,
    },
    {
      title: '主供应商',
      dataIndex: 'is_primary',
      key: 'is_primary',
      width: 100,
      render: (value: boolean) => value ? <Tag color="blue">主供应商</Tag> : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (value: string) => value === 'active' ? <Tag color="green">启用</Tag> : <Tag>停用</Tag>,
    },
    { title: '报价日期', dataIndex: 'price_date', key: 'price_date', width: 120, render: formatDate },
    {
      title: '有效期',
      key: 'valid_range',
      width: 210,
      render: (_: unknown, record: SupplierPrice) => `${formatDate(record.valid_from)} 至 ${formatDate(record.valid_to)}`,
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right' as const,
      width: 150,
      render: (_: unknown, record: SupplierPrice) => isAdmin ? (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(record)}>编辑</Button>
          {record.status === 'active' && (
            <Popconfirm title="确认停用该报价？" onConfirm={() => handleDisable(record)} okText="确认" cancelText="取消">
              <Button type="link" danger icon={<StopOutlined />}>停用</Button>
            </Popconfirm>
          )}
        </Space>
      ) : null,
    },
  ];

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 16 }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>供应商报价管理</Title>
          <Text type="secondary">维护同一零件号在不同供应商下的采购价格，BOM 成本按选中的报价计算。</Text>
        </div>
        <Space>
          <Input
            allowClear
            placeholder="搜索零件号、名称、供应商"
            prefix={<SearchOutlined />}
            style={{ width: 280 }}
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            onPressEnter={() => fetchPrices(1, keyword)}
          />
          <Button icon={<ReloadOutlined />} onClick={() => fetchPrices(pagination.current, keyword)}>刷新</Button>
          {isAdmin && <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新增报价</Button>}
        </Space>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={items}
        loading={loading}
        scroll={{ x: 1350 }}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: false,
          onChange: (page) => fetchPrices(page, keyword),
        }}
      />

      <Modal
        title={editingItem ? '编辑供应商报价' : '新增供应商报价'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
        width={760}
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="part_id" label="零件号" rules={[{ required: true, message: '请选择零件号' }]}>
              <Select
                showSearch
                placeholder="选择零件号"
                optionFilterProp="label"
                filterOption
                loading={optionsLoading}
                notFoundContent={optionsLoading ? '加载中...' : '暂无零件号，请先在零件号申请/管理中创建'}
                onDropdownVisibleChange={(open) => {
                  if (open && parts.length === 0) fetchOptions().catch(() => undefined);
                }}
                onSearch={(value) => {
                  fetchOptions({ part_keyword: value.trim() }).catch(() => undefined);
                }}
                onChange={(value) => {
                  const part = parts.find((item) => item.part_id === value);
                  setSelectedPartOption(part);
                  form.setFieldsValue({ part_version_id: '' });
                }}
                options={partOptions}
              />
            </Form.Item>
            <Form.Item name="part_version_id" label="版本号">
              <Select
                placeholder={selectedPart ? '选择版本或通用报价' : '请先选择零件号'}
                options={versionOptions}
                disabled={!selectedPart}
              />
            </Form.Item>
            <Form.Item name="supplier_code" label="供应商" rules={[{ required: true, message: '请选择供应商' }]}>
              <Select
                showSearch
                placeholder="选择供应商"
                optionFilterProp="label"
                filterOption
                loading={optionsLoading}
                notFoundContent={optionsLoading ? '加载中...' : '暂无供应商，请先在供应商信息中创建'}
                onDropdownVisibleChange={(open) => {
                  if (open && suppliers.length === 0) fetchOptions().catch(() => undefined);
                }}
                onSearch={(value) => {
                  fetchOptions({ supplier_keyword: value }).catch(() => undefined);
                }}
                options={supplierOptions}
              />
            </Form.Item>
            <Form.Item name="price" label="价格" rules={[{ required: true, message: '请输入价格' }]}>
              <InputNumber min={0} precision={4} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="currency" label="币种">
              <Select
                options={[
                  { value: 'CNY', label: 'CNY 人民币' },
                  { value: 'USD', label: 'USD 美元' },
                  { value: 'EUR', label: 'EUR 欧元' },
                ]}
              />
            </Form.Item>
            <Form.Item name="supplier_part_no" label="供应商料号">
              <Input placeholder="供应商自己的物料编号" />
            </Form.Item>
            <Form.Item name="price_date" label="报价日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="valid_from" label="生效日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="valid_to" label="失效日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="lead_time" label="交期（天）">
              <InputNumber min={0} precision={0} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="min_order_qty" label="最小订购量">
              <InputNumber min={0} precision={4} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="status" label="状态">
              <Select options={[{ value: 'active', label: '启用' }, { value: 'inactive', label: '停用' }]} />
            </Form.Item>
            <Form.Item name="is_primary" label="主供应商" valuePropName="checked">
              <Switch checkedChildren="是" unCheckedChildren="否" />
            </Form.Item>
          </div>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={3} placeholder="报价说明、付款条件或其他备注" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default SupplierPriceManagement;
