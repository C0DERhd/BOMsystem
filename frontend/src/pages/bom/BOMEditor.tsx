import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Button,
  Card,
  Checkbox,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Spin,
  Tag,
  Tree,
  Typography,
  message,
} from 'antd';
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  SaveOutlined,
} from '@ant-design/icons';

import api from '@/services/api';
import { BOM, BOMItem, MaterialSupplier, PaginatedResponse } from '@/types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { TextArea } = Input;

type ItemType = 'part' | 'sub_bom';

type PartNumber = {
  part_id: string;
  part_name?: string;
  category?: string;
  main_type?: string;
  sub_type?: string;
  unit?: string;
  standard_cost?: number;
  material_id?: number;
  supplier_options?: MaterialSupplier[];
  version_supplier_options?: Record<string, MaterialSupplier[]>;
  current_version_id?: number;
  versions?: {
    id: number;
    version_no: string;
    status: 'active' | 'obsolete';
    is_current: boolean;
  }[];
  supplier_count?: number;
  has_multiple_suppliers?: boolean;
};

type LocalBomItem = {
  client_id: string;
  part_id?: string;
  part_version_id?: number;
  version_no?: string;
  item_type: ItemType;
  material_id?: number;
  material_code?: string;
  material_name?: string;
  sub_bom_id?: number;
  sub_bom_code?: string;
  quantity: number;
  unit?: string;
  item_no?: string;
  is_key_material?: boolean;
  is_optional?: boolean;
  usage_rate?: number;
  selected_supplier_id?: number;
  selected_supplier_name?: string;
  selected_supplier_price?: number;
  supplier_options?: MaterialSupplier[];
  has_multiple_suppliers?: boolean;
  substitute_group?: string;
  substitute_priority?: number;
  process_step?: string;
  assembly_note?: string;
  effective_date?: string;
  expiry_date?: string;
  remark?: string;
  children?: LocalBomItem[];
};

const createClientId = () => `tmp-${Date.now()}-${Math.random().toString(16).slice(2)}`;
const levelLabels: Record<number, string> = { 1: '模块', 2: '子组件', 3: '零件' };
const maxItemLevel = 3;

const formatDateValue = (value?: any) => {
  if (!value) return undefined;
  if (typeof value?.toISOString === 'function') return value.toISOString();
  return value;
};

const parseDateValue = (value?: string) => (value ? dayjs(value) : undefined);

const getApiErrorMessage = (error: any) => (
  error?.response?.data?.message ||
  error?.message ||
  '请检查后端服务和数据库连接'
);

const markErrorHandled = (error: any) => {
  if (error && typeof error === 'object') {
    error.__bomEditorHandled = true;
  }
  return error;
};

const findItemLevel = (items: LocalBomItem[], clientId: string, level = 1): number | null => {
  for (const item of items) {
    if (item.client_id === clientId) return level;
    const childLevel = findItemLevel(item.children || [], clientId, level + 1);
    if (childLevel) return childLevel;
  }
  return null;
};

const buildLocalTree = (items: BOMItem[] = []): LocalBomItem[] => {
  const itemMap = new Map<number, LocalBomItem>();
  const childrenByParent = new Map<number | undefined, BOMItem[]>();

  items.forEach((item) => {
    itemMap.set(item.id, {
      client_id: String(item.id),
      item_type: item.sub_bom_id ? 'sub_bom' : 'part',
      part_id: item.material_id ? item.material_code : undefined,
      part_version_id: item.part_version_id,
      version_no: item.version_no,
      material_id: item.material_id,
      material_code: item.material_code,
      material_name: item.material_name,
      sub_bom_id: item.sub_bom_id,
      sub_bom_code: item.sub_bom_code,
      quantity: item.quantity,
      unit: item.unit,
      item_no: item.item_no,
      is_key_material: item.is_key_material,
      is_optional: item.is_optional,
      usage_rate: item.usage_rate || 1,
      selected_supplier_id: item.selected_supplier_id,
      selected_supplier_name: item.selected_supplier_name,
      selected_supplier_price: item.selected_supplier_price,
      supplier_options: item.supplier_options || [],
      has_multiple_suppliers: item.has_multiple_suppliers,
      substitute_group: item.substitute_group,
      substitute_priority: item.substitute_priority || 1,
      process_step: item.process_step,
      assembly_note: item.assembly_note,
      effective_date: item.effective_date,
      expiry_date: item.expiry_date,
      remark: item.remark,
      children: [],
    });

    const parentId = item.parent_item_id || undefined;
    const siblings = childrenByParent.get(parentId) || [];
    siblings.push(item);
    childrenByParent.set(parentId, siblings);
  });

  const build = (parentId?: number): LocalBomItem[] => {
    return (childrenByParent.get(parentId) || [])
      .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
      .map((item) => {
        const localItem = itemMap.get(item.id)!;
        localItem.children = build(item.id);
        return localItem;
      });
  };

  return build(undefined);
};

const mapItemsForSave = (items: LocalBomItem[]): any[] => {
  return items.map((item, index) => ({
    client_id: item.client_id,
    part_id: item.item_type === 'part' ? item.part_id : undefined,
    part_version_id: item.item_type === 'part' ? item.part_version_id : undefined,
    material_id: item.item_type === 'part' && !item.part_id ? item.material_id : undefined,
    sub_bom_id: item.item_type === 'sub_bom' ? item.sub_bom_id : undefined,
    item_no: item.item_no,
    quantity: item.quantity,
    unit: item.unit,
    is_key_material: !!item.is_key_material,
    is_optional: !!item.is_optional,
    usage_rate: item.usage_rate || 1,
    selected_supplier_id: item.selected_supplier_id,
    substitute_group: item.substitute_group,
    substitute_priority: item.substitute_priority || 1,
    process_step: item.process_step,
    assembly_note: item.assembly_note,
    effective_date: formatDateValue(item.effective_date),
    expiry_date: formatDateValue(item.expiry_date),
    remark: item.remark,
    sort_order: index + 1,
    children: mapItemsForSave(item.children || []),
  }));
};

const updateTreeItem = (
  items: LocalBomItem[],
  clientId: string,
  updater: (item: LocalBomItem) => LocalBomItem,
): LocalBomItem[] => {
  return items.map((item) => {
    if (item.client_id === clientId) return updater(item);
    return { ...item, children: updateTreeItem(item.children || [], clientId, updater) };
  });
};

const addTreeItem = (
  items: LocalBomItem[],
  parentClientId: string | null,
  newItem: LocalBomItem,
): LocalBomItem[] => {
  if (!parentClientId) return [...items, newItem];
  return updateTreeItem(items, parentClientId, (item) => ({
    ...item,
    children: [...(item.children || []), newItem],
  }));
};

const deleteTreeItem = (items: LocalBomItem[], clientId: string): LocalBomItem[] => {
  return items
    .filter((item) => item.client_id !== clientId)
    .map((item) => ({ ...item, children: deleteTreeItem(item.children || [], clientId) }));
};

const flattenTree = (items: LocalBomItem[]): LocalBomItem[] => {
  const result: LocalBomItem[] = [];
  items.forEach((item) => {
    result.push(item);
    result.push(...flattenTree(item.children || []));
  });
  return result;
};

const BOMEditor: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const [form] = Form.useForm();
  const [itemForm] = Form.useForm();
  const itemType = Form.useWatch('item_type', itemForm) as ItemType | undefined;
  const selectedPartId = Form.useWatch('part_id', itemForm) as string | undefined;
  const selectedVersionId = Form.useWatch('part_version_id', itemForm) as number | undefined;
  const selectedSupplierId = Form.useWatch('selected_supplier_id', itemForm) as number | undefined;

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [partNumbers, setPartNumbers] = useState<PartNumber[]>([]);
  const [availableBoms, setAvailableBoms] = useState<BOM[]>([]);
  const [treeItems, setTreeItems] = useState<LocalBomItem[]>([]);
  const [itemModalOpen, setItemModalOpen] = useState(false);
  const [editingClientId, setEditingClientId] = useState<string | null>(null);
  const [targetParentId, setTargetParentId] = useState<string | null>(null);
  const [partSearchLoading, setPartSearchLoading] = useState(false);
  const partSearchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const partSearchRequestId = useRef(0);

  const selectedPart = useMemo(
    () => partNumbers.find((item) => item.part_id === selectedPartId),
    [partNumbers, selectedPartId],
  );
  const selectedSupplierOptions = selectedPart
    ? (selectedVersionId
      ? (selectedPart.version_supplier_options?.[String(selectedVersionId)] || [])
      : (selectedPart.supplier_options || []))
    : [];
  const selectedSupplier = selectedSupplierOptions.find((item) => item.id === selectedSupplierId);

  const getDefaultVersionId = (part?: PartNumber) => {
    const activeVersions = (part?.versions || []).filter((item) => item.status === 'active');
    return part?.current_version_id || activeVersions.find((item) => item.is_current)?.id || activeVersions[0]?.id;
  };

  const getSupplierOptionsForVersion = (part?: PartNumber, versionId?: number) => {
    if (!part) return [];
    return versionId
      ? (part.version_supplier_options?.[String(versionId)] || [])
      : (part.supplier_options || []);
  };

  const getDefaultSupplierId = (part?: PartNumber, versionId?: number) => {
    const suppliers = getSupplierOptionsForVersion(part, versionId);
    return suppliers.find((item) => item.is_primary)?.id || suppliers[0]?.id;
  };

  const currentItemLevel = useMemo(() => {
    if (editingClientId) return findItemLevel(treeItems, editingClientId) || 1;
    const parentLevel = targetParentId ? findItemLevel(treeItems, targetParentId) || 0 : 0;
    return parentLevel + 1;
  }, [editingClientId, targetParentId, treeItems]);

  const itemTypeOptions = useMemo(() => {
    if (currentItemLevel >= maxItemLevel) {
      return [{ value: 'part', label: '零件号' }];
    }
    return [
      { value: 'sub_bom', label: currentItemLevel === 1 ? '模块BOM' : '子组件BOM' },
      { value: 'part', label: '零件号' },
    ];
  }, [currentItemLevel]);

  const loadPartNumbers = async (keyword = '') => {
    const requestId = ++partSearchRequestId.current;
    setPartSearchLoading(true);
    try {
      const response = await api.get('/visiray/part-numbers', {
        params: {
          page: 1,
          per_page: 30,
          include_suppliers: 1,
          ...(keyword.trim() ? { keyword: keyword.trim() } : {}),
        },
      });
      if (requestId === partSearchRequestId.current) {
        setPartNumbers((response.data.data as PaginatedResponse<PartNumber>).items || []);
      }
    } finally {
      if (requestId === partSearchRequestId.current) {
        setPartSearchLoading(false);
      }
    }
  };

  const handlePartSearch = (keyword: string) => {
    if (partSearchTimer.current) {
      clearTimeout(partSearchTimer.current);
    }
    partSearchTimer.current = setTimeout(() => {
      loadPartNumbers(keyword).catch((error: any) => {
        message.error(`搜索零件号失败：${getApiErrorMessage(error)}`);
      });
    }, 250);
  };

  const fetchOptions = async () => {
    try {
      await loadPartNumbers();
    } catch (error: any) {
      message.error(`加载零件号/报价数据失败：${getApiErrorMessage(error)}`);
      throw markErrorHandled(error);
    }

    try {
      const bomsResponse = await api.get('/bom', { params: { page: 1, per_page: 500 } });
      const boms = ((bomsResponse.data.data as PaginatedResponse<BOM>).items || [])
        .filter((bom) => String(bom.id) !== id && bom.status === 'active');
      setAvailableBoms(boms);
    } catch (error: any) {
      message.error(`加载可选子BOM列表失败：${getApiErrorMessage(error)}`);
      throw markErrorHandled(error);
    }
  };

  const fetchBom = async () => {
    if (!id) return;
    try {
      const response = await api.get(`/bom/${id}`);
      const bom = response.data.data as BOM;
      form.setFieldsValue({
        bom_code: bom.bom_code,
        product_name: bom.product_name,
        product_model: bom.product_model,
        product_spec: bom.product_spec,
        version: bom.version,
        status: bom.status,
        base_quantity: bom.base_quantity,
        unit: bom.unit,
        process_route: bom.process_route,
        lead_time: bom.lead_time,
        effective_date: parseDateValue(bom.effective_date),
        expiry_date: parseDateValue(bom.expiry_date),
        remark: bom.remark,
      });
      setTreeItems(buildLocalTree(bom.items || []));
    } catch (error: any) {
      message.error(`加载当前BOM详情失败：${getApiErrorMessage(error)}`);
      throw markErrorHandled(error);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        await fetchOptions();
        if (isEdit) {
          await fetchBom();
        } else {
          form.setFieldsValue({ version: '0001', status: 'draft', base_quantity: 1, unit: 'pcs' });
        }
      } catch (error: any) {
        if (!error?.__bomEditorHandled) {
          message.error(error?.response?.data?.message || '加载BOM编辑数据失败');
        }
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [id]);

  useEffect(() => () => {
    if (partSearchTimer.current) {
      clearTimeout(partSearchTimer.current);
    }
  }, []);

  const treeData = useMemo(() => {
    const build = (items: LocalBomItem[], level = 1): any[] => items.map((item) => ({
      key: item.client_id,
      item,
      level,
      title: item.material_name || item.sub_bom_code || '未命名项目',
      children: build(item.children || [], level + 1),
    }));
    return build(treeItems);
  }, [treeItems]);

  const openAddModal = (parentClientId: string | null = null) => {
    const parentLevel = parentClientId ? findItemLevel(treeItems, parentClientId) || 0 : 0;
    if (parentLevel >= maxItemLevel) {
      message.warning('零件层不能继续添加子节点');
      return;
    }
    setEditingClientId(null);
    setTargetParentId(parentClientId);
    itemForm.resetFields();
    itemForm.setFieldsValue({
      item_type: parentLevel + 1 >= maxItemLevel ? 'part' : 'sub_bom',
      quantity: 1,
      usage_rate: 1,
      substitute_priority: 1,
      is_key_material: false,
      is_optional: false,
      unit: 'pcs',
    });
    setItemModalOpen(true);
  };

  const openEditModal = (item: LocalBomItem) => {
    setEditingClientId(item.client_id);
    setTargetParentId(null);
    const part = partNumbers.find((partItem) => partItem.part_id === item.part_id || partItem.part_id === item.material_code);
    const supplierOptions = item.item_type === 'part'
      ? getSupplierOptionsForVersion(part, item.part_version_id)
      : [];
    itemForm.resetFields();
    itemForm.setFieldsValue({
      ...item,
      part_id: item.item_type === 'part' ? (part?.part_id || item.part_id || item.material_code) : undefined,
      selected_supplier_id: item.selected_supplier_id || getDefaultSupplierId(part, item.part_version_id),
      effective_date: parseDateValue(item.effective_date),
      expiry_date: parseDateValue(item.expiry_date),
    });
    if (item.item_type === 'part' && supplierOptions.length) {
      setTimeout(() => {
        itemForm.setFieldsValue({
          selected_supplier_id: itemForm.getFieldValue('selected_supplier_id') || getDefaultSupplierId(part, item.part_version_id),
        });
      }, 0);
    }
    setItemModalOpen(true);
  };

  const handleItemSubmit = async () => {
    const values = await itemForm.validateFields();
    if (currentItemLevel >= maxItemLevel && values.item_type === 'sub_bom') {
      message.warning('第三级是零件层，只能选择零件号');
      return;
    }
    const selectedBom = availableBoms.find((item) => item.id === values.sub_bom_id);
    const supplierOptions = selectedPart?.supplier_options || [];
    const versionSupplierOptions = getSupplierOptionsForVersion(selectedPart, values.part_version_id);
    const selectedVersion = selectedPart?.versions?.find((item) => item.id === values.part_version_id);
    const chosenSupplier = versionSupplierOptions.find((item) => item.id === values.selected_supplier_id);
    const nextItem: LocalBomItem = {
      client_id: editingClientId || createClientId(),
      item_type: values.item_type,
      part_id: values.item_type === 'part' ? values.part_id : undefined,
      part_version_id: values.item_type === 'part' ? values.part_version_id : undefined,
      version_no: values.item_type === 'part' ? selectedVersion?.version_no : undefined,
      material_id: values.item_type === 'part' && !values.part_id ? values.material_id : undefined,
      material_code: selectedPart?.part_id,
      material_name: selectedPart?.part_name || selectedPart?.sub_type || selectedPart?.part_id,
      sub_bom_id: values.item_type === 'sub_bom' ? values.sub_bom_id : undefined,
      sub_bom_code: selectedBom?.bom_code,
      quantity: values.quantity,
      unit: values.unit || selectedPart?.unit || selectedBom?.unit || 'pcs',
      item_no: values.item_no,
      is_key_material: values.is_key_material,
      is_optional: values.is_optional,
      usage_rate: values.usage_rate || 1,
      selected_supplier_id: values.item_type === 'part' ? values.selected_supplier_id : undefined,
      selected_supplier_name: chosenSupplier?.supplier_name,
      selected_supplier_price: chosenSupplier?.price,
      supplier_options: values.item_type === 'part' ? versionSupplierOptions : [],
      has_multiple_suppliers: versionSupplierOptions.length > 1,
      substitute_group: values.substitute_group,
      substitute_priority: values.substitute_priority || 1,
      process_step: values.process_step,
      assembly_note: values.assembly_note,
      effective_date: formatDateValue(values.effective_date),
      expiry_date: formatDateValue(values.expiry_date),
      remark: values.remark,
      children: editingClientId ? flattenTree(treeItems).find((item) => item.client_id === editingClientId)?.children || [] : [],
    };

    if (editingClientId) {
      setTreeItems((items) => updateTreeItem(items, editingClientId, () => nextItem));
    } else {
      setTreeItems((items) => addTreeItem(items, targetParentId, nextItem));
    }
    setItemModalOpen(false);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const payload = {
        ...values,
        status: values.status || 'draft',
        effective_date: formatDateValue(values.effective_date),
        expiry_date: formatDateValue(values.expiry_date),
        items: mapItemsForSave(treeItems),
      };

      if (isEdit) {
        await api.put(`/bom/${id}`, payload);
        message.success('BOM更新成功');
      } else {
        const response = await api.post('/bom', payload);
        message.success('BOM创建成功');
        const newBom = response.data.data as BOM;
        navigate(`/bom/${newBom.id}/edit`, { replace: true });
        return;
      }
      navigate(`/bom/${id}`);
    } catch (error: any) {
      if (error?.errorFields) return;
      message.error(error?.response?.data?.message || '保存BOM失败');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Spin />;

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Space style={{ justifyContent: 'space-between', width: '100%' }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(isEdit ? `/bom/${id}` : '/bom')}>返回</Button>
          <Title level={3} style={{ margin: 0 }}>{isEdit ? '编辑BOM' : '新建BOM'}</Title>
        </Space>
        <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving}>保存</Button>
      </Space>

      <Card title="基本信息">
        <Form form={form} layout="vertical">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(180px, 1fr))', gap: 16 }}>
            <Form.Item name="bom_code" label="BOM编码">
              <Input placeholder="留空自动生成" disabled={isEdit} />
            </Form.Item>
            <Form.Item name="product_name" label="产品名称" rules={[{ required: true, message: '请输入产品名称' }]}>
              <Input />
            </Form.Item>
            <Form.Item name="product_model" label="产品型号">
              <Input />
            </Form.Item>
            <Form.Item
              name="version"
              label="版本"
              rules={[
                { required: true, message: '请输入版本' },
                { pattern: /^\d{4}$/, message: '版本号必须是四位数字，例如 0001' },
              ]}
            >
              <Input maxLength={4} placeholder="例如 0001" />
            </Form.Item>
            <Form.Item name="status" label="状态">
              <Select options={[
                { value: 'draft', label: '草稿' },
                { value: 'active', label: '生效' },
                { value: 'inactive', label: '停用' },
                { value: 'obsolete', label: '作废' },
              ]} />
            </Form.Item>
            <Form.Item name="base_quantity" label="基础数量">
              <InputNumber min={0.0001} precision={4} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="unit" label="单位">
              <Input />
            </Form.Item>
            <Form.Item name="lead_time" label="生产周期(天)">
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="effective_date" label="生效日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="expiry_date" label="失效日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </div>
          <Form.Item name="product_spec" label="产品规格">
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item name="process_route" label="工艺路线">
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <TextArea rows={2} />
          </Form.Item>
        </Form>
      </Card>

      <Card
        title="四级BOM结构（整机 -> 模块 -> 子组件 -> 零件）"
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => openAddModal(null)}>添加模块</Button>}
      >
        {treeData.length ? (
          <Tree
            showLine
            defaultExpandAll
            treeData={treeData}
            titleRender={(node: any) => {
              const item = node.item as LocalBomItem;
              return (
                <Space wrap>
                  <Text strong>{node.title}</Text>
                  <Text type="secondary">{levelLabels[node.level] || `第${node.level}层`}</Text>
                  <Text type="secondary">{item.material_code || item.sub_bom_code || '-'}</Text>
                  {item.version_no && <Tag color="blue">版本 {item.version_no}</Tag>}
                  {item.has_multiple_suppliers && <Tag color="gold">多供应商</Tag>}
                  {item.selected_supplier_name && <Text type="secondary">供应商:{item.selected_supplier_name}</Text>}
                  {item.selected_supplier_price != null && <Text type="secondary">单价:￥{Number(item.selected_supplier_price || 0).toFixed(4)}</Text>}
                  <Text>{item.quantity}{item.unit}</Text>
                  <Text type="secondary">损耗率:{Number(item.usage_rate || 1).toFixed(4)}</Text>
                  {item.substitute_group && <Text type="secondary">替代组:{item.substitute_group}/优先级:{item.substitute_priority || 1}</Text>}
                  {item.is_key_material && <Text type="danger">关键</Text>}
                  {item.is_optional && <Text type="secondary">可选</Text>}
                  {node.level < maxItemLevel && <Button size="small" type="link" icon={<PlusOutlined />} onClick={(event) => { event.stopPropagation(); openAddModal(item.client_id); }}>子节点</Button>}
                  <Button size="small" type="link" icon={<EditOutlined />} onClick={(event) => { event.stopPropagation(); openEditModal(item); }}>编辑</Button>
                  <Button size="small" type="link" danger icon={<DeleteOutlined />} onClick={(event) => { event.stopPropagation(); setTreeItems((items) => deleteTreeItem(items, item.client_id)); }}>删除</Button>
                </Space>
              );
            }}
          />
        ) : (
          <Text type="secondary">还没有BOM明细，先添加模块。</Text>
        )}
      </Card>

      <Modal
        title={editingClientId ? `编辑${levelLabels[currentItemLevel] || 'BOM节点'}` : `添加${levelLabels[currentItemLevel] || 'BOM节点'}`}
        open={itemModalOpen}
        onOk={handleItemSubmit}
        onCancel={() => setItemModalOpen(false)}
        okText="确定"
        cancelText="取消"
        width={720}
      >
        <Form form={itemForm} layout="vertical">
          <Form.Item name="item_type" label="节点类型" rules={[{ required: true, message: '请选择节点类型' }]}>
            <Select options={itemTypeOptions} />
          </Form.Item>

          {itemType !== 'sub_bom' ? (
            <Form.Item name="part_id" label="零件号" rules={[{ required: true, message: '请选择零件号' }]}>
              <Select
                showSearch
                placeholder="选择零件号"
                filterOption={false}
                loading={partSearchLoading}
                onSearch={handlePartSearch}
                onChange={(partId) => {
                  const part = partNumbers.find((item) => item.part_id === partId);
                  const versionId = getDefaultVersionId(part);
                  itemForm.setFieldsValue({
                    part_version_id: versionId,
                    selected_supplier_id: getDefaultSupplierId(part, versionId),
                    unit: part?.unit || itemForm.getFieldValue('unit') || 'pcs',
                  });
                }}
                options={partNumbers.map((item) => ({
                  value: item.part_id,
                  label: `${item.part_id} - ${item.part_name || item.sub_type || item.main_type || ''}${item.supplier_count ? ` - ${item.supplier_count}个供应商` : ''}`,
                }))}
              />
            </Form.Item>
          ) : (
            <Form.Item name="sub_bom_id" label="子BOM" rules={[{ required: true, message: '请选择子BOM' }]}>
              <Select
                showSearch
                placeholder="选择子BOM"
                optionFilterProp="label"
                options={availableBoms.map((item) => ({
                  value: item.id,
                  label: `${item.bom_code} - ${item.product_name}`,
                }))}
              />
            </Form.Item>
          )}

          {itemType !== 'sub_bom' && selectedPart && (
            <Form.Item name="part_version_id" label="版本号">
              <Select
                placeholder={(selectedPart.versions || []).length ? '选择版本号' : '该零件暂无版本'}
                disabled={!(selectedPart.versions || []).length}
                onChange={(versionId) => {
                  itemForm.setFieldsValue({
                    selected_supplier_id: getDefaultSupplierId(selectedPart, versionId),
                  });
                }}
                options={(selectedPart.versions || []).filter((item) => item.status === 'active').map((item) => ({
                  value: item.id,
                  label: `${item.version_no}${item.is_current ? ' 当前' : ''}`,
                }))}
              />
            </Form.Item>
          )}

          {itemType !== 'sub_bom' && (
            <Form.Item
              name="selected_supplier_id"
              label="供应商价格"
              rules={selectedSupplierOptions.length ? [{ required: true, message: '请选择供应商价格' }] : []}
            >
              <Select
                placeholder={selectedSupplierOptions.length ? '请选择供应商价格' : '该零件暂无供应商报价'}
                disabled={!selectedSupplierOptions.length}
                options={selectedSupplierOptions.map((item) => ({
                  value: item.id,
                  label: `${item.supplier_name || item.supplier_id} - ￥${Number(item.price || 0).toFixed(4)}${item.is_primary ? ' - 主供应商' : ''}`,
                }))}
              />
            </Form.Item>
          )}

          {itemType !== 'sub_bom' && selectedSupplier && (
            <Text type="secondary">
              当前单价：￥{Number(selectedSupplier.price || 0).toFixed(4)}
            </Text>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(160px, 1fr))', gap: 16 }}>
            <Form.Item name="item_no" label="项目号">
              <Input />
            </Form.Item>
            <Form.Item name="quantity" label="数量" rules={[{ required: true, message: '请输入数量' }]}>
              <InputNumber min={0.0001} precision={4} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="unit" label="单位">
              <Input placeholder="默认 pcs" />
            </Form.Item>
            <Form.Item name="usage_rate" label="损耗率">
              <InputNumber min={0} max={99} precision={4} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="substitute_group" label="替代组">
              <Input placeholder="同一替代组内按优先级替代" />
            </Form.Item>
            <Form.Item name="substitute_priority" label="替代优先级">
              <InputNumber min={1} precision={0} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="effective_date" label="生效日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="expiry_date" label="失效日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="is_key_material" valuePropName="checked">
              <Checkbox>关键物料</Checkbox>
            </Form.Item>
            <Form.Item name="is_optional" valuePropName="checked">
              <Checkbox>可选物料</Checkbox>
            </Form.Item>
          </div>

          <Form.Item name="process_step" label="工序">
            <Input />
          </Form.Item>
          <Form.Item name="assembly_note" label="装配说明">
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
};

export default BOMEditor;



