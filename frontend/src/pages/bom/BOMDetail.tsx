import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Button,
  Card,
  Col,
  Descriptions,
  InputNumber,
  Modal,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Tabs,
  Tag,
  Tree,
  Typography,
  message,
} from 'antd';
import {
  ArrowLeftOutlined,
  BranchesOutlined,
  CalculatorOutlined,
  CopyOutlined,
  DownloadOutlined,
  DollarOutlined,
  EditOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import { usePermissions } from '@/hooks/usePermissions';
import api from '@/services/api';
import { BOM, BOMItem, BOMShortageItem, BOMShortageReport } from '@/types';

const { Text } = Typography;

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

const levelLabels: Record<number, string> = {
  1: '模块',
  2: '子组件',
  3: '零件',
};

const formatDate = (value?: string) => (value ? new Date(value).toLocaleDateString() : '-');
const formatQuantity = (value?: number) => Number(value || 0).toLocaleString(undefined, {
  maximumFractionDigits: 4,
});
const isCostExcludedStatus = (status?: string) => status === 'inactive' || status === 'obsolete';

const buildItemTree = (items: BOMItem[] = []) => {
  const childrenByParent = new Map<number | undefined, BOMItem[]>();
  items.forEach((item) => {
    const parentId = item.parent_item_id || undefined;
    const siblings = childrenByParent.get(parentId) || [];
    siblings.push(item);
    childrenByParent.set(parentId, siblings);
  });

  const build = (parentId?: number): any[] => {
    return (childrenByParent.get(parentId) || [])
      .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
      .map((item) => ({
        key: String(item.id),
        title: item.material_name || item.sub_bom_code || item.item_no || `项目${item.id}`,
        item,
        children: build(item.id),
      }));
  };

  return build(undefined);
};

const buildNestedItemTree = (items: BOMItem[] = [], path = 'root'): any[] => {
  return [...items]
    .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
    .map((item, index) => ({
      key: `${path}-${item.bom_id}-${item.id}-${index}`,
      title: item.material_name || item.sub_bom_code || item.item_no || `项目${item.id}`,
      item,
      children: buildNestedItemTree(item.children || [], `${path}-${item.bom_id}-${item.id}-${index}`),
    }));
};

const BOMDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isAdmin } = usePermissions();
  const [bom, setBom] = useState<BOM | null>(null);
  const [loading, setLoading] = useState(true);
  const [exportLoading, setExportLoading] = useState(false);
  const [upgradeLoading, setUpgradeLoading] = useState(false);
  const [shortageLoading, setShortageLoading] = useState(false);
  const [shortageQuantity, setShortageQuantity] = useState<number>(1);
  const [shortageReport, setShortageReport] = useState<BOMShortageReport | null>(null);

  const fetchShortageReport = async (quantity?: number) => {
    if (!id) return;
    const queryQuantity = quantity || shortageQuantity || bom?.base_quantity || 1;
    setShortageLoading(true);
    try {
      const response = await api.get(`/bom/${id}/shortage`, {
        params: { quantity: queryQuantity },
        // 缺料清单需要递归展开子 BOM 并查询库存，允许更长的服务端计算时间。
        timeout: 30000,
      });
      setShortageReport(response.data.data);
      setShortageQuantity(response.data.data?.production_quantity || queryQuantity);
    } catch (error: any) {
      message.error(error?.response?.data?.message || '获取缺料清单失败');
    } finally {
      setShortageLoading(false);
    }
  };

  const fetchBomDetail = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await api.get(`/bom/${id}`);
      const nextBom = response.data.data as BOM;
      setBom(nextBom);
      setShortageQuantity(nextBom.base_quantity || 1);
      fetchShortageReport(nextBom.base_quantity || 1);
    } catch (error: any) {
      message.error(error?.response?.data?.message || '获取BOM详情失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBomDetail();
  }, [id]);

  const handleSupplierChange = async (itemBomId: number, itemId: number, supplierPriceId: number) => {
    if (!id || !itemBomId) return;
    try {
      const response = await api.patch(`/bom/${itemBomId}/items/${itemId}/supplier`, {
        selected_supplier_id: supplierPriceId,
      });
      if (response.data.success) {
        message.success(response.data.message || '供应商已切换');
        fetchBomDetail();
      } else {
        message.error(response.data.message || '切换供应商失败');
      }
    } catch (error: any) {
      message.error(error?.response?.data?.message || '切换供应商失败');
    }
  };

  const handleVersionChange = async (itemBomId: number, itemId: number, partVersionId: number) => {
    if (!id || !itemBomId) return;
    try {
      const response = await api.patch(`/bom/${itemBomId}/items/${itemId}/version`, {
        part_version_id: partVersionId,
      });
      if (response.data.success) {
        message.success(response.data.message || '零件版本已切换');
        fetchBomDetail();
      } else {
        message.error(response.data.message || '切换零件版本失败');
      }
    } catch (error: any) {
      message.error(error?.response?.data?.message || '切换零件版本失败');
    }
  };

  const handleUpgrade = () => {
    if (!id || !bom) return;
    Modal.confirm({
      title: 'BOM版本升级',
      content: `将复制一份“${bom.product_name}”的完整BOM结构，并自动生成下一个版本。确定继续吗？`,
      okText: '升级',
      cancelText: '取消',
      onOk: async () => {
        setUpgradeLoading(true);
        try {
          const response = await api.post(`/bom/${id}/upgrade`);
          const upgradedBom = response.data.data as BOM;
          message.success(response.data.message || 'BOM版本升级成功');
          navigate(`/bom/${upgradedBom.id}`);
        } catch (error: any) {
          message.error(error?.response?.data?.message || 'BOM版本升级失败');
        } finally {
          setUpgradeLoading(false);
        }
      },
    });
  };

  const handleExport = async () => {
    if (!id || !bom) return;
    setExportLoading(true);
    try {
      const response = await api.get(`/bom/${id}/export-xlsx`, {
        responseType: 'blob',
        timeout: 60000,
      });
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${bom.bom_code}_BOM.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      message.success('BOM导出成功');
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'BOM导出失败');
    } finally {
      setExportLoading(false);
    }
  };

  const treeData = useMemo(() => {
    if (bom?.tree_structure?.length) {
      return buildNestedItemTree(bom.tree_structure as unknown as BOMItem[]);
    }
    return buildItemTree(bom?.items || []);
  }, [bom?.items, bom?.tree_structure]);

  const itemColumns: ColumnsType<BOMItem> = [
    {
      title: '层级',
      dataIndex: 'level',
      width: 90,
      align: 'center',
      render: (value: number) => levelLabels[value] || `第${value}层`,
    },
    { title: '序号', dataIndex: 'item_no', width: 90, render: (value?: string) => value || '-' },
    {
      title: '物料/BOM编码',
      width: 180,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text>{record.material_code || record.sub_bom_code || '-'}</Text>
          {isCostExcludedStatus((record as any).sub_bom_status) && <Tag color="default">停用/作废不计价</Tag>}
        </Space>
      ),
    },
    {
      title: '名称',
      ellipsis: true,
      render: (_, record) => record.material_name || record.sub_bom_code || '-',
    },
    {
      title: '版本号',
      width: 150,
      render: (_, record) => (
        record.material_id ? (
          isAdmin() && record.version_options?.length ? (
            <Select
              size="small"
              value={record.part_version_id}
              placeholder="无版本"
              style={{ width: 120 }}
              onChange={(value) => handleVersionChange(record.bom_id, record.id, value)}
              options={record.version_options
                .filter((item) => item.status === 'active' || item.id === record.part_version_id)
                .map((item) => ({
                  value: item.id,
                  label: `${item.version_no}${item.is_current ? ' 当前' : ''}${item.status === 'obsolete' ? ' 废弃' : ''}`,
                  disabled: item.status === 'obsolete',
                }))}
            />
          ) : (
            <Tag color={record.version_no ? 'blue' : 'default'}>{record.version_no || '无版本'}</Tag>
          )
        ) : '-'
      ),
    },
    { title: '数量', dataIndex: 'quantity', width: 90, align: 'right' },
    { title: '单位', dataIndex: 'unit', width: 80, align: 'center' },
    {
      title: '供应商',
      dataIndex: 'selected_supplier_name',
      width: 140,
      render: (value?: string, record?: BOMItem) => (
        <Space>
          {record?.has_multiple_suppliers && <Tag color="gold">多</Tag>}
          <span>{value || '-'}</span>
        </Space>
      ),
    },
    {
      title: '单价',
      dataIndex: 'selected_supplier_price',
      width: 110,
      align: 'right',
      render: (value: number) => `￥${Number(value || 0).toFixed(4)}`,
    },
    {
      title: '损耗率',
      dataIndex: 'usage_rate',
      width: 90,
      align: 'right',
      render: (value: number) => Number(value || 1).toFixed(4),
    },
    {
      title: '替代组',
      dataIndex: 'substitute_group',
      width: 110,
      render: (value?: string) => value || '-',
    },
    {
      title: '替代优先级',
      dataIndex: 'substitute_priority',
      width: 110,
      align: 'center',
      render: (value?: number) => value || '-',
    },
    {
      title: '生效日期',
      dataIndex: 'effective_date',
      width: 120,
      render: formatDate,
    },
    {
      title: '失效日期',
      dataIndex: 'expiry_date',
      width: 120,
      render: formatDate,
    },
    {
      title: '属性',
      width: 150,
      render: (_, record) => (
        <Space>
          {record.is_key_material && <Tag color="red">关键</Tag>}
          {record.is_optional && <Tag color="blue">可选</Tag>}
        </Space>
      ),
    },
    {
      title: '小计',
      dataIndex: 'item_cost',
      width: 120,
      align: 'right',
      render: (value: number) => `￥${Number(value || 0).toFixed(2)}`,
    },
  ];

  const shortageColumns: ColumnsType<BOMShortageItem> = [
    {
      title: '零件号',
      width: 170,
      render: (_, record) => <span className="material-code">{record.part_id || record.material_code || '-'}</span>,
    },
    {
      title: '零件名称',
      dataIndex: 'material_name',
      ellipsis: true,
      render: (value?: string) => value || '-',
    },
    {
      title: '需求数量',
      dataIndex: 'required_quantity',
      width: 120,
      align: 'right',
      render: (value: number, record) => `${formatQuantity(value)} ${record.unit || ''}`,
    },
    {
      title: '当前库存',
      dataIndex: 'stock_quantity',
      width: 120,
      align: 'right',
      render: (value: number, record) => `${formatQuantity(value)} ${record.unit || ''}`,
    },
    {
      title: '缺料数量',
      dataIndex: 'shortage_quantity',
      width: 120,
      align: 'right',
      render: (value: number, record) => (
        <Text type={value > 0 ? 'danger' : undefined} strong={value > 0}>
          {formatQuantity(value)} {record.unit || ''}
        </Text>
      ),
    },
    {
      title: '属性',
      width: 150,
      render: (_, record) => (
        <Space>
          {record.is_key_material && <Tag color="red">关键</Tag>}
          {record.is_optional && <Tag color="blue">可选</Tag>}
          {!record.is_key_material && !record.is_optional && '-'}
        </Space>
      ),
    },
    {
      title: '替代组',
      dataIndex: 'substitute_group',
      width: 120,
      render: (value?: string, record?: BOMShortageItem) => (
        value ? `${value}/${record?.substitute_priority || 1}` : '-'
      ),
    },
    {
      title: '库存来源',
      dataIndex: 'stock_source',
      width: 120,
      render: (value: string) => value === 'visiray_inventory' ? '库存信息' : '物料库存',
    },
    {
      title: '供应商',
      dataIndex: 'inventory_supplier',
      width: 160,
      render: (value?: string) => value || '-',
    },
    {
      title: 'BOM路径',
      dataIndex: 'paths',
      width: 320,
      ellipsis: true,
      render: (paths?: string[]) => paths?.[0] || '-',
    },
  ];

  if (loading) {
    return <Spin />;
  }

  if (!bom) {
    return <Card>未找到BOM</Card>;
  }

  return (
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Space>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/bom')}>返回列表</Button>
        <Button icon={<DownloadOutlined />} loading={exportLoading} onClick={handleExport}>导出BOM</Button>
        {isAdmin() && (
          <>
            <Button type="primary" icon={<EditOutlined />} onClick={() => navigate(`/bom/${id}/edit`)}>编辑BOM</Button>
            <Button icon={<CopyOutlined />} loading={upgradeLoading} onClick={handleUpgrade}>版本升级</Button>
          </>
        )}
      </Space>

      <Card title="BOM基本信息">
        <Descriptions column={3} bordered>
          <Descriptions.Item label="BOM编码"><span className="material-code">{bom.bom_code}</span></Descriptions.Item>
          <Descriptions.Item label="产品名称">{bom.product_name}</Descriptions.Item>
          <Descriptions.Item label="产品型号">{bom.product_model || '-'}</Descriptions.Item>
          <Descriptions.Item label="版本">{bom.version}</Descriptions.Item>
          <Descriptions.Item label="状态"><Tag color={statusColor[bom.status]}>{statusText[bom.status] || bom.status}</Tag></Descriptions.Item>
          <Descriptions.Item label="基础数量">{bom.base_quantity} {bom.unit}</Descriptions.Item>
          <Descriptions.Item label="生效日期">{formatDate(bom.effective_date)}</Descriptions.Item>
          <Descriptions.Item label="失效日期">{formatDate(bom.expiry_date)}</Descriptions.Item>
          <Descriptions.Item label="产品规格" span={3}>{bom.product_spec || '-'}</Descriptions.Item>
          <Descriptions.Item label="工艺路线" span={3}>{bom.process_route || '-'}</Descriptions.Item>
          <Descriptions.Item label="生产周期">{bom.lead_time ? `${bom.lead_time}天` : '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间" span={2}>{bom.created_at ? new Date(bom.created_at).toLocaleString() : '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Row gutter={16}>
        <Col span={6}><Card><Statistic title="总成本" value={bom.total_cost || 0} prefix={<DollarOutlined />} suffix="元" /></Card></Col>
        <Col span={6}><Card><Statistic title="材料成本" value={bom.material_cost || 0} prefix={<CalculatorOutlined />} suffix="元" /></Card></Col>
        <Col span={6}><Card><Statistic title="人工成本" value={bom.labor_cost || 0} suffix="元" /></Card></Col>
        <Col span={6}><Card><Statistic title="制造费用" value={bom.overhead_cost || 0} suffix="元" /></Card></Col>
      </Row>

      <Card>
        <Tabs
          items={[
            {
              key: 'items',
              label: 'BOM明细',
              children: (
                <Table
                  columns={itemColumns}
                  dataSource={bom.items || []}
                  rowKey="id"
                  pagination={false}
                  scroll={{ x: 'max-content' }}
                />
              ),
            },
            {
              key: 'shortage',
              label: '缺料清单',
              children: (
                <Space direction="vertical" size={16} style={{ width: '100%' }}>
                  <Space wrap>
                    <Text>计划生产数量</Text>
                    <InputNumber
                      min={0.0001}
                      precision={4}
                      value={shortageQuantity}
                      onChange={(value) => setShortageQuantity(Number(value || 1))}
                      style={{ width: 160 }}
                    />
                    <Text type="secondary">{bom.unit}</Text>
                    <Button
                      type="primary"
                      icon={<WarningOutlined />}
                      loading={shortageLoading}
                      onClick={() => fetchShortageReport(shortageQuantity)}
                    >
                      查询缺料
                    </Button>
                  </Space>

                  <Row gutter={16}>
                    <Col span={6}>
                      <div style={{ padding: 16, border: '1px solid #f0f0f0', borderRadius: 6 }}>
                        <Statistic title="涉及零件" value={shortageReport?.summary.item_count || 0} suffix="项" />
                      </div>
                    </Col>
                    <Col span={6}>
                      <div style={{ padding: 16, border: '1px solid #f0f0f0', borderRadius: 6 }}>
                        <Statistic title="缺料零件" value={shortageReport?.summary.shortage_item_count || 0} suffix="项" />
                      </div>
                    </Col>
                    <Col span={6}>
                      <div style={{ padding: 16, border: '1px solid #f0f0f0', borderRadius: 6 }}>
                        <Statistic title="总需求量" value={shortageReport?.summary.total_required_quantity || 0} precision={4} />
                      </div>
                    </Col>
                    <Col span={6}>
                      <div style={{ padding: 16, border: '1px solid #f0f0f0', borderRadius: 6 }}>
                        <Statistic title="总缺料量" value={shortageReport?.summary.total_shortage_quantity || 0} precision={4} valueStyle={{ color: '#cf1322' }} />
                      </div>
                    </Col>
                  </Row>

                  <Table
                    columns={shortageColumns}
                    dataSource={shortageReport?.shortage_items || []}
                    rowKey={(record) => record.part_id || record.material_code || String(record.material_id)}
                    loading={shortageLoading}
                    pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 条缺料` }}
                    locale={{ emptyText: '当前库存满足该BOM需求' }}
                    scroll={{ x: 'max-content' }}
                  />
                </Space>
              ),
            },
            {
              key: 'tree',
              label: 'BOM树结构',
              children: (
                <Card title={<Space><BranchesOutlined />BOM树形结构</Space>}>
                  <Tree
                    showLine
                    defaultExpandAll
                    treeData={treeData}
                    titleRender={(node: any) => {
                      const item = node.item as BOMItem;
                      return (
                        <Space wrap>
                          <Text strong>{node.title}</Text>
                          <Tag color="blue">{levelLabels[item.level] || `第${item.level}层`}</Tag>
                          <Tag>{item.material_code || item.sub_bom_code || '-'}</Tag>
                          {item.material_id && (
                            isAdmin() && item.version_options?.length ? (
                              <Select
                                size="small"
                                value={item.part_version_id}
                                placeholder="无版本"
                                style={{ minWidth: 120 }}
                                onClick={(event) => event.stopPropagation()}
                                onChange={(value) => handleVersionChange(item.bom_id, item.id, value)}
                                options={item.version_options
                                  .filter((version) => version.status === 'active' || version.id === item.part_version_id)
                                  .map((version) => ({
                                    value: version.id,
                                    label: `${version.version_no}${version.is_current ? ' 当前' : ''}${version.status === 'obsolete' ? ' 废弃' : ''}`,
                                    disabled: version.status === 'obsolete',
                                  }))}
                              />
                            ) : (
                              <Tag color={item.version_no ? 'blue' : 'default'}>版本 {item.version_no || '无'}</Tag>
                            )
                          )}
                          {isCostExcludedStatus((item as any).sub_bom_status) && <Tag color="default">停用/作废不计价</Tag>}
                          {item.has_multiple_suppliers && <Tag color="gold">多供应商</Tag>}
                          {item.supplier_options?.length ? (
                            isAdmin() ? (
                              <Select
                                size="small"
                                value={item.selected_supplier_id}
                                style={{
                                  minWidth: 220,
                                  background: item.has_multiple_suppliers ? '#fffbe6' : undefined,
                                }}
                                onClick={(event) => event.stopPropagation()}
                                onChange={(value) => handleSupplierChange(item.bom_id, item.id, value)}
                                options={item.supplier_options.map((supplier) => ({
                                  value: supplier.id,
                                  label: `${supplier.supplier_name || supplier.supplier_id} ￥${Number(supplier.price || 0).toFixed(4)}${supplier.is_primary ? ' 主' : ''}`,
                                }))}
                              />
                            ) : (
                              <Tag>{item.selected_supplier_name || '已选供应商'}</Tag>
                            )
                          ) : item.material_id ? (
                            <Tag color="default">无供应商报价</Tag>
                          ) : null}
                          <Text type="secondary">用量:{item.quantity}{item.unit}</Text>
                          <Text type="secondary">损耗率:{Number(item.usage_rate || 1).toFixed(4)}</Text>
                          {item.substitute_group && <Text type="secondary">替代组:{item.substitute_group}/优先级:{item.substitute_priority || 1}</Text>}
                          {item.effective_date && <Text type="secondary">生效:{formatDate(item.effective_date)}</Text>}
                          <Text type="secondary">￥{Number(item.item_cost || 0).toFixed(2)}</Text>
                        </Space>
                      );
                    }}
                  />
                </Card>
              ),
            },
          ]}
        />
      </Card>
    </Space>
  );
};

export default BOMDetail;
