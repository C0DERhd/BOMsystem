import React, { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { PlusOutlined, ReloadOutlined, StopOutlined } from '@ant-design/icons';
import api from '@/services/api';
import authService from '@/services/auth';

const { Title, Text } = Typography;

type PartVersion = {
  id: number;
  part_id: string;
  version_no: string;
  status: 'active' | 'obsolete';
  is_current: boolean;
  remark?: string;
  created_at?: string;
};

type PartRecord = {
  part_id: string;
  part_name?: string;
  category?: string;
  main_type?: string;
  sub_type?: string;
  versions?: PartVersion[];
};

const PartNumberVersionManagementPage: React.FC = () => {
  const [parts, setParts] = useState<PartRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedPart, setSelectedPart] = useState<PartRecord | null>(null);
  const [saving, setSaving] = useState(false);
  const [keyword, setKeyword] = useState('');
  const [form] = Form.useForm();

  const fetchParts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/visiray/part-numbers', {
        params: { all: 1 },
      });
      if (!response.data.success) {
        throw new Error(response.data.message || '获取零件版本失败');
      }
      setParts(response.data.data.items || []);
    } catch (error: any) {
      message.error(error?.response?.data?.message || error?.message || '获取零件版本失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchParts();
  }, []);

  const openCreate = (part: PartRecord) => {
    setSelectedPart(part);
    form.resetFields();
    form.setFieldsValue({ version_no: '', remark: '' });
    setModalOpen(true);
  };

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      await api.post(`/visiray/part-number/${encodeURIComponent(selectedPart!.part_id)}/versions`, {
        version_no: values.version_no,
        remark: values.remark,
        auto_current: true,
      });
      message.success('零件版本创建成功');
      setModalOpen(false);
      fetchParts();
    } catch (error: any) {
      if (!error?.errorFields) {
        message.error(error?.response?.data?.message || error?.message || '创建零件版本失败');
      }
    } finally {
      setSaving(false);
    }
  };

  const setCurrent = async (version: PartVersion) => {
    try {
      await api.post(`/visiray/part-number-versions/${version.id}/set-current`);
      message.success('当前版本已更新');
      fetchParts();
    } catch (error: any) {
      message.error(error?.response?.data?.message || error?.message || '设置当前版本失败');
    }
  };

  const obsolete = async (version: PartVersion) => {
    try {
      await api.post(`/visiray/part-number-versions/${version.id}/obsolete`);
      message.success('版本已废弃');
      fetchParts();
    } catch (error: any) {
      message.error(error?.response?.data?.message || error?.message || '废弃版本失败');
    }
  };

  const filteredParts = useMemo(() => {
    const text = keyword.trim().toLowerCase();
    if (!text) {
      return parts;
    }

    return parts.filter((part) => {
      const fields = [
        part.part_id,
        part.part_name,
        part.category,
        part.main_type,
        part.sub_type,
        ...(part.versions || []).map((version) => version.version_no),
      ];
      return fields.some((value) => String(value || '').toLowerCase().includes(text));
    });
  }, [keyword, parts]);

  const columns = useMemo(() => [
    {
      title: '零件号',
      dataIndex: 'part_id',
      key: 'part_id',
      width: 180,
      render: (value: string, record: PartRecord) => (
        <Space direction="vertical" size={0}>
          <Text strong>{value}</Text>
          <Text type="secondary">{record.part_name || record.sub_type || record.main_type || '-'}</Text>
        </Space>
      ),
    },
    {
      title: '版本',
      key: 'versions',
      render: (_: unknown, record: PartRecord) => (
        <Space wrap>
          {(record.versions || []).map((version) => (
            <Tag key={version.id} color={version.status === 'obsolete' ? 'default' : version.is_current ? 'blue' : 'green'}>
              {version.version_no}
              {version.is_current ? ' 当前' : ''}
              {version.status === 'obsolete' ? ' 已废弃' : ''}
            </Tag>
          ))}
          {!(record.versions || []).length && <Text type="secondary">暂无版本</Text>}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 360,
      render: (_: unknown, record: PartRecord) => {
        const versions = record.versions || [];

        return (
          <Space direction="vertical" size={6}>
            <Button type="link" icon={<PlusOutlined />} onClick={() => openCreate(record)}>
              新增版本
            </Button>
            {versions.map((version) => (
              <Space key={version.id} size={8} wrap>
                <Tag color={version.status === 'obsolete' ? 'default' : version.is_current ? 'blue' : 'green'}>
                  {version.version_no}
                  {version.is_current ? ' 当前' : ''}
                  {version.status === 'obsolete' ? ' 已废弃' : ''}
                </Tag>
                {version.is_current && version.status === 'active' && (
                  <Text type="secondary">当前版本</Text>
                )}
                {!version.is_current && version.status === 'active' && (
                  <>
                    <Button type="link" onClick={() => setCurrent(version)}>设为当前</Button>
                    <Popconfirm
                      title={`确认废弃 ${version.version_no} 版本？`}
                      description="废弃后不能加入新 BOM，但历史 BOM、报价和库存仍会保留。"
                      okText="确认"
                      cancelText="取消"
                      onConfirm={() => obsolete(version)}
                    >
                      <Button type="link" danger icon={<StopOutlined />}>废弃</Button>
                    </Popconfirm>
                  </>
                )}
              </Space>
            ))}
          </Space>
        );
      },
    },
  ], []);

  return (
    <Card>
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        <Space style={{ justifyContent: 'space-between', width: '100%' }}>
          <div>
            <Title level={3} style={{ margin: 0 }}>零件版本管理</Title>
            <Text type="secondary">同一个零件号可以维护多个四位数字版本，新增版本会自动成为当前版本。</Text>
          </div>
          <Space>
            <Input.Search
              allowClear
              placeholder="搜索零件号、名称或版本号"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              style={{ width: 280 }}
            />
            <Button icon={<ReloadOutlined />} onClick={fetchParts}>刷新</Button>
          </Space>
        </Space>
        <Table
          rowKey="part_id"
          loading={loading}
          dataSource={filteredParts}
          columns={columns}
          pagination={{
            pageSize: 12,
            showSizeChanger: false,
            showTotal: (total) => `共 ${total} 个零件`,
          }}
          scroll={{ x: 900 }}
        />
      </Space>

      <Modal
        title={`为 ${selectedPart?.part_id || ''} 新增版本`}
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="version_no"
            label="版本号"
            rules={[
              { required: true, message: '请输入版本号' },
              { pattern: /^\d{4}$/, message: '版本号必须是四位数字，例如 0001' },
            ]}
          >
            <Input maxLength={4} placeholder="例如 0001" />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default PartNumberVersionManagementPage;
