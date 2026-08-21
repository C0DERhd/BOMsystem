import React, { useEffect, useState, useRef } from 'react';
import { Card, Typography, Table, Space, Button, Input, DatePicker, message, Empty, Modal, Form, InputNumber, Select, Popconfirm, Upload, List, Tag, AutoComplete } from 'antd';
import { SearchOutlined, ReloadOutlined, PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, UploadOutlined, PaperClipOutlined } from '@ant-design/icons';
import api from '@/services/api';
import dayjs from 'dayjs';
import authService from '@/services/auth';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

const PurchaseOrders: React.FC = () => {
  const [dataSource, setDataSource] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  
  // 新增/编辑采购对话框相关状态
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [modalTitle, setModalTitle] = useState('新增采购入库单');
  const [editingPurchaseOrderNo, setEditingPurchaseOrderNo] = useState<string | null>(null);
  const [attachmentsModalVisible, setAttachmentsModalVisible] = useState(false);
  const [currentOrderNo, setCurrentOrderNo] = useState<string | null>(null);
  const [attachments, setAttachments] = useState<any[]>([]);
  const [attachmentsUploading, setAttachmentsUploading] = useState(false);
  const [attachmentsFileList, setAttachmentsFileList] = useState<any[]>([]);
  const [editingRecord, setEditingRecord] = useState<any | null>(null);
  const [modalApi, modalContextHolder] = Modal.useModal();
  const [partOptions, setPartOptions] = useState<any[]>([]);
  const [productCodeInput, setProductCodeInput] = useState<string>('');
  const searchPartNumbers = async (q: string) => {
    try {
      if (!q || !q.trim()) { setPartOptions([]); return; }
      const res = await api.get('/visiray/part-numbers', { params: { keyword: q.trim() } });
      if (res.data.success) {
        const items = res.data.data.items || [];
        const options = items.map((it: any) => {
          const label = `${it.part_id}${it.part_name ? ' - ' + it.part_name : ''}`;
          return { value: it.part_id, label, meta: it };
        });
        setPartOptions(options);
      }
    } catch (e) { setPartOptions([]); }
  };
  const onSelectPart = (_val: string, option: any) => {
    setProductCodeInput(option?.value ?? '');
    form.setFieldsValue({ product_code: option?.value, product_name: option?.meta?.part_name || option?.meta?.sub_type || '' });
  };

  // 获取采购入库单数据
  const fetchPurchaseOrders = async (page = 1, keyword = '') => {
    setLoading(true);
    try {
      const response = await api.get('/visiray/purchase-orders', {
        params: {
          page: page,
          per_page: pagination.pageSize,
          keyword: keyword,
        },
      });
      
      if (response.data.success) {
        setDataSource(response.data.data.items);
        setPagination({
          ...pagination,
          current: page,
          total: response.data.data.total,
        });
      } else {
        message.error(response.data.message || '获取采购入库单失败');
      }
    } catch (error) {
      message.error('获取采购入库单失败');
    } finally {
      setLoading(false);
    }
  };

  // 刷新数据
  const handleRefresh = () => {
    fetchPurchaseOrders(pagination.current, searchKeyword);
  };

  // 搜索
  const handleSearch = () => {
    fetchPurchaseOrders(1, searchKeyword);
  };

  // 分页变化
  const handleTableChange = (page: number) => {
    fetchPurchaseOrders(page, searchKeyword);
  };

  // 显示新增采购对话框
  const showModal = () => {
    setModalTitle('新增采购单');
    setEditingPurchaseOrderNo(null);
    setIsModalVisible(true);
    form.resetFields();
  };

  // 显示编辑采购对话框
  const showEditModal = (record: any) => {
    setModalTitle('编辑采购单');
    setEditingPurchaseOrderNo(record.purchase_order_no);
    setIsModalVisible(true);
    setEditingRecord(record);
    setCurrentOrderNo(record.purchase_order_no);
    (async () => {
      try {
        const res = await api.get(`/visiray/purchase-orders/${record.purchase_order_no}/attachments`);
        if (res.data.success) {
          setAttachments(res.data.data || []);
        } else {
          message.error(res.data.message || '获取附件失败');
        }
      } catch (e: any) {
        const msg = e?.response?.data?.message || e?.message || '获取附件失败';
        message.error(msg);
      }
    })();
    
    const mapped = {
      purchase_order_no: record.purchase_order_no,
      product_code: record.goods_id,
      product_name: record.goods_name,
      quantity: record.purchase_quantity,
      unit: record.unit,
      product_type: record.goods_type,
      unit_price: record.purchase_price,
      receiving_time: record.inbound_time ? dayjs(record.inbound_time, 'YYYY-MM-DD') : null,
      status: record.status,
      supplier: record.supplier,
      invoice_no: record.purchase_invoice ? { fileList: [] } : undefined,
      contract_pdf: record.contract_pdf ? { fileList: [] } : undefined
    } as any;
    form.setFieldsValue(mapped);
  };

  // 显示详情对话框
  const showDetailModal = (record: any) => {
    modalApi.info({
      title: '采购单详情',
      width: 600,
      content: (
        <div>
          <p><strong>采购单号:</strong> {record.purchase_order_no}</p>
          <p><strong>零件号:</strong> {record.goods_id}</p>
          <p><strong>零件名称:</strong> {record.goods_name}</p>
          <p><strong>采购数量:</strong> {record.purchase_quantity}</p>
          <p><strong>单位:</strong> {record.unit}</p>
          <p><strong>货品类型:</strong> {record.goods_type}</p>
          <p><strong>采购单价:</strong> {record.purchase_price}</p>
          <p><strong>总价:</strong> {record.total_price}</p>
          <p><strong>入库时间:</strong> {record.inbound_time}</p>
          <p><strong>状态:</strong> {record.status}</p>
          <p><strong>供应商:</strong> {record.supplier}</p>
          <p><strong>采购发票:</strong> {record.purchase_invoice ? 
            <a href={`/api/visiray/purchase-orders/${record.purchase_order_no}/invoice`} target="_blank" rel="noopener noreferrer">
              {record.purchase_invoice}
            </a> : 
            ''}
          </p>
          <p><strong>入库合同:</strong> {record.contract_pdf ? 
            <a href={`/api/visiray/purchase-orders/${record.purchase_order_no}/contract`} target="_blank" rel="noopener noreferrer">
              {record.contract_pdf}
            </a> : 
            ''}
          </p>
        </div>
      ),
    });
  };

  const openAttachmentsModal = async (record: any) => {
    setCurrentOrderNo(record.purchase_order_no);
    setAttachmentsModalVisible(true);
    setAttachmentsFileList([]);
    try {
      const res = await api.get(`/visiray/purchase-orders/${record.purchase_order_no}/attachments`);
      if (res.data.success) {
        const list = res.data.data || [];
        setAttachments(list);
        setDataSource(prev => prev.map(r => r.purchase_order_no === record.purchase_order_no ? { ...r, attachment_count: list.length } : r));
      } else {
        message.error(res.data.message || '获取附件失败');
      }
    } catch (e: any) {
      const msg = e?.response?.data?.message || e?.message || '获取附件失败';
      message.error(msg);
    }
  };

  const handleUploadAttachments = async () => {
    if (!currentOrderNo) return;
    if (attachmentsFileList.length === 0) {
      message.warning('请选择文件');
      return;
    }
    const remaining = 100 - attachments.length;
    if (attachmentsFileList.length > remaining) {
      message.error(`最多还能上传${remaining}个附件`);
      return;
    }
    try {
      setAttachmentsUploading(true);
      const formData = new FormData();
      attachmentsFileList.forEach((f: any) => {
        formData.append('files', f.originFileObj);
      });
      const res = await api.post(`/visiray/purchase-orders/${currentOrderNo}/attachments`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 600000,
      });
      if (res.data.success) {
        message.success('附件上传成功');
        setAttachmentsFileList([]);
        const listRes = await api.get(`/visiray/purchase-orders/${currentOrderNo}/attachments`);
        if (listRes.data.success) {
          const list = listRes.data.data || [];
          setAttachments(list);
          setDataSource(prev => prev.map(r => r.purchase_order_no === currentOrderNo ? { ...r, attachment_count: list.length } : r));
        }
      } else {
        message.error(res.data.message || '上传失败');
      }
    } catch (e) {
      message.error('上传失败');
    } finally {
      setAttachmentsUploading(false);
    }
  };

  const handleDeleteAttachment = async (attId: number) => {
    if (!currentOrderNo) return;
    try {
      const res = await api.delete(`/visiray/purchase-orders/${currentOrderNo}/attachments/${attId}`);
      if (res.data.success) {
        message.success('删除成功');
        const listRes = await api.get(`/visiray/purchase-orders/${currentOrderNo}/attachments`);
        if (listRes.data.success) {
          const list = listRes.data.data || [];
          setAttachments(list);
          setDataSource(prev => prev.map(r => r.purchase_order_no === currentOrderNo ? { ...r, attachment_count: list.length } : r));
        }
      } else {
        message.error(res.data.message || '删除失败');
      }
    } catch (e) {
      message.error('删除失败');
    }
  };

  // 删除采购入库单
  const handleDelete = async (purchaseOrderNo: string) => {
    try {
      setLoading(true);
      const response = await api.delete(`/visiray/purchase-orders/${purchaseOrderNo}`);
      
      if (response.data.success) {
        message.success(response.data.message || '采购单删除成功');
        // 刷新数据
        fetchPurchaseOrders();
      } else {
        message.error(response.data.message || '删除采购单失败');
      }
    } catch (error) {
      message.error('删除采购单失败');
    } finally {
      setLoading(false);
    }
  };

  // 关闭对话框
  const handleCancel = () => {
    setIsModalVisible(false);
    form.resetFields();
    setEditingRecord(null);
    setAttachments([]);
  };

  // 提交表单
  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      
      // 处理日期格式
      if (values.receiving_time) {
        values.receiving_time = values.receiving_time.format('YYYY-MM-DD');
      }
      
      // 处理文件上传
      const formData = new FormData();
      
      // 添加所有字段到FormData
      Object.keys(values).forEach(key => {
        if (key === 'contract_pdf' && values[key] && values[key].fileList && values[key].fileList.length > 0) {
          // 处理入库合同文件上传
          const file = values[key].fileList[0].originFileObj;
          formData.append('contract_pdf', file);
        } else if (key === 'invoice_no' && values[key] && values[key].fileList && values[key].fileList.length > 0) {
          // 处理采购发票文件上传
          const file = values[key].fileList[0].originFileObj;
          formData.append('invoice_no', file);
        } else if (key !== 'contract_pdf' && key !== 'invoice_no') {
          // 其他字段直接添加
          formData.append(key, values[key]);
        }
      });
      
      setLoading(true);
      let response;
      
      if (editingPurchaseOrderNo) {
        // 编辑模式 - 使用PUT方法
        response = await api.put(`/visiray/purchase-orders/${editingPurchaseOrderNo}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
      } else {
        // 新增模式 - 使用POST方法
        response = await api.post('/visiray/purchase-orders', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
      }
      
      if (response && response.data.success) {
        message.success(response.data.message || (editingPurchaseOrderNo ? '采购单更新成功' : '采购单创建成功'));
        setIsModalVisible(false);
        form.resetFields();
        const orderNo = editingPurchaseOrderNo ? editingPurchaseOrderNo : response.data.data?.purchase_order_no;
        const other = (values as any).other_attachments;
        if (orderNo && other && other.fileList && other.fileList.length > 0) {
          const fd = new FormData();
          other.fileList.forEach((f: any) => {
            fd.append('files', f.originFileObj);
          });
          try {
            await api.post(`/visiray/purchase-orders/${orderNo}/attachments`, fd, {
              headers: { 'Content-Type': 'multipart/form-data' },
              timeout: 600000,
            });
          } catch (e) {
            message.error('其他附件上传失败');
          }
        }
        fetchPurchaseOrders();
      } else if (response) {
        message.error(response.data.message || (editingPurchaseOrderNo ? '更新采购单失败' : '创建采购单失败'));
      }
    } catch (error) {
      message.error(editingPurchaseOrderNo ? '更新采购单失败' : '创建采购单失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPurchaseOrders();
  }, []);

  const columns = [
    {
      title: '序号',
      dataIndex: 'index',
      key: 'index',
      render: (text: any, record: any, index: number) => (pagination.current - 1) * pagination.pageSize + index + 1,
      width: 60,
      align: 'center' as const,
    },
    {
      title: '采购单号',
      dataIndex: 'purchase_order_no',
      key: 'purchase_order_no',
    },
    {
      title: '零件号',
      dataIndex: 'goods_id',
      key: 'goods_id',
    },
    {
      title: '零件名称',
      dataIndex: 'goods_name',
      key: 'goods_name',
    },
    {
      title: '采购数量',
      dataIndex: 'purchase_quantity',
      key: 'purchase_quantity',
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
    },
    {
      title: '货品类型',
      dataIndex: 'goods_type',
      key: 'goods_type',
    },
    {
      title: '采购单价',
      dataIndex: 'purchase_price',
      key: 'purchase_price',
    },
    {
      title: '总价',
      dataIndex: 'total_price',
      key: 'total_price',
    },
    {
      title: '入库时间',
      dataIndex: 'inbound_time',
      key: 'inbound_time',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
    },
    {
      title: '供应商',
      dataIndex: 'supplier',
      key: 'supplier',
    },
    {
      title: '采购发票',
      dataIndex: 'purchase_invoice',
      key: 'purchase_invoice',
      render: (text: any) => (
        text ? 
        <span>{text}</span> : 
        <span></span>
      ),
    },
    {
      title: '入库合同',
      dataIndex: 'contract_pdf',
      key: 'contract_pdf',
      render: (text: any) => (
        text ? 
        <span>{text}</span> : 
        <span></span>
      ),
    },
    {
      title: '附件数',
      dataIndex: 'attachment_count',
      key: 'attachment_count',
      render: (text: any, record: any) => (
        <a onClick={() => openAttachmentsModal(record)}>{Number(text || 0)}</a>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => {
        const isAdmin = authService.isAdmin();
        return (
          <Space size="middle">
            <Button 
              type="link" 
              icon={<EyeOutlined />} 
              onClick={() => showDetailModal(record)}
              style={{ padding: 0 }}
            >
              查看详情
            </Button>
            <Button 
              type="link" 
              icon={<PaperClipOutlined />} 
              onClick={() => openAttachmentsModal(record)}
              style={{ padding: 0 }}
            >
              附件
            </Button>
            
            {isAdmin && (
              <>
                <Button 
                  type="link" 
                  icon={<EditOutlined />} 
                  onClick={() => showEditModal(record)}
                  style={{ padding: 0 }}
                >
                  编辑
                </Button>
                <Popconfirm
                  title="确认删除"
                  description="确定要删除这条采购单吗？"
                  onConfirm={() => handleDelete(record.purchase_order_no)}
                  okText="确认"
                  cancelText="取消"
                >
                  <Button 
                    type="link" 
                    icon={<DeleteOutlined />} 
                    danger
                    style={{ padding: 0 }}
                  >
                    删除
                  </Button>
                </Popconfirm>
              </>
            )}
          </Space>
        );
      },
    },
  ];

  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({
    index: 60,
    purchase_order_no: 160,
    goods_id: 120,
    goods_name: 160,
    purchase_quantity: 120,
    unit: 100,
    goods_type: 140,
    purchase_price: 120,
    total_price: 120,
    inbound_time: 140,
    status: 120,
    supplier: 160,
    purchase_invoice: 140,
    contract_pdf: 140,
    attachment_count: 100,
    action: 220,
  });

  const ResizableHeaderCell: React.FC<any> = (props) => {
    const { children, width, onResize, ...rest } = props;
    const startXRef = useRef(0);
    const startWRef = useRef<number>(width || 100);
    const draggingRef = useRef(false);
    const thRef = useRef<HTMLTableCellElement | null>(null);
    const onMouseDown = (e: React.MouseEvent) => {
      draggingRef.current = true;
      startXRef.current = e.clientX;
      startWRef.current = (thRef.current?.getBoundingClientRect().width || width || 100);
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
      e.preventDefault();
      e.stopPropagation();
    };
    const onMouseMove = (e: MouseEvent) => {
      if (!draggingRef.current) return;
      const delta = e.clientX - startXRef.current;
      const next = Math.max(60, Math.round(startWRef.current + delta));
      if (onResize) onResize(next);
    };
    const onMouseUp = () => {
      draggingRef.current = false;
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
    return (
      <th ref={thRef} style={{ width, position: 'relative' }} {...rest}>
        <div style={{ position: 'relative', width: '100%' }}>
          <div style={{ paddingRight: 8 }}>{children}</div>
          <span
            onMouseDown={onMouseDown}
            style={{ position: 'absolute', right: 0, top: 0, height: '100%', width: 12, cursor: 'col-resize', userSelect: 'none', transform: 'translateX(50%)', zIndex: 1 }}
          />
        </div>
      </th>
    );
  };

  const resizableColumns = columns.map((col: any) => ({
    ...col,
    ellipsis: col.ellipsis ?? true,
    width: columnWidths[col.key || col.dataIndex] || col.width,
    onHeaderCell: (column: any) => ({
      width: columnWidths[column.key || column.dataIndex] || column.width,
      onResize: (w: number) => {
        const key = column.key || column.dataIndex;
        setColumnWidths((prev) => ({ ...prev, [key]: w }));
      },
    }),
    onCell: (record: any) => ({
      style: {
        maxWidth: columnWidths[col.key || col.dataIndex] || col.width,
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
      },
    }),
  }));

  return (
    <Card>
      {modalContextHolder}
      <div style={{ marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0, display: 'inline-block' }}>采购单</Title>
        <div style={{ float: 'right' }}>
          <Space>
            <RangePicker 
              placeholder={['开始日期', '结束日期']} 
              value={dateRange}
              onChange={(dates) => setDateRange(dates)}
            />
            <Input 
              placeholder="搜索采购单号、供应商、零件名称" 
              prefix={<SearchOutlined />} 
              style={{ width: 250 }} 
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onPressEnter={handleSearch}
            />
            <Button icon={<ReloadOutlined />} onClick={handleRefresh}>刷新</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={showModal}>新增采购</Button>
          </Space>
        </div>
      </div>
      
      <Table 
        dataSource={dataSource} 
        columns={resizableColumns} 
        loading={loading}
        rowKey="purchase_order_no"
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          onChange: handleTableChange,
          showSizeChanger: false,
        }}
        components={{ header: { cell: ResizableHeaderCell } }}
        scroll={{ x: 'max-content' }}
        locale={{
          emptyText: (
            <Empty 
              description="暂无采购单数据" 
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )
        }}
      />
      
      {/* 新增/编辑采购对话框 */}
      <Modal
        title={modalTitle}
        open={isModalVisible}
        onOk={handleOk}
        onCancel={handleCancel}
        confirmLoading={loading}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            status: '待入库',
            receiving_time: dayjs(),
          }}
        >
          {/* 在编辑模式下显示采购单号字段 */}
          {editingPurchaseOrderNo && (
            <Form.Item
              name="purchase_order_no"
              label="采购单号"
              rules={[{ required: true, message: '请输入采购单号' }]}
            >
              <Input placeholder="请输入采购单号" />
            </Form.Item>
          )}
          
          <Form.Item
            name="product_code"
            label="零件号"
            rules={[{ required: true, message: '请输入或选择零件号' }]}
          >
            <AutoComplete
              options={partOptions}
              onSearch={searchPartNumbers}
              onSelect={onSelectPart}
              style={{ width: '100%' }}
              filterOption={(inputValue, option) => String(option?.label ?? '').toLowerCase().includes(inputValue.toLowerCase())}
            >
              <Input id="product_code" placeholder="请输入零件号或名称进行搜索" value={productCodeInput} onChange={(e) => setProductCodeInput(e.target.value)} />
            </AutoComplete>
          </Form.Item>
          
          <Form.Item
            name="product_name"
            label="零件名称"
            rules={[{ required: true, message: '请输入零件名称' }]}
          >
            <Input placeholder="请输入零件名称" />
          </Form.Item>
          
          <Form.Item
            name="quantity"
            label="采购数量"
            rules={[{ required: true, message: '请输入采购数量' }]}
          >
            <InputNumber style={{ width: '100%' }} placeholder="请输入采购数量" min={1} />
          </Form.Item>
          
          <Form.Item
            name="unit"
            label="单位"
            rules={[{ required: true, message: '请输入单位' }]}
          >
            <Select placeholder="请选择单位">
              <Option value="个">个</Option>
              <Option value="件">件</Option>
              <Option value="套">套</Option>
              <Option value="台">台</Option>
              <Option value="米">米</Option>
              <Option value="千克">千克</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="product_type"
            label="货品类型"
            rules={[{ required: true, message: '请输入货品类型' }]}
          >
            <Input placeholder="请输入货品类型" />
          </Form.Item>
          
          <Form.Item
            name="unit_price"
            label="采购单价"
            rules={[{ required: true, message: '请输入采购单价' }]}
          >
            <InputNumber 
              style={{ width: '100%' }} 
              placeholder="请输入采购单价" 
              min={0}
              precision={2}
              formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value!.replace(/\¥\s?|(,*)/g, '') as any}
            />
          </Form.Item>
          <Form.Item label="总价" shouldUpdate={(prev, curr) => prev.quantity !== curr.quantity || prev.unit_price !== curr.unit_price}>
            {() => {
              const q = Number(form.getFieldValue('quantity') || 0);
              const up = Number(form.getFieldValue('unit_price') || 0);
              const total = Number.isFinite(q * up) ? Number((q * up).toFixed(2)) : 0;
              return (
                <InputNumber
                  style={{ width: '100%' }}
                  value={total}
                  disabled
                  precision={2}
                  formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={value => value!.replace(/\¥\s?|(,*)/g, '') as any}
                />
              );
            }}
          </Form.Item>
          
          <Form.Item
            name="receiving_time"
            label="入库时间"
            rules={[{ required: true, message: '请选择入库时间' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            name="status"
            label="状态"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select placeholder="请选择状态">
              <Option value="待入库">待入库</Option>
              <Option value="已入库">已入库</Option>
              <Option value="已取消">已取消</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="supplier"
            label="供应商"
            rules={[{ required: true, message: '请输入供应商' }]}
          >
            <Input placeholder="请输入供应商" />
          </Form.Item>
          
          <Form.Item
            name="invoice_no"
            label="采购发票"
          >
            <Upload 
              name="invoice_no" 
              maxCount={1} 
              beforeUpload={() => false}
              accept=".pdf"
            >
              <Button icon={<UploadOutlined />}>点击上传PDF文件</Button>
            </Upload>
            {editingRecord?.purchase_invoice ? (
              <div style={{ marginTop: 8 }}>
                当前文件：
                <a
                  href={`/api/visiray/purchase-orders/${editingRecord.purchase_order_no}/invoice`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {editingRecord.purchase_invoice}
                </a>
                <Button
                  danger
                  type="link"
                  style={{ paddingLeft: 8 }}
                  onClick={async () => {
                    try {
                      const res = await api.delete(`/visiray/purchase-orders/${editingRecord.purchase_order_no}/invoice`);
                      if (res.data.success) {
                        message.success('采购发票已删除');
                        setEditingRecord({ ...editingRecord, purchase_invoice: null });
                      } else {
                        message.error(res.data.message || '删除失败');
                      }
                    } catch (e: any) {
                      const msg = e?.response?.data?.message || e?.message || '删除失败';
                      message.error(msg);
                    }
                  }}
                >
                  删除当前文件
                </Button>
              </div>
            ) : null}
          </Form.Item>
          
          <Form.Item
            name="contract_pdf"
            label="入库合同"
          >
            <Upload 
              name="contract_pdf" 
              maxCount={1} 
              beforeUpload={() => false}
              accept=".pdf"
            >
              <Button icon={<UploadOutlined />}>点击上传PDF文件</Button>
            </Upload>
            {editingRecord?.contract_pdf ? (
              <div style={{ marginTop: 8 }}>
                当前文件：
                <a
                  href={`/api/visiray/purchase-orders/${editingRecord.purchase_order_no}/contract`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {editingRecord.contract_pdf}
                </a>
                <Button
                  danger
                  type="link"
                  style={{ paddingLeft: 8 }}
                  onClick={async () => {
                    try {
                      const res = await api.delete(`/visiray/purchase-orders/${editingRecord.purchase_order_no}/contract`);
                      if (res.data.success) {
                        message.success('入库合同已删除');
                        setEditingRecord({ ...editingRecord, contract_pdf: null });
                      } else {
                        message.error(res.data.message || '删除失败');
                      }
                    } catch (e: any) {
                      const msg = e?.response?.data?.message || e?.message || '删除失败';
                      message.error(msg);
                    }
                  }}
                >
                  删除当前文件
                </Button>
              </div>
            ) : null}
          </Form.Item>
          <Form.Item
            name="other_attachments"
            label="其他附件"
          >
            <Upload
              multiple
              beforeUpload={(file) => {
                const ext = file.name.split('.').pop()?.toLowerCase();
                const allowed = ['pdf','doc','docx','xls','xlsx','ppt','pptx','png','jpg','jpeg','gif','txt','csv','zip','rar','7z'];
                if (!ext || !allowed.includes(ext)) {
                  message.error(`不支持的文件格式: ${file.name}`);
                  return Upload.LIST_IGNORE as any;
                }
                const maxMB = 120;
                if (file.size && file.size > maxMB * 1024 * 1024) {
                  message.error(`文件过大(>${maxMB}MB): ${file.name}`);
                  return Upload.LIST_IGNORE as any;
                }
                return false;
              }}
              accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.png,.jpg,.jpeg,.gif,.txt,.csv,.zip,.rar,.7z"
              maxCount={100}
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title="其他附件"
        open={attachmentsModalVisible}
        onCancel={() => { setAttachmentsModalVisible(false); setAttachmentsFileList([]); }}
        footer={null}
        width={720}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <Tag color="blue">已上传 {attachments.length} / 100</Tag>
            <Tag>剩余 {Math.max(0, 100 - attachments.length)}</Tag>
          </Space>
          <Upload
            multiple
            fileList={attachmentsFileList}
            onChange={({ fileList }) => setAttachmentsFileList(fileList)}
            beforeUpload={(file) => {
              const ext = file.name.split('.').pop()?.toLowerCase();
              const allowed = ['pdf','doc','docx','xls','xlsx','ppt','pptx','png','jpg','jpeg','gif','txt','csv','zip','rar','7z'];
              if (!ext || !allowed.includes(ext)) {
                message.error(`不支持的文件格式: ${file.name}`);
                return Upload.LIST_IGNORE as any;
              }
              const maxMB = 120;
              if (file.size && file.size > maxMB * 1024 * 1024) {
                message.error(`文件过大(>${maxMB}MB): ${file.name}`);
                return Upload.LIST_IGNORE as any;
              }
              return false;
            }}
            accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.png,.jpg,.jpeg,.gif,.txt,.csv,.zip,.rar,.7z"
            maxCount={100}
          >
            <Button icon={<UploadOutlined />}>选择文件</Button>
          </Upload>
          <Button type="primary" onClick={handleUploadAttachments} loading={attachmentsUploading}>
            上传附件
          </Button>
          <List
            header={attachments.length ? '已上传附件' : '暂无附件'}
            dataSource={attachments}
            renderItem={(item: any) => (
              <List.Item key={item.id}
                actions={[
                  <a onClick={async () => {
                    try {
                      const res = await api.get(`/visiray/purchase-orders/${item.purchase_order_no}/attachments/${item.id}/preview`, { responseType: 'blob' });
                      const url = window.URL.createObjectURL(res.data);
                      window.open(url, '_blank');
                    } catch (e) {
                      message.error('预览失败');
                    }
                  }}>预览</a>,
                  <a onClick={async () => {
                    try {
                      const res = await api.get(`/visiray/purchase-orders/${item.purchase_order_no}/attachments/${item.id}`, { responseType: 'blob' });
                      const blobUrl = window.URL.createObjectURL(res.data);
                      const link = document.createElement('a');
                      link.href = blobUrl;
                      link.download = item.original_filename || '附件';
                      document.body.appendChild(link);
                      link.click();
                      link.remove();
                      window.URL.revokeObjectURL(blobUrl);
                    } catch (e) {
                      message.error('下载失败');
                    }
                  }}>下载</a>,
                  <a onClick={() => handleDeleteAttachment(item.id)}>删除</a>
                ]}
              >
              <List.Item.Meta
                title={item.original_filename}
                description={`类型: ${item.content_type || ''} 大小: ${formatBytes(item.file_size)}`}
              />
              </List.Item>
            )}
          />
        </Space>
      </Modal>
    </Card>
  );
};

export default PurchaseOrders;
  const formatBytes = (size?: number) => {
    if (!size || size <= 0) return '0 B';
    const kb = 1024;
    const mb = kb * 1024;
    const gb = mb * 1024;
    if (size >= gb) return `${(size / gb).toFixed(2)} GB`;
    if (size >= mb) return `${(size / mb).toFixed(2)} MB`;
    if (size >= kb) return `${(size / kb).toFixed(2)} KB`;
    return `${size} B`;
  };
