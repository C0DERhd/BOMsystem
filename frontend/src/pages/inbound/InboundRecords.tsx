import React, { useEffect, useState } from 'react';
import {
  AutoComplete,
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Typography,
} from 'antd';
import {
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons';
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

const InboundRecords: React.FC = () => {
  const [dataSource, setDataSource] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const { user } = useSelector((state: RootState) => state.auth);

  const [purchaseOrderOptions, setPurchaseOrderOptions] = useState<any[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [modalTitle, setModalTitle] = useState('新增入库');
  const [editingInRecord, setEditingInRecord] = useState<string | null>(null);
  const [modalApi, modalContextHolder] = Modal.useModal();
  const [partOptions, setPartOptions] = useState<any[]>([]);
  const [supplierOptions, setSupplierOptions] = useState<any[]>([]);
  const [partDropdownOpen, setPartDropdownOpen] = useState(false);
  const [supplierDropdownOpen, setSupplierDropdownOpen] = useState(false);
  const selectedPartId = Form.useWatch('goods_id', form) as string | undefined;
  const selectedPart = partOptions.find((item) => item.value === selectedPartId)?.meta;
  const versionOptions = (selectedPart?.versions || [])
    .filter((item: any) => item.status === 'active')
    .map((item: any) => ({
      value: item.id,
      label: `${item.version_no}${item.is_current ? ' 当前' : ''}`,
    }));

  const getErrorMessage = (error: any, fallback: string) => error?.response?.data?.message || fallback;

  const searchPartNumbers = async (q = '') => {
    try {
      const keyword = q.trim();
      const response = await api.get('/visiray/part-numbers', {
        params: { keyword: keyword || undefined, page: 1, per_page: 20 },
      });
      if (response.data.success) {
        const items = response.data.data.items || [];
        setPartOptions(items.map((item: any) => ({
          value: String(item.part_id),
          label: `${item.part_id}${item.part_name ? ' - ' + item.part_name : ''}`,
          meta: item,
        })));
      }
    } catch (error) {
      setPartOptions([]);
    }
  };

  const onSelectPart = (value: string, option: any) => {
    setPartDropdownOpen(false);
    const currentVersion = (option?.meta?.versions || []).find((item: any) => item.is_current && item.status === 'active')
      || (option?.meta?.versions || []).find((item: any) => item.status === 'active');
    form.setFieldsValue({
      goods_id: value,
      goods_name: option?.meta?.part_name || option?.meta?.sub_type || '',
      unit: option?.meta?.unit || form.getFieldValue('unit'),
      goods_type: option?.meta?.main_type || form.getFieldValue('goods_type'),
      part_version_id: currentVersion?.id,
    });
  };

  const searchSuppliers = async (q = '') => {
    try {
      const keyword = q.trim();
      const response = await api.get('/visiray/suppliers', {
        params: { keyword: keyword || undefined, page: 1, per_page: 20 },
      });
      if (response.data.success) {
        const items = response.data.data.items || [];
        setSupplierOptions(items.map((item: any) => ({
          value: item.supplier_name || item.supplier_code,
          label: `${item.supplier_name || item.supplier_code}${item.supplier_code ? ' - ' + item.supplier_code : ''}`,
          meta: item,
        })));
      }
    } catch (error) {
      setSupplierOptions([]);
    }
  };

  const onSelectSupplier = (value: string) => {
    setSupplierDropdownOpen(false);
    form.setFieldsValue({ supplier_name: value });
  };

  const fetchInboundData = async (page = 1, keyword = searchKeyword) => {
    setLoading(true);
    try {
      const response = await api.get('/visiray/inbound', {
        params: { page, per_page: pagination.pageSize, keyword: keyword.trim() || undefined },
      });
      if (response.data.success) {
        setDataSource(response.data.data.items);
        setPagination(prev => ({ ...prev, current: page, total: response.data.data.total }));
      } else {
        message.error(response.data.message || '获取入库记录失败');
      }
    } catch (error) {
      message.error(getErrorMessage(error, '获取入库记录失败'));
    } finally {
      setLoading(false);
    }
  };

  const fetchPurchaseOrderOptions = async () => {
    try {
      const response = await api.get('/visiray/purchase-orders', {
        params: { page: 1, per_page: 1000 },
      });
      if (response.data.success) {
        setPurchaseOrderOptions((response.data.data.items || []).map((item: any) => ({
          value: item.purchase_order_no,
          label: item.purchase_order_no,
        })));
      }
    } catch (error) {
      message.error(getErrorMessage(error, '获取采购单号失败'));
    }
  };

  const showModal = () => {
    setModalTitle('新增入库');
    setEditingInRecord(null);
    setIsModalVisible(true);
    form.resetFields();
    form.setFieldsValue({
      in_date: dayjs(),
      inbound_type: '入库',
    });
    fetchPurchaseOrderOptions();
    searchPartNumbers();
    searchSuppliers();
  };

  const showEditModal = (record: any) => {
    setModalTitle('编辑入库');
    setEditingInRecord(record.in_record);
    setIsModalVisible(true);
    form.setFieldsValue({
      ...record,
      goods_id: getDisplayPartId(record),
      part_version_id: record.part_version_id,
      supplier_name: record.supplier_name || record.supplier,
      in_date: record.in_date ? dayjs(record.in_date, 'YYYY-MM-DD') : null,
      inbound_type: '入库',
    });
    fetchPurchaseOrderOptions();
    searchPartNumbers(getDisplayPartId(record) === '-' ? '' : getDisplayPartId(record));
    searchSuppliers(record.supplier_name || record.supplier || '');
  };

  const showDetailModal = (record: any) => {
    modalApi.info({
      title: '入库记录详情',
      width: 600,
      content: (
        <div>
          <p><strong>入库记录:</strong> {record.in_record}</p>
          <p><strong>零件号:</strong> {getDisplayPartId(record)}</p>
          <p><strong>版本号:</strong> {record.version_no || '-'}</p>
          <p><strong>供应商:</strong> {record.supplier_name || record.supplier || '-'}</p>
          <p><strong>数量:</strong> {record.quantity}</p>
          <p><strong>单位:</strong> {record.unit}</p>
          <p><strong>入库日期:</strong> {record.in_date}</p>
          <p><strong>入库人:</strong> {record.operator}</p>
          <p><strong>货架:</strong> {record.shelf_location}</p>
          <p><strong>关联采购单:</strong> {record.related_voucher || '-'}</p>
        </div>
      ),
    });
  };

  const handleDelete = async (inRecord: string) => {
    try {
      setLoading(true);
      const response = await api.delete(`/visiray/inbound/${inRecord}`);
      if (response.data.success) {
        message.success(response.data.message || '入库记录删除成功');
        fetchInboundData(pagination.current, searchKeyword);
      } else {
        message.error(response.data.message || '删除入库记录失败');
      }
    } catch (error) {
      message.error(getErrorMessage(error, '删除入库记录失败'));
    } finally {
      setLoading(false);
    }
  };

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      if (values.in_date) {
        values.in_date = values.in_date.format('YYYY-MM-DD');
      }
      values.inbound_type = '入库';
      values.supplier = values.supplier_name;
      values.goods_name = form.getFieldValue('goods_name') || values.goods_name;
      if (!editingInRecord) {
        values.operator = user?.name || values.operator;
        delete values.in_record;
      }

      setLoading(true);
      const response = editingInRecord
        ? await api.put(`/visiray/inbound/${editingInRecord}`, values)
        : await api.post('/visiray/inbound', values);

      if (response.data.success) {
        message.success(response.data.message || (editingInRecord ? '入库记录更新成功' : '入库记录创建成功'));
        setIsModalVisible(false);
        form.resetFields();
        fetchInboundData(pagination.current, searchKeyword);
      } else {
        message.error(response.data.message || (editingInRecord ? '更新入库记录失败' : '创建入库记录失败'));
      }
    } catch (error) {
      message.error(getErrorMessage(error, editingInRecord ? '更新入库记录失败' : '创建入库记录失败'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInboundData();
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
    { title: '入库记录', dataIndex: 'in_record', key: 'in_record' },
    { title: '零件号', dataIndex: 'goods_id', key: 'goods_id', render: (_: any, record: any) => getDisplayPartId(record) },
    { title: '版本号', dataIndex: 'version_no', key: 'version_no', render: (value: any) => value || '-' },
    { title: '供应商', dataIndex: 'supplier_name', key: 'supplier_name', render: (_: any, record: any) => record.supplier_name || record.supplier || '-' },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '单位', dataIndex: 'unit', key: 'unit' },
    { title: '入库日期', dataIndex: 'in_date', key: 'in_date' },
    { title: '入库人', dataIndex: 'operator', key: 'operator' },
    { title: '货架', dataIndex: 'shelf_location', key: 'shelf_location' },
    { title: '关联采购单', dataIndex: 'related_voucher', key: 'related_voucher', render: (text: any) => text || '-' },
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
                description="确定要删除这条入库记录吗？"
                onConfirm={() => handleDelete(record.in_record)}
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

  return (
    <Card>
      {modalContextHolder}
      <div style={{ marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0, display: 'inline-block' }}>入库记录</Title>
        <div style={{ float: 'right' }}>
          <Space>
            <RangePicker placeholder={['开始日期', '结束日期']} value={dateRange} onChange={(dates) => setDateRange(dates)} />
            <Input
              placeholder="搜索入库记录、零件号、供应商"
              prefix={<SearchOutlined />}
              style={{ width: 280 }}
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onPressEnter={() => fetchInboundData(1, searchKeyword)}
              allowClear
            />
            <Button icon={<ReloadOutlined />} onClick={() => fetchInboundData(pagination.current, searchKeyword)}>刷新</Button>
            {authService.isAdmin() && <Button type="primary" icon={<PlusOutlined />} onClick={showModal}>新增入库</Button>}
          </Space>
        </div>
      </div>

      <Table
        dataSource={dataSource}
        columns={columns}
        loading={loading}
        rowKey="in_record"
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          onChange: (page) => fetchInboundData(page, searchKeyword),
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
        <Form form={form} layout="vertical" initialValues={{ in_date: dayjs(), inbound_type: '入库' }}>
          <Form.Item name="goods_id" label="零件号" rules={[{ required: true, message: '请输入或选择零件号' }]}>
            <AutoComplete
              options={partOptions}
              open={partDropdownOpen && partOptions.length > 0}
              onFocus={() => {
                setPartDropdownOpen(true);
                searchPartNumbers(form.getFieldValue('goods_id') || '');
              }}
              onOpenChange={setPartDropdownOpen}
              onSearch={(value) => {
                setPartDropdownOpen(true);
                searchPartNumbers(value);
              }}
              onSelect={onSelectPart}
              onChange={(value) => form.setFieldsValue({ goods_id: value })}
              style={{ width: '100%' }}
              filterOption={(inputValue, option) => String(option?.label ?? '').toLowerCase().includes(inputValue.toLowerCase())}
            >
              <Input placeholder="请输入零件号或名称进行搜索" />
            </AutoComplete>
          </Form.Item>

          <Form.Item name="goods_name" hidden>
            <Input />
          </Form.Item>

          <Form.Item name="part_version_id" label="版本号">
            <Select
              placeholder={selectedPart ? (versionOptions.length ? '请选择版本号' : '该零件暂无版本') : '请先选择零件号'}
              allowClear
              disabled={!selectedPart || !versionOptions.length}
              options={versionOptions}
            />
          </Form.Item>

          <Form.Item name="product_model" label="商品型号">
            <Input placeholder="请输入商品型号" />
          </Form.Item>

          <Form.Item name="goods_type" label="货品类型">
            <Input placeholder="请输入货品类型" />
          </Form.Item>

          <Form.Item name="inbound_type" hidden initialValue="入库">
            <Input />
          </Form.Item>

          <Form.Item name="supplier_name" label="供应商" rules={[{ required: true, message: '请输入供应商' }]}>
            <AutoComplete
              options={supplierOptions}
              open={supplierDropdownOpen && supplierOptions.length > 0}
              onFocus={() => {
                setSupplierDropdownOpen(true);
                searchSuppliers(form.getFieldValue('supplier_name') || '');
              }}
              onOpenChange={setSupplierDropdownOpen}
              onSearch={(value) => {
                setSupplierDropdownOpen(true);
                searchSuppliers(value);
              }}
              onSelect={onSelectSupplier}
              onChange={(value) => form.setFieldsValue({ supplier_name: value })}
              style={{ width: '100%' }}
              filterOption={(inputValue, option) => String(option?.label ?? '').toLowerCase().includes(inputValue.toLowerCase())}
            >
              <Input placeholder="请输入供应商名称或编号搜索" />
            </AutoComplete>
          </Form.Item>

          <Form.Item name="quantity" label="数量" rules={[{ required: true, message: '请输入数量' }]}>
            <InputNumber style={{ width: '100%' }} placeholder="请输入数量" min={1} />
          </Form.Item>

          <Form.Item name="unit" label="单位" rules={[{ required: true, message: '请选择单位' }]}>
            <Select placeholder="请选择单位">
              <Option value="个">个</Option>
              <Option value="件">件</Option>
              <Option value="套">套</Option>
              <Option value="台">台</Option>
              <Option value="米">米</Option>
              <Option value="千克">千克</Option>
              <Option value="pcs">pcs</Option>
            </Select>
          </Form.Item>

          <Form.Item name="in_date" label="入库日期" rules={[{ required: true, message: '请选择入库日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          {editingInRecord && (
            <Form.Item name="operator" label="入库人" rules={[{ required: true, message: '请输入入库人' }]}>
              <Input placeholder="请输入入库人" />
            </Form.Item>
          )}

          <Form.Item name="shelf_location" label="货架" rules={[{ required: true, message: '请输入货架位置' }]}>
            <Input placeholder="请输入货架位置" />
          </Form.Item>

          <Form.Item name="related_voucher" label="关联采购单号">
            <Select placeholder="请选择采购单号" options={purchaseOrderOptions} showSearch optionFilterProp="label" allowClear />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default InboundRecords;
