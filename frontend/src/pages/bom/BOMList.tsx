import React, { useEffect, useState } from 'react';
import {
  Button,
  Card,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
  Upload,
  message,
} from 'antd';
import {
  CopyOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useNavigate } from 'react-router-dom';

import { usePermissions } from '@/hooks/usePermissions';
import api from '@/services/api';
import { BOM, PaginatedResponse } from '@/types';

const { Title } = Typography;
const { Search } = Input;

const statusText: Record<string, string> = {
  draft: '草稿',
  active: '生效',
  inactive: '停用',
  obsolete: '作废',
};

const statusColor: Record<string, string> = {
  draft: 'orange',
  active: 'green',
  inactive: 'red',
  obsolete: 'default',
};

const BOMList: React.FC = () => {
  const navigate = useNavigate();
  const { isAdmin } = usePermissions();
  const [boms, setBoms] = useState<BOM[]>([]);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [upgradingId, setUpgradingId] = useState<number | null>(null);
  const [keyword, setKeyword] = useState('');
  const [status, setStatus] = useState<string | undefined>();
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });

  const fetchBoms = async (page = pagination.current, pageSize = pagination.pageSize) => {
    setLoading(true);
    try {
      const response = await api.get('/bom', {
        params: {
          page,
          per_page: pageSize,
          keyword: keyword || undefined,
          status,
        },
        timeout: 30000,
      });
      const data = response.data.data as PaginatedResponse<BOM>;
      setBoms(data.items || []);
      setPagination({ current: data.current_page || page, pageSize: data.per_page || pageSize, total: data.total || 0 });
    } catch (error: any) {
      message.error(error?.response?.data?.message || error?.message || '获取BOM列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBoms(1, pagination.pageSize);
  }, [keyword, status]);

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '删除BOM',
      content: '确定要将这个BOM删除吗？',
      okText: '删除',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await api.delete(`/bom/${id}`);
          message.success('BOM已移入回收站');
          fetchBoms();
        } catch (error: any) {
          message.error(error?.response?.data?.message || '删除失败');
        }
      },
    });
  };

  const handleUpgrade = (record: BOM) => {
    Modal.confirm({
      title: 'BOM版本升级',
      content: `将复制一份“${record.product_name}”的完整BOM结构，并自动生成下一个版本。确定继续吗？`,
      okText: '升级',
      cancelText: '取消',
      onOk: async () => {
        setUpgradingId(record.id);
        try {
          const response = await api.post(`/bom/${record.id}/upgrade`);
          const upgradedBom = response.data.data as BOM;
          message.success(response.data.message || 'BOM版本升级成功');
          navigate(`/bom/${upgradedBom.id}`);
        } catch (error: any) {
          message.error(error?.response?.data?.message || 'BOM版本升级失败');
        } finally {
          setUpgradingId(null);
        }
      },
    });
  };

  const handleImport = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    setImporting(true);
    try {
      const response = await api.post('/bom/import-xlsx', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      });
      message.success(response.data.message || 'BOM导入成功');
      fetchBoms(1, pagination.pageSize);
    } catch (error: any) {
      const errorMessage = error?.response?.data?.message || error?.message || 'BOM导入失败';
      Modal.error({
        title: 'BOM导入失败',
        content: <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{errorMessage}</pre>,
        width: 720,
      });
    } finally {
      setImporting(false);
    }
  };

  const columns: ColumnsType<BOM> = [
    {
      title: 'BOM编码',
      dataIndex: 'bom_code',
      width: 150,
      render: (text: string) => <span className="material-code">{text}</span>,
    },
    {
      title: '产品名称',
      dataIndex: 'product_name',
      ellipsis: true,
    },
    {
      title: '产品型号',
      dataIndex: 'product_model',
      width: 140,
      render: (text?: string) => text || '-',
    },
    {
      title: '版本',
      dataIndex: 'version',
      width: 90,
      align: 'center',
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      align: 'center',
      render: (value: string) => <Tag color={statusColor[value]}>{statusText[value] || value}</Tag>,
    },
    {
      title: '总成本',
      dataIndex: 'total_cost',
      width: 130,
      align: 'right',
      render: (value: number) => `￥${Number(value || 0).toLocaleString()}`,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (date: string) => (date ? new Date(date).toLocaleString() : '-'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      align: 'center',
      render: (_, record) => (
        <Space>
          <Tooltip title="查看">
            <Button type="text" icon={<EyeOutlined />} onClick={() => navigate(`/bom/${record.id}`)} />
          </Tooltip>
          {isAdmin() && (
            <>
              <Tooltip title="编辑树结构">
                <Button type="text" icon={<EditOutlined />} onClick={() => navigate(`/bom/${record.id}/edit`)} />
              </Tooltip>
              <Tooltip title="版本升级">
                <Button
                  type="text"
                  icon={<CopyOutlined />}
                  loading={upgradingId === record.id}
                  onClick={() => handleUpgrade(record)}
                />
              </Tooltip>
              <Tooltip title="删除">
                <Button type="text" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
              </Tooltip>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Card>
      <div className="table-header">
        <Title level={3} style={{ margin: 0 }}>BOM管理</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => fetchBoms()} loading={loading}>刷新</Button>
          {isAdmin() && (
            <>
              <Upload
                accept=".xlsx,.xlsm"
                showUploadList={false}
                beforeUpload={(file) => {
                  handleImport(file as File);
                  return false;
                }}
              >
                <Button icon={<UploadOutlined />} loading={importing}>导入BOM</Button>
              </Upload>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/bom/create')}>新建BOM</Button>
            </>
          )}
        </Space>
      </div>

      <Space style={{ marginBottom: 16 }} wrap>
        <Search
          placeholder="搜索BOM编码、产品名称、型号"
          allowClear
          enterButton={<SearchOutlined />}
          style={{ width: 320 }}
          onSearch={setKeyword}
        />
        <Select
          placeholder="状态"
          allowClear
          value={status}
          style={{ width: 140 }}
          onChange={setStatus}
          options={[
            { value: 'draft', label: '草稿' },
            { value: 'active', label: '生效' },
            { value: 'inactive', label: '停用' },
            { value: 'obsolete', label: '作废' },
          ]}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={boms}
        rowKey="id"
        loading={loading}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => fetchBoms(page, pageSize),
        }}
      />
    </Card>
  );
};

export default BOMList;
