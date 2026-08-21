import React, { useEffect, useState } from 'react';
import {
  AutoComplete,
  Button,
  Card,
  Descriptions,
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
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import api from '@/services/api';
import authService from '@/services/auth';

const { Title } = Typography;
const { Option } = Select;

const detailLabelStyle = { width: 120 };
const getDisplayPartId = (record: any) => record?.display_goods_id || record?.part_id || record?.goods_id || '-';
const getRecordList = (value: any) => String(value || '')
  .split(/[;,；，]/)
  .map(item => item.trim())
  .filter(Boolean);

const InventoryManagement: React.FC = () => {
  const [dataSource, setDataSource] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filters, setFilters] = useState({ supplier: '', goods_type: '', shelf_location: '', stock_status: '' });
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [modalTitle, setModalTitle] = useState('新增库存');
  const [editingGoodsId, setEditingGoodsId] = useState<number | null>(null);
  const [editingInventoryType, setEditingInventoryType] = useState<'legacy' | 'versioned'>('legacy');
  const [modalApi, modalContextHolder] = Modal.useModal();
  const [partOptions, setPartOptions] = useState<any[]>([]);

  const searchPartNumbers = async (q: string) => {
    try {
      const keyword = q.trim();
      if (!keyword) {
        setPartOptions([]);
        return;
      }
      const response = await api.get('/visiray/part-numbers', {
        params: { keyword, page: 1, per_page: 20 },
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
    form.setFieldsValue({
      goods_id: value,
      goods_name: option?.meta?.part_name || option?.meta?.sub_type || '',
      goods_type: option?.meta?.main_type || form.getFieldValue('goods_type'),
      unit: option?.meta?.unit || form.getFieldValue('unit'),
    });
  };

  const buildQueryParams = (page: number, keyword: string, activeFilters = filters) => {
    const params: Record<string, any> = { page, per_page: pagination.pageSize };
    const trimmedKeyword = keyword.trim();
    if (trimmedKeyword) {
      params.keyword = trimmedKeyword;
    }
    Object.entries(activeFilters).forEach(([key, value]) => {
      const filterValue = typeof value === 'string' ? value.trim() : value;
      if (filterValue) {
        params[key] = filterValue;
      }
    });
    return params;
  };

  const fetchInventoryData = async (page = 1, keyword = searchKeyword, activeFilters = filters) => {
    setLoading(true);
    try {
      const params = buildQueryParams(page, keyword, activeFilters);
      const [legacyResponse, versionedResponse] = await Promise.all([
        api.get('/visiray/inventory', { params }),
        api.get('/visiray/versioned-inventory', { params }),
      ]);
      const legacyData = legacyResponse.data.data || {};
      const versionedData = versionedResponse.data.data || {};
      const legacyItems = legacyResponse.data.success ? (legacyData.items || []) : [];
      const versionedItems = versionedResponse.data.success ? (versionedData.items || []) : [];
      setDataSource([...legacyItems, ...versionedItems]);
      setPagination(prev => ({
        ...prev,
        current: page,
        total: Number(legacyData.total || 0) + Number(versionedData.total || 0),
      }));
    } catch (error) {
      message.error('获取库存数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleResetFilters = () => {
    const emptyFilters = { supplier: '', goods_type: '', shelf_location: '', stock_status: '' };
    setSearchKeyword('');
    setFilters(emptyFilters);
    fetchInventoryData(1, '', emptyFilters);
  };

  const showEditModal = (record: any) => {
    setModalTitle('编辑库存');
    setEditingInventoryType(record.inventory_type === 'versioned' ? 'versioned' : 'legacy');
    setEditingGoodsId(record.inventory_type === 'versioned' ? record.id : record.goods_id);
    setIsModalVisible(true);
    form.setFieldsValue({ ...record, goods_id: getDisplayPartId(record) });
  };

  const showDetailModal = (record: any) => {
    modalApi.info({
      title: '库存详情',
      width: 600,
      content: (
        <div>
          <p><strong>零件号:</strong> {getDisplayPartId(record)}</p>
          <p><strong>零件名称:</strong> {record.goods_name}</p>
          <p><strong>供应商:</strong> {record.supplier}</p>
          <p><strong>商品型号:</strong> {record.product_model}</p>
          <p><strong>货品类型:</strong> {record.goods_type}</p>
          <p><strong>入库数量:</strong> {record.in_quantity}</p>
          <p><strong>出库数量:</strong> {record.out_quantity}</p>
          <p><strong>库存数量:</strong> {record.stock_quantity}</p>
          <p><strong>单位:</strong> {record.unit}</p>
          <p><strong>货架:</strong> {record.shelf_location}</p>
          <p><strong>入库记录:</strong> {record.in_record}</p>
          <p><strong>出库记录:</strong> {record.out_record}</p>
          <p><strong>附件:</strong> {record.attachments}</p>
          <p><strong>采购发票:</strong> {record.purchase_invoice}</p>
          <p><strong>发票信息:</strong> {record.invoice_info}</p>
          <p><strong>父记录:</strong> {record.parent_record}</p>
        </div>
      ),
    });
  };

  const showInboundRecordDetail = async (recordNo: string) => {
    try {
      const response = await api.get('/visiray/inbound', {
        params: { keyword: recordNo, page: 1, per_page: 20 },
      });
      const record = (response.data.data.items || []).find((item: any) => String(item.in_record) === String(recordNo));
      if (!record) {
        message.error('入库记录不存在');
        return;
      }
      modalApi.info({
        title: '入库记录详情',
        width: 720,
        content: (
          <Descriptions column={2} bordered size="small" labelStyle={detailLabelStyle}>
            <Descriptions.Item label="入库记录">{record.in_record}</Descriptions.Item>
            <Descriptions.Item label="零件号">{getDisplayPartId(record)}</Descriptions.Item>
            <Descriptions.Item label="供应商">{record.supplier_name || record.supplier || '-'}</Descriptions.Item>
            <Descriptions.Item label="数量">{record.quantity} {record.unit || ''}</Descriptions.Item>
            <Descriptions.Item label="入库日期">{record.in_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="入库人">{record.operator || '-'}</Descriptions.Item>
            <Descriptions.Item label="货架">{record.shelf_location || '-'}</Descriptions.Item>
            <Descriptions.Item label="货品类型">{record.goods_type || '-'}</Descriptions.Item>
            <Descriptions.Item label="商品型号">{record.product_model || '-'}</Descriptions.Item>
            <Descriptions.Item label="入库类型">{record.inbound_type || '-'}</Descriptions.Item>
            <Descriptions.Item label="关联采购单" span={2}>{record.related_voucher || '-'}</Descriptions.Item>
            <Descriptions.Item label="父记录" span={2}>{record.parent_record || '-'}</Descriptions.Item>
          </Descriptions>
        ),
      });
    } catch (error: any) {
      message.error(error?.response?.data?.message || '获取入库记录详情失败');
    }
  };

  const showOutboundRecordDetail = async (recordNo: string) => {
    try {
      const response = await api.get('/visiray/outbound', {
        params: { keyword: recordNo, page: 1, per_page: 20 },
      });
      const record = (response.data.data.items || []).find((item: any) => String(item.out_record_id) === String(recordNo));
      if (!record) {
        message.error('出库记录不存在');
        return;
      }
      modalApi.info({
        title: '出库记录详情',
        width: 720,
        content: (
          <Descriptions column={2} bordered size="small" labelStyle={detailLabelStyle}>
            <Descriptions.Item label="出库记录">{record.out_record_id}</Descriptions.Item>
            <Descriptions.Item label="零件号">{getDisplayPartId(record)}</Descriptions.Item>
            <Descriptions.Item label="零件名称">{record.goods_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="数量">{record.quantity || 0}</Descriptions.Item>
            <Descriptions.Item label="出库日期">{record.out_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="出库人">{record.operator || '-'}</Descriptions.Item>
            <Descriptions.Item label="货架">{record.shelf_location || '-'}</Descriptions.Item>
            <Descriptions.Item label="出库类型">{record.outbound_type || '-'}</Descriptions.Item>
          </Descriptions>
        ),
      });
    } catch (error: any) {
      message.error(error?.response?.data?.message || '获取出库记录详情失败');
    }
  };

  const renderRecordLinks = (value: any, type: 'inbound' | 'outbound') => {
    const records = getRecordList(value);
    if (!records.length) {
      return '-';
    }
    return (
      <Space size={4} wrap>
        {records.map((recordNo) => (
          <Button
            key={`${type}-${recordNo}`}
            type="link"
            size="small"
            style={{ padding: 0 }}
            onClick={() => type === 'inbound' ? showInboundRecordDetail(recordNo) : showOutboundRecordDetail(recordNo)}
          >
            {recordNo}
          </Button>
        ))}
      </Space>
    );
  };

  const openInboundRecordDetail = async (recordNo: string) => {
    try {
      const response = await api.get('/visiray/inbound', {
        params: { keyword: recordNo, page: 1, per_page: 20 },
      });
      const record = (response.data.data.items || []).find((item: any) => String(item.in_record) === String(recordNo));
      if (!record) {
        message.error('入库记录不存在');
        return;
      }
      modalApi.info({
        title: '入库记录详情',
        width: 600,
        content: (
          <div>
            <p><strong>入库记录:</strong> {record.in_record}</p>
            <p><strong>零件号:</strong> {getDisplayPartId(record)}</p>
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
    } catch (error: any) {
      message.error(error?.response?.data?.message || '获取入库记录详情失败');
    }
  };

  const openOutboundRecordDetail = async (recordNo: string) => {
    try {
      const response = await api.get('/visiray/outbound', {
        params: { keyword: recordNo, page: 1, per_page: 20 },
      });
      const record = (response.data.data.items || []).find((item: any) => String(item.out_record_id) === String(recordNo));
      if (!record) {
        message.error('出库记录不存在');
        return;
      }
      modalApi.info({
        title: '出库记录详情',
        width: 600,
        content: (
          <div>
            <p><strong>出库记录:</strong> {record.out_record_id}</p>
            <p><strong>零件号:</strong> {getDisplayPartId(record)}</p>
            <p><strong>零件名称:</strong> {record.goods_name}</p>
            <p><strong>数量:</strong> {record.quantity}</p>
            <p><strong>出库日期:</strong> {record.out_date}</p>
            <p><strong>出库人:</strong> {record.operator}</p>
            <p><strong>货架:</strong> {record.shelf_location}</p>
            <p><strong>出库类型:</strong> {record.outbound_type}</p>
          </div>
        ),
      });
    } catch (error: any) {
      message.error(error?.response?.data?.message || '获取出库记录详情失败');
    }
  };

  const renderRecordButton = (recordNo: string, type: 'inbound' | 'outbound') => (
    <Button
      type="link"
      size="small"
      style={{ padding: 0 }}
      onClick={() => type === 'inbound' ? openInboundRecordDetail(recordNo) : openOutboundRecordDetail(recordNo)}
    >
      {recordNo}
    </Button>
  );

  const showFoldedRecordListModal = (title: string, value: any, type: 'inbound' | 'outbound') => {
    const records = getRecordList(value);
    modalApi.info({
      title,
      width: 520,
      content: records.length ? (
        <div style={{ maxHeight: 360, overflowY: 'auto' }}>
          {records.map((item, index) => (
            <div
              key={`${type}-${item}-${index}`}
              style={{ padding: '6px 0', borderBottom: index === records.length - 1 ? 'none' : '1px solid #f0f0f0' }}
            >
              {index + 1}. {renderRecordButton(item, type)}
            </div>
          ))}
        </div>
      ) : '暂无记录',
    });
  };

  const renderFoldedRecordSummary = (value: any, title: string, type: 'inbound' | 'outbound') => {
    const records = getRecordList(value);
    if (!records.length) {
      return '-';
    }
    const latestRecord = records[records.length - 1];
    return (
      <Space size={4}>
        {renderRecordButton(latestRecord, type)}
        {records.length > 1 && (
          <Button type="link" size="small" style={{ padding: 0 }} onClick={() => showFoldedRecordListModal(title, value, type)}>
            共{records.length}条
          </Button>
        )}
      </Space>
    );
  };

  const showRecordListModal = (title: string, value: any) => {
    const records = getRecordList(value);
    modalApi.info({
      title,
      width: 520,
      content: records.length ? (
        <div style={{ maxHeight: 360, overflowY: 'auto' }}>
          {records.map((item, index) => (
            <div
              key={`${item}-${index}`}
              style={{ padding: '6px 0', borderBottom: index === records.length - 1 ? 'none' : '1px solid #f0f0f0' }}
            >
              {index + 1}. {item}
            </div>
          ))}
        </div>
      ) : '暂无记录',
    });
  };

  const renderRecordSummary = (value: any, title: string) => {
    const records = getRecordList(value);
    if (!records.length) {
      return '-';
    }
    const latestRecord = records[records.length - 1];
    return (
      <Space size={4}>
        <span>{latestRecord}</span>
        {records.length > 1 && (
          <Button type="link" size="small" style={{ padding: 0 }} onClick={() => showRecordListModal(title, value)}>
            共{records.length}条
          </Button>
        )}
      </Space>
    );
  };

  const handleDelete = async (goodsId: number) => {
    try {
      setLoading(true);
      const response = await api.delete(`/visiray/inventory/${goodsId}`);
      if (response.data.success) {
        message.success(response.data.message || '库存记录删除成功');
        fetchInventoryData(pagination.current, searchKeyword);
      } else {
        message.error(response.data.message || '删除库存记录失败');
      }
    } catch (error) {
      message.error('删除库存记录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      const response = editingGoodsId
        ? await api.put(editingInventoryType === 'versioned' ? `/visiray/versioned-inventory/${editingGoodsId}` : `/visiray/inventory/${editingGoodsId}`, values)
        : await api.post('/visiray/inventory', values);
      if (response.data.success) {
        message.success(response.data.message || (editingGoodsId ? '库存记录更新成功' : '库存记录创建成功'));
        setIsModalVisible(false);
        form.resetFields();
        fetchInventoryData(pagination.current, searchKeyword);
      } else {
        message.error(response.data.message || (editingGoodsId ? '更新库存记录失败' : '创建库存记录失败'));
      }
    } catch (error) {
      message.error(editingGoodsId ? '更新库存记录失败' : '创建库存记录失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventoryData();
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
    { title: '零件号', dataIndex: 'goods_id', key: 'goods_id', render: (_: any, record: any) => getDisplayPartId(record) },
    { title: '版本号', dataIndex: 'version_no', key: 'version_no', render: (value: any) => value || '-' },
    { title: '零件名称', dataIndex: 'goods_name', key: 'goods_name' },
    { title: '供应商', dataIndex: 'supplier', key: 'supplier' },
    { title: '商品型号', dataIndex: 'product_model', key: 'product_model' },
    { title: '货品类型', dataIndex: 'goods_type', key: 'goods_type' },
    { title: '入库数量', dataIndex: 'in_quantity', key: 'in_quantity' },
    { title: '出库数量', dataIndex: 'out_quantity', key: 'out_quantity' },
    { title: '库存数量', dataIndex: 'stock_quantity', key: 'stock_quantity' },
    { title: '单位', dataIndex: 'unit', key: 'unit' },
    { title: '货架', dataIndex: 'shelf_location', key: 'shelf_location' },
    { title: '入库记录', dataIndex: 'in_record', key: 'in_record', render: (value: any) => renderFoldedRecordSummary(value, '入库记录', 'inbound') },
    { title: '出库记录', dataIndex: 'out_record', key: 'out_record', render: (value: any) => renderFoldedRecordSummary(value, '出库记录', 'outbound') },
    { title: '附件', dataIndex: 'attachments', key: 'attachments' },
    { title: '采购发票', dataIndex: 'purchase_invoice', key: 'purchase_invoice' },
    { title: '发票信息', dataIndex: 'invoice_info', key: 'invoice_info' },
    { title: '父记录', dataIndex: 'parent_record', key: 'parent_record' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button type="link" icon={<EyeOutlined />} onClick={() => showDetailModal(record)} style={{ padding: 0 }}>查看详情</Button>
          {authService.isAdmin() && (
            <>
              <Button type="link" icon={<EditOutlined />} onClick={() => showEditModal(record)} style={{ padding: 0 }}>编辑</Button>
              {/*
              <Popconfirm
                title="确认删除"
                description="确定要删除这条库存记录吗？"
                onConfirm={() => handleDelete(record.goods_id)}
                okText="确认"
                cancelText="取消"
              >
                <Button type="link" icon={<DeleteOutlined />} danger style={{ padding: 0 }}>删除</Button>
              </Popconfirm>
              */}
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
        <Title level={3} style={{ margin: 0, display: 'inline-block' }}>库存管理</Title>
        <div style={{ float: 'right' }}>
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => fetchInventoryData(pagination.current, searchKeyword)}>刷新</Button>
          </Space>
        </div>
      </div>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input
            placeholder="搜索零件号、名称、供应商、型号"
            prefix={<SearchOutlined />}
            style={{ width: 240 }}
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            onPressEnter={() => fetchInventoryData(1, searchKeyword)}
            allowClear
          />
          <Input
            placeholder="供应商"
            style={{ width: 160 }}
            value={filters.supplier}
            onChange={(e) => setFilters({ ...filters, supplier: e.target.value })}
            onPressEnter={() => fetchInventoryData(1, searchKeyword)}
            allowClear
          />
          <Input
            placeholder="货品类型"
            style={{ width: 160 }}
            value={filters.goods_type}
            onChange={(e) => setFilters({ ...filters, goods_type: e.target.value })}
            onPressEnter={() => fetchInventoryData(1, searchKeyword)}
            allowClear
          />
          <Input
            placeholder="货架"
            style={{ width: 140 }}
            value={filters.shelf_location}
            onChange={(e) => setFilters({ ...filters, shelf_location: e.target.value })}
            onPressEnter={() => fetchInventoryData(1, searchKeyword)}
            allowClear
          />
          <Select
            placeholder="库存状态"
            style={{ width: 140 }}
            value={filters.stock_status || undefined}
            onChange={(value) => setFilters({ ...filters, stock_status: value || '' })}
            allowClear
          >
            <Option value="in_stock">有库存</Option>
            <Option value="out_of_stock">无库存</Option>
          </Select>
          <Button type="primary" icon={<SearchOutlined />} onClick={() => fetchInventoryData(1, searchKeyword)}>查询</Button>
          <Button onClick={handleResetFilters}>重置</Button>
        </Space>
      </Card>

      <Table
        dataSource={dataSource}
        columns={columns}
        loading={loading}
        rowKey="goods_id"
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          onChange: (page) => fetchInventoryData(page, searchKeyword),
          showSizeChanger: false,
        }}
        locale={{ emptyText: '暂无库存数据' }}
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
        <Form form={form} layout="vertical">
          <Form.Item name="goods_id" label="零件号" rules={[{ required: true, message: '请输入或选择零件号' }]}>
            <AutoComplete
              options={partOptions}
              onSearch={searchPartNumbers}
              onSelect={onSelectPart}
              onChange={(value) => form.setFieldsValue({ goods_id: value })}
              style={{ width: '100%' }}
              filterOption={(inputValue, option) => String(option?.label ?? '').toLowerCase().includes(inputValue.toLowerCase())}
            >
              <Input placeholder="请输入零件号或名称进行搜索" />
            </AutoComplete>
          </Form.Item>

          <Form.Item name="goods_name" label="零件名称" rules={[{ required: true, message: '请输入零件名称' }]}>
            <Input placeholder="选择零件号后自动带出，也可手动修改" />
          </Form.Item>

          <Form.Item name="supplier" label="供应商">
            <Input placeholder="请输入供应商" />
          </Form.Item>

          <Form.Item name="product_model" label="商品型号">
            <Input placeholder="请输入商品型号" />
          </Form.Item>

          <Form.Item name="goods_type" label="货品类型">
            <Input placeholder="请输入货品类型" />
          </Form.Item>

          <Form.Item name="in_quantity" label="入库数量">
            <InputNumber style={{ width: '100%' }} placeholder="请输入入库数量" min={0} />
          </Form.Item>

          <Form.Item name="out_quantity" label="出库数量">
            <InputNumber style={{ width: '100%' }} placeholder="请输入出库数量" min={0} />
          </Form.Item>

          <Form.Item name="stock_quantity" label="库存数量">
            <InputNumber style={{ width: '100%' }} placeholder="请输入库存数量" min={0} />
          </Form.Item>

          <Form.Item name="unit" label="单位">
            <Input placeholder="请输入单位" />
          </Form.Item>

          <Form.Item name="shelf_location" label="货架">
            <Input placeholder="请输入货架位置" />
          </Form.Item>

          <Form.Item name="in_record" label="入库记录">
            <Input placeholder="请输入入库记录" />
          </Form.Item>

          <Form.Item name="out_record" label="出库记录">
            <Input placeholder="请输入出库记录" />
          </Form.Item>

          <Form.Item name="attachments" label="附件">
            <Input placeholder="请输入附件" />
          </Form.Item>

          <Form.Item name="purchase_invoice" label="采购发票">
            <Input placeholder="请输入采购发票" />
          </Form.Item>

          <Form.Item name="invoice_info" label="发票信息">
            <Input placeholder="请输入发票信息" />
          </Form.Item>

          <Form.Item name="parent_record" label="父记录">
            <Input placeholder="请输入父记录" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default InventoryManagement;
