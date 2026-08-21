import React, { useEffect, useState } from 'react';
import { AutoComplete, Button, Card, DatePicker, Form, Input, InputNumber, message, Modal, Popconfirm, Select, Space, Table, Typography } from 'antd';
import { ApartmentOutlined, DeleteOutlined, EditOutlined, EyeOutlined, PlusOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import api from '@/services/api';
import dayjs from 'dayjs';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import authService from '@/services/auth';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

const getDisplayPartId = (record: any) => record?.display_goods_id || record?.part_id || record?.goods_id || '-';
const SHOW_RECORD_DELETE_ACTIONS = false;

const formatQuantity = (value: any) => {
  const numberValue = Number(value ?? 0);
  if (!Number.isFinite(numberValue)) {
    return value ?? '-';
  }
  return Number.isInteger(numberValue)
    ? String(numberValue)
    : numberValue.toFixed(4).replace(/\.?0+$/, '');
};

const normalizeOutboundType = (value: any) => {
  const text = String(value || '').trim();
  const legacyTypes: Record<string, string> = {
    '\u9351\u54c4\u7c31': '出库',
    '\u95b8\u621d\u642b\u7ee8?': '出库',
    '\u95b8\u621d\u642b\u7ee8': '出库',
    '\u9347\u54c4\u7c31': '出库',
    '\u93b6\u30e5\u7c3e': '报废',
    '\u95b9\u8eb2\u5131\u7ee8?': '报废',
    '\u95b9\u8eb2\u5131\u7ee8': '报废',
  };
  return legacyTypes[text] || text || '出库';
};

const OutboundRecords: React.FC = () => {
  const [dataSource, setDataSource] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const { user } = useSelector((state: RootState) => state.auth);

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [modalTitle, setModalTitle] = useState('新增出库记录');
  const [editingOutRecordId, setEditingOutRecordId] = useState<number | null>(null);
  const [modalApi, modalContextHolder] = Modal.useModal();
  const [partOptions, setPartOptions] = useState<any[]>([]);
  const [partDropdownOpen, setPartDropdownOpen] = useState(false);
  const [bomModalVisible, setBomModalVisible] = useState(false);
  const [bomForm] = Form.useForm();
  const [bomOptions, setBomOptions] = useState<any[]>([]);
  const [bomInvalidModalVisible, setBomInvalidModalVisible] = useState(false);
  const [bomInvalidMessage, setBomInvalidMessage] = useState('');
  const [bomInvalidItems, setBomInvalidItems] = useState<any[]>([]);

  const getErrorMessage = (error: any, fallback: string) => error?.response?.data?.message || fallback;

  const showBomInvalidItems = (payload: any, fallback: string) => {
    const invalidItems = payload?.data?.invalid_items || [];
    if (!invalidItems.length) {
      return false;
    }
    setBomInvalidMessage(payload?.message || fallback);
    setBomInvalidItems(invalidItems);
    setBomInvalidModalVisible(true);
    return true;
  };

  const searchInventory = async (q = '') => {
    try {
      const keyword = q.trim();
      const [legacyResponse, versionedResponse] = await Promise.all([
        api.get('/visiray/inventory', {
          params: { keyword: keyword || undefined, page: 1, per_page: 20 },
        }),
        api.get('/visiray/versioned-inventory', {
          params: { keyword: keyword || undefined, page: 1, per_page: 20 },
        }),
      ]);
      const legacyItems = legacyResponse.data.success ? (legacyResponse.data.data.items || []) : [];
      const versionedItems = versionedResponse.data.success ? (versionedResponse.data.data.items || []) : [];
      const items = [...legacyItems, ...versionedItems];
      setPartOptions(items.map((item: any) => {
          const partId = getDisplayPartId(item);
          return {
            value: `${partId}@@${item.part_version_id || ''}`,
            label: `${partId}${item.version_no ? ` - 版本 ${item.version_no}` : ''}${item.goods_name ? ' - ' + item.goods_name : ''}`,
            meta: item,
          };
        }));
    } catch (error) {
      setPartOptions([]);
    }
  };

  const onSelectPart = (value: string, option: any) => {
    setPartDropdownOpen(false);
    form.setFieldsValue({
      goods_id: getDisplayPartId(option?.meta),
      part_version_id: option?.meta?.part_version_id,
      goods_name: option?.meta?.goods_name || '',
      shelf_location: option?.meta?.shelf_location || form.getFieldValue('shelf_location'),
    });
  };

  const fetchOutboundData = async (page = 1, keyword = searchKeyword) => {
    setLoading(true);
    try {
      const response = await api.get('/visiray/outbound', {
        params: { page, per_page: pagination.pageSize, keyword: keyword.trim() || undefined },
      });
      if (response.data.success) {
        setDataSource(response.data.data.items);
        setPagination(prev => ({ ...prev, current: page, total: response.data.data.total }));
      } else {
        message.error(response.data.message || '获取出库记录失败');
      }
    } catch (error) {
      message.error(getErrorMessage(error, '获取出库记录失败'));
    } finally {
      setLoading(false);
    }
  };

  const fetchBomOptions = async () => {
    try {
      const response = await api.get('/bom', {
        params: { page: 1, per_page: 500, status: 'active' },
      });
      if (response.data.success) {
        setBomOptions(response.data.data.items || []);
      } else {
        message.error(response.data.message || '获取BOM列表失败');
      }
    } catch (error) {
      message.error(getErrorMessage(error, '获取BOM列表失败'));
    }
  };

  const showModal = () => {
    setModalTitle('新增出库记录');
    setEditingOutRecordId(null);
    setIsModalVisible(true);
    form.resetFields();
    searchInventory();
    form.setFieldsValue({ out_date: dayjs(), outbound_type: '出库' });
  };

  const showBomOutboundModal = () => {
    setBomModalVisible(true);
    bomForm.resetFields();
    bomForm.setFieldsValue({
      quantity: 1,
      out_date: dayjs(),
      outbound_type: '出库',
    });
    fetchBomOptions();
  };

  const showEditModal = (record: any) => {
    setModalTitle('编辑出库记录');
    setEditingOutRecordId(record.out_record_id);
    setIsModalVisible(true);
    form.setFieldsValue({
      ...record,
      goods_id: getDisplayPartId(record),
      part_version_id: record.part_version_id,
      outbound_type: normalizeOutboundType(record.outbound_type),
      out_date: record.out_date ? dayjs(record.out_date, 'YYYY-MM-DD') : null,
    });
    searchInventory(getDisplayPartId(record) === '-' ? '' : getDisplayPartId(record));
  };

  const showDetailModal = (record: any) => {
    modalApi.info({
      title: '出库记录详情',
      width: 600,
      content: (
        <div>
          <p><strong>出库记录:</strong> {record.out_record_id}</p>
          <p><strong>零件号:</strong> {getDisplayPartId(record)}</p>
          <p><strong>版本号:</strong> {record.version_no || '-'}</p>
          <p><strong>零件名称:</strong> {record.goods_name}</p>
          <p><strong>数量:</strong> {record.quantity}</p>
          <p><strong>出库日期:</strong> {record.out_date}</p>
          <p><strong>出库人:</strong> {record.operator}</p>
          <p><strong>货架:</strong> {record.shelf_location}</p>
          <p><strong>出库类型:</strong> {normalizeOutboundType(record.outbound_type)}</p>
        </div>
      ),
    });
  };

  const handleDelete = async (outRecordId: number) => {
    try {
      setLoading(true);
      const response = await api.delete(`/visiray/outbound/${outRecordId}`);
      if (response.data.success) {
        message.success(response.data.message || '出库记录删除成功');
        fetchOutboundData(pagination.current, searchKeyword);
      } else {
        message.error(response.data.message || '删除出库记录失败');
      }
    } catch (error) {
      message.error(getErrorMessage(error, '删除出库记录失败'));
    } finally {
      setLoading(false);
    }
  };

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      if (values.out_date) {
        values.out_date = values.out_date.format('YYYY-MM-DD');
      }
      values.outbound_type = normalizeOutboundType(values.outbound_type);
      if (!editingOutRecordId) {
        values.operator = user?.name || values.operator;
      }

      setLoading(true);
      const response = editingOutRecordId
        ? await api.put(`/visiray/outbound/${editingOutRecordId}`, values)
        : await api.post('/visiray/outbound', values);

      if (response.data.success) {
        message.success(response.data.message || (editingOutRecordId ? '出库记录更新成功' : '出库记录创建成功'));
        setIsModalVisible(false);
        form.resetFields();
        fetchOutboundData(pagination.current, searchKeyword);
      } else {
        message.error(response.data.message || (editingOutRecordId ? '更新出库记录失败' : '创建出库记录失败'));
      }
    } catch (error) {
      message.error(getErrorMessage(error, editingOutRecordId ? '更新出库记录失败' : '创建出库记录失败'));
    } finally {
      setLoading(false);
    }
  };

  const handleBomOutbound = async () => {
    try {
      const values = await bomForm.validateFields();
      if (values.out_date) {
        values.out_date = values.out_date.format('YYYY-MM-DD');
      }
      values.operator = user?.name || values.operator;
      values.outbound_type = normalizeOutboundType(values.outbound_type);

      setLoading(true);
      const response = await api.post('/visiray/outbound/by-bom', values);
      if (response.data.success) {
        message.success(response.data.message || 'BOM出库成功');
        setBomModalVisible(false);
        bomForm.resetFields();
        fetchOutboundData(1, searchKeyword);
      } else if (!showBomInvalidItems(response.data, 'BOM出库失败')) {
        message.error(response.data.message || 'BOM出库失败');
      }
    } catch (error: any) {
      if (!showBomInvalidItems(error?.response?.data, 'BOM出库失败')) {
        message.error(getErrorMessage(error, 'BOM出库失败'));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOutboundData();
  }, []);

  const columns = [
    {
      title: '序号',
      dataIndex: 'index',
      key: 'index',
      render: (_: any, __: any, index: number) => (pagination.current - 1) * pagination.pageSize + index + 1,
      width: 60,
      align: 'center' as const,
    },
    { title: '出库记录', dataIndex: 'out_record_id', key: 'out_record_id' },
    { title: '零件号', dataIndex: 'goods_id', key: 'goods_id', render: (_: any, record: any) => getDisplayPartId(record) },
    { title: '版本号', dataIndex: 'version_no', key: 'version_no', render: (value: any) => value || '-' },
    { title: '零件名称', dataIndex: 'goods_name', key: 'goods_name' },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '出库日期', dataIndex: 'out_date', key: 'out_date' },
    { title: '出库人', dataIndex: 'operator', key: 'operator' },
    { title: '货架', dataIndex: 'shelf_location', key: 'shelf_location' },
    { title: '出库类型', dataIndex: 'outbound_type', key: 'outbound_type', render: (value: any) => normalizeOutboundType(value) },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button type="link" icon={<EyeOutlined />} onClick={() => showDetailModal(record)} style={{ padding: 0 }}>查看详情</Button>
          {authService.isAdmin() && (
            <>
              <Button type="link" icon={<EditOutlined />} onClick={() => showEditModal(record)} style={{ padding: 0 }}>编辑</Button>
              {SHOW_RECORD_DELETE_ACTIONS && (
                <Popconfirm
                title="确认删除"
                description="确定要删除这条出库记录吗？"
                onConfirm={() => handleDelete(record.out_record_id)}
                okText="确认"
                cancelText="取消"
              >
                <Button type="link" icon={<DeleteOutlined />} danger style={{ padding: 0 }}>删除</Button>
                </Popconfirm>
              )}
            </>
          )}
        </Space>
      ),
    },
  ];

  const bomInvalidColumns = [
    {
      title: '序号',
      dataIndex: 'index',
      key: 'index',
      width: 70,
      align: 'center' as const,
      render: (_: any, __: any, index: number) => index + 1,
    },
    { title: '零件号', dataIndex: 'part_id', key: 'part_id' },
    { title: '版本号', dataIndex: 'version_no', key: 'version_no', render: (value: any) => value || '-' },
    { title: '零件名称', dataIndex: 'material_name', key: 'material_name' },
    {
      title: '需要数量',
      dataIndex: 'required_quantity',
      key: 'required_quantity',
      render: (value: any) => formatQuantity(value),
    },
    {
      title: '当前库存',
      dataIndex: 'stock_quantity',
      key: 'stock_quantity',
      render: (value: any) => formatQuantity(value ?? 0),
    },
    {
      title: '缺少数量',
      key: 'shortage_quantity',
      render: (_: any, record: any) => {
        const requiredQuantity = Number(record.required_quantity ?? 0);
        const stockQuantity = Number(record.stock_quantity ?? 0);
        return formatQuantity(Math.max(requiredQuantity - stockQuantity, 0));
      },
    },
    { title: '原因', dataIndex: 'reason', key: 'reason' },
  ];

  return (
    <Card>
      {modalContextHolder}
      <div style={{ marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0, display: 'inline-block' }}>出库记录</Title>
        <div style={{ float: 'right' }}>
          <Space>
            <RangePicker placeholder={['开始日期', '结束日期']} value={dateRange} onChange={(dates) => setDateRange(dates)} />
            <Input
              placeholder="搜索零件号、零件名称、出库人"
              prefix={<SearchOutlined />}
              style={{ width: 250 }}
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onPressEnter={() => fetchOutboundData(1, searchKeyword)}
              allowClear
            />
            <Button icon={<ReloadOutlined />} onClick={() => fetchOutboundData(pagination.current, searchKeyword)}>刷新</Button>
            {authService.isAdmin() && (
              <>
                <Button icon={<ApartmentOutlined />} onClick={showBomOutboundModal}>按BOM出库</Button>
                <Button type="primary" icon={<PlusOutlined />} onClick={showModal}>新增出库</Button>
              </>
            )}
          </Space>
        </div>
      </div>

      <Table
        dataSource={dataSource}
        columns={columns}
        loading={loading}
        rowKey="out_record_id"
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          onChange: (page) => fetchOutboundData(page, searchKeyword),
          showSizeChanger: false,
        }}
        scroll={{ x: 'max-content' }}
      />

      <Modal
        title={modalTitle}
        open={isModalVisible}
        onOk={handleOk}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
        confirmLoading={loading}
        width={600}
      >
        <Form form={form} layout="vertical" initialValues={{ out_date: dayjs(), outbound_type: '出库' }}>
          <Form.Item name="goods_id" label="零件号" rules={[{ required: true, message: '请输入或选择零件号' }]}>
            <AutoComplete
              options={partOptions}
              open={partDropdownOpen && partOptions.length > 0}
              onFocus={() => {
                setPartDropdownOpen(true);
                searchInventory(form.getFieldValue('goods_id') || '');
              }}
              onOpenChange={setPartDropdownOpen}
              onSearch={(value) => {
                setPartDropdownOpen(true);
                searchInventory(value);
              }}
              onSelect={onSelectPart}
              onChange={(value) => form.setFieldsValue({ goods_id: value, goods_name: '' })}
              style={{ width: '100%' }}
              filterOption={(inputValue, option) => String(option?.label ?? '').toLowerCase().includes(inputValue.toLowerCase())}
            >
              <Input placeholder="请输入零件号或名称进行搜索" />
            </AutoComplete>
          </Form.Item>

          <Form.Item name="goods_name" label="零件名称" rules={[{ required: true, message: '请选择零件号带出零件名称' }]}>
            <Input placeholder="选择零件号后自动带出" readOnly />
          </Form.Item>

          <Form.Item name="part_version_id" hidden>
            <Input />
          </Form.Item>

          <Form.Item name="quantity" label="数量" rules={[{ required: true, message: '请输入数量' }]}>
            <InputNumber style={{ width: '100%' }} placeholder="请输入数量" min={1} />
          </Form.Item>

          <Form.Item name="out_date" label="出库日期" rules={[{ required: true, message: '请选择出库日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          {editingOutRecordId && (
            <Form.Item name="operator" label="出库人" rules={[{ required: true, message: '请输入出库人' }]}>
              <Input placeholder="请输入出库人" />
            </Form.Item>
          )}

          <Form.Item name="shelf_location" label="货架" rules={[{ required: true, message: '请输入货架位置' }]}>
            <Input placeholder="请输入货架位置" />
          </Form.Item>

          <Form.Item name="outbound_type" label="出库类型" rules={[{ required: true, message: '请选择出库类型' }]}>
            <Select placeholder="请选择出库类型">
              <Option value="出库">出库</Option>
              <Option value="报废">报废</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="按BOM出库"
        open={bomModalVisible}
        onOk={handleBomOutbound}
        onCancel={() => {
          setBomModalVisible(false);
          bomForm.resetFields();
        }}
        confirmLoading={loading}
        width={640}
      >
        <Form form={bomForm} layout="vertical" initialValues={{ quantity: 1, out_date: dayjs(), outbound_type: '出库' }}>
          <Form.Item name="bom_id" label="BOM" rules={[{ required: true, message: '请选择BOM' }]}>
            <Select
              showSearch
              placeholder="请选择生效BOM"
              optionFilterProp="label"
              options={bomOptions.map((item) => ({
                value: item.id,
                label: `${item.bom_code} - ${item.product_name}${item.product_model ? ` - ${item.product_model}` : ''}`,
              }))}
            />
          </Form.Item>

          <Form.Item name="quantity" label="生产数量" rules={[{ required: true, message: '请输入生产数量' }]}>
            <InputNumber min={0.0001} precision={4} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="out_date" label="出库日期" rules={[{ required: true, message: '请选择出库日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="outbound_type" label="出库类型" rules={[{ required: true, message: '请选择出库类型' }]}>
            <Select placeholder="请选择出库类型">
              <Option value="出库">出库</Option>
              <Option value="报废">报废</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="BOM出库缺料明细"
        open={bomInvalidModalVisible}
        onCancel={() => setBomInvalidModalVisible(false)}
        footer={[
          <Button key="ok" type="primary" onClick={() => setBomInvalidModalVisible(false)}>
            知道了
          </Button>,
        ]}
        width={900}
      >
        <div style={{ marginBottom: 12 }}>{bomInvalidMessage || 'BOM出库校验失败'}</div>
        <Table
          dataSource={bomInvalidItems}
          columns={bomInvalidColumns}
          rowKey={(record, index) => `${record.part_id || 'part'}-${index}`}
          pagination={false}
          size="small"
          scroll={{ x: 'max-content' }}
        />
      </Modal>
    </Card>
  );
};

export default OutboundRecords;
