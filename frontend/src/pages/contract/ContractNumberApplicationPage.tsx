import React, { useEffect, useState } from 'react';
import { Button, Card, DatePicker, Descriptions, Form, Input, InputNumber, message, Space, Table, Typography, Upload } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import api from '@/services/api';

const { Title } = Typography;

type ContractNumberResult = {
  date: string;
  seq: number;
  contract_no: string;
  subject?: string;
  supplier?: string;
  related_order_no?: string;
  purchase_content?: string;
  quantity?: number | null;
  amount?: number | null;
  attachment_name?: string;
};

const formatNumber = (value: any) => {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) {
    return value ?? '-';
  }
  return Number.isInteger(numberValue)
    ? String(numberValue)
    : numberValue.toFixed(4).replace(/\.?0+$/, '');
};

const formatAmount = (value: any) => {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) {
    return value ?? '-';
  }
  return numberValue.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const ContractNumberApplicationPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ContractNumberResult | null>(null);
  const [list, setList] = useState<any[]>([]);
  const [listLoading, setListLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');

  const loadList = async (page = 1, pageSize = 10) => {
    try {
      setListLoading(true);
      const params: any = { page, per_page: pageSize };
      if (keyword) params.keyword = keyword;
      const res = await api.get('/visiray/contract-number/list', { params });
      if (res.data.success) {
        const data = res.data.data || { items: [], total: 0 };
        setList(data.items || []);
        setPagination({
          current: data.current_page || page,
          pageSize: data.per_page || pageSize,
          total: data.total || 0,
        });
      }
    } catch (e) {
      message.error('获取合同号列表失败');
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    loadList(1, pagination.pageSize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleApply = async () => {
    try {
      const values = await form.validateFields();
      const formData = new FormData();
      const dateValue = values.date as dayjs.Dayjs | undefined;
      if (dateValue) {
        formData.append('date', dateValue.format('YYYY-MM-DD'));
      }
      ['subject', 'supplier', 'related_order_no', 'purchase_content', 'remark'].forEach((field) => {
        if (values[field] !== undefined && values[field] !== null) {
          formData.append(field, String(values[field]));
        }
      });
      if (values.quantity !== undefined && values.quantity !== null) {
        formData.append('quantity', String(values.quantity));
      }
      if (values.amount !== undefined && values.amount !== null) {
        formData.append('amount', String(values.amount));
      }
      const attachmentFile = values.attachment?.[0]?.originFileObj;
      if (attachmentFile) {
        formData.append('attachment', attachmentFile);
      }

      setLoading(true);
      const res = await api.post('/visiray/contract-number/apply', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (res.data.success) {
        setResult(res.data.data);
        message.success('合同号申请成功');
        form.resetFields();
        form.setFieldsValue({ date: dayjs() });
        loadList(1, pagination.pageSize);
      } else {
        message.error(res.data.message || '合同号申请失败');
      }
    } catch (e: any) {
      if (e?.errorFields) {
        return;
      }
      message.error(e?.response?.data?.message || '合同号申请失败');
    } finally {
      setLoading(false);
    }
  };

  const attachmentLink = (record: any) => {
    if (!record.attachment_file) {
      return '-';
    }
    return (
      <Button
        type="link"
        style={{ padding: 0 }}
        href={`/api/visiray/contract-number/${encodeURIComponent(record.contract_no)}/attachment`}
        target="_blank"
      >
        {record.attachment_name || '下载附件'}
      </Button>
    );
  };

  return (
    <Card>
      <Space direction="vertical" style={{ width: '100%' }} size={16}>
        <Title level={3} style={{ margin: 0 }}>合同号申请</Title>
        <Form form={form} layout="vertical" initialValues={{ date: dayjs() }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(180px, 1fr))', gap: 16 }}>
            <Form.Item name="date" label="日期">
              <DatePicker allowClear format="YYYY-MM-DD" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="subject" label="绑定事宜" rules={[{ required: true, message: '请填写合同绑定事宜' }]}>
              <Input placeholder="例如：采购合同、设备合同" />
            </Form.Item>
            <Form.Item name="supplier" label="供应商">
              <Input placeholder="供应商名称" />
            </Form.Item>
            <Form.Item name="related_order_no" label="关联采购单">
              <Input placeholder="采购单号" />
            </Form.Item>
            <Form.Item name="purchase_content" label="采购内容">
              <Input.TextArea placeholder="请输入采购内容" autoSize={{ minRows: 1, maxRows: 3 }} />
            </Form.Item>
            <Form.Item name="quantity" label="数量">
              <InputNumber min={0} precision={4} placeholder="请输入数量" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="amount" label="金额">
              <InputNumber min={0} precision={2} placeholder="请输入金额" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="attachment"
              label="附件"
              valuePropName="fileList"
              getValueFromEvent={(event) => Array.isArray(event) ? event : event?.fileList}
            >
              <Upload beforeUpload={() => false} maxCount={1}>
                <Button icon={<UploadOutlined />}>选择附件</Button>
              </Upload>
            </Form.Item>
          </div>
          <Form.Item name="remark" label="备注">
            <Input.TextArea placeholder="备注" autoSize={{ minRows: 2, maxRows: 4 }} />
          </Form.Item>
          <Button type="primary" onClick={handleApply} loading={loading}>申请合同号</Button>
        </Form>

        {result && (
          <Descriptions title="申请结果" bordered column={2} size="small">
            <Descriptions.Item label="日期">{result.date}</Descriptions.Item>
            <Descriptions.Item label="序号">{String(result.seq).padStart(3, '0')}</Descriptions.Item>
            <Descriptions.Item label="合同号">{result.contract_no}</Descriptions.Item>
            <Descriptions.Item label="供应商">{result.supplier || '-'}</Descriptions.Item>
            <Descriptions.Item label="采购内容">{result.purchase_content || '-'}</Descriptions.Item>
            <Descriptions.Item label="数量">{formatNumber(result.quantity)}</Descriptions.Item>
            <Descriptions.Item label="金额">{formatAmount(result.amount)}</Descriptions.Item>
            <Descriptions.Item label="附件">{result.attachment_name || '-'}</Descriptions.Item>
          </Descriptions>
        )}

        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Title level={4} style={{ margin: 0 }}>历史合同号</Title>
          <Space>
            <Input
              placeholder="搜索合同号、事宜、供应商、采购单、采购内容"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onPressEnter={() => loadList(1, pagination.pageSize)}
              style={{ width: 360 }}
              allowClear
            />
            <Button onClick={() => loadList(1, pagination.pageSize)}>搜索</Button>
          </Space>
        </Space>
        <Table
          dataSource={list}
          loading={listLoading}
          rowKey={(record) => `${record.contract_no}-${record.seq}-${record.created_at}`}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            onChange: (page, pageSize) => loadList(page, pageSize),
            showSizeChanger: false,
          }}
          scroll={{ x: 'max-content' }}
          columns={[
            { title: '日期', dataIndex: 'date', key: 'date' },
            { title: '序号', dataIndex: 'seq', key: 'seq', render: (value: number) => String(value).padStart(3, '0') },
            { title: '合同号', dataIndex: 'contract_no', key: 'contract_no' },
            { title: '绑定事宜', dataIndex: 'subject', key: 'subject', ellipsis: true },
            { title: '供应商', dataIndex: 'supplier', key: 'supplier', ellipsis: true },
            { title: '关联采购单', dataIndex: 'related_order_no', key: 'related_order_no' },
            { title: '采购内容', dataIndex: 'purchase_content', key: 'purchase_content', ellipsis: true },
            { title: '数量', dataIndex: 'quantity', key: 'quantity', render: (value: any) => formatNumber(value) },
            { title: '金额', dataIndex: 'amount', key: 'amount', render: (value: any) => formatAmount(value) },
            { title: '附件', key: 'attachment', render: (_: any, record: any) => attachmentLink(record) },
            { title: '备注', dataIndex: 'remark', key: 'remark', ellipsis: true },
            { title: '申请人', dataIndex: 'created_by', key: 'created_by' },
            { title: '申请时间', dataIndex: 'created_at', key: 'created_at' },
          ]}
        />
      </Space>
    </Card>
  );
};

export default ContractNumberApplicationPage;
