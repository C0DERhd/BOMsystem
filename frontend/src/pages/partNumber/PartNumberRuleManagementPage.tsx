import React, { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd';
import {
  CheckCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import api from '@/services/api';

const { Title, Text } = Typography;

type PartNumberRule = {
  id: number;
  rule_name: string;
  prefix: string;
  config: any;
  is_active: boolean;
  remark?: string;
  updated_at?: string;
  created_at?: string;
};

const sourceOptions = [
  { value: 'part_category_code', label: '自动填写：一级大类编码' },
  { value: 'main_category_code', label: '自动填写：二级类别编码' },
  { value: 'sub_category_index', label: '自动填写：三级材质/表面处理编码' },
  { value: 'sequence', label: '自动填写：四级流水号' },
  { value: 'static', label: '手工固定值' },
];

const subCategoryLabelMap: Record<string, string> = {
  light_source: '光源器件类',
  light_transmission: '光传输器件类',
  lens_prism: '光学透镜/棱镜类',
  optical_filter: '光学滤光片类',
  optical_sensor: '光学传感器类',
  light_modulator: '光调制器件类',
  display_imaging: '显示与成像类',
  optical_other: '其他（光学）',
  aluminum_profile: '铝型材类',
  transmission: '传动类',
  fasteners: '紧固件类',
  spring: '弹簧类',
  net_filter: '网及筛滤器类',
  mechanical_other: '其他（机械外购）',
  iron_steel: '铁、钢、合金钢',
  copper_aluminum_titanium: '铜、铝、钛及其合金',
  other_metal: '其他金属',
  plastic: '塑料类',
  rubber: '橡胶类',
  glass_ceramic: '玻璃、陶瓷等',
  passive: '被动元件类',
  semiconductor: '半导体器件类',
  electromechanical: '机电与连接类',
  power: '电源与储能类',
  sensor: '传感器类',
  electrical_other: '其他（电气外购）',
  custom_power: '电源与储能类（定制）',
  custom_sensor: '传感器类（定制）',
  wire_harness: '线束类',
  drive_control: '驱控类',
  custom_electrical_other: '其他（电气定制）',
  system_software: '系统与基础软件',
  office_software: '通用办公软件',
  security_software: '安全与管理软件',
  engineering_software: '工程与研发通用软件',
  development_tools: '开发工具',
  software_other: '其他（外购软件）',
  custom_platform: '定制平台类',
  custom_development_tools: '定制研发工具',
  custom_information_visualization: '定制信息化与可视化',
  custom_software_other: '其他（定制软件）',
  inorganic: '基础无机化学品',
  organic: '有机化学品',
  reagent: '试剂与实验室化学品',
  functional: '功能化学品',
  material_chemical: '材料化学品',
  hazardous: '危险化学品',
  chemical_other: '其他（化学外购）',
  custom_formulation: '定制配方化学品',
  custom_polymer: '定制高分子材料',
  custom_coating: '定制涂层与胶粘剂',
  custom_functional: '定制功能化学品',
  custom_material: '定制材料化学品',
  custom_environmental: '定制环境与工业化学品',
  custom_chemical_other: '其他（化学定制）',
  material_aluminum: '铝',
  material_plastic: '塑料',
  material_steel: '钢',
  material_glass: '玻璃',
  material_other: '其它',
  surface_sandblast: '喷砂',
  surface_anodized: '阳极氧化',
  surface_spray: '喷涂',
  surface_sandblast_anodized: '喷砂+阳极氧化',
};
const subCategoryKeyToLabel = (key: string) => subCategoryLabelMap[key] || key;
const subCategoryLabelToKey = Object.fromEntries(
  Object.entries(subCategoryLabelMap).map(([key, label]) => [label, key])
);

const mainCategoryKeyToLabel = (config: any, key: string) =>
  config?.main_categories?.[key]?.name || key;

const partCategoryKeyToLabel = (config: any, key: string) =>
  config?.part_categories?.[key]?.name || key;

const subCategoryKeyToConfigLabel = (config: any, key: string) =>
  config?.sub_categories?.[key]?.name || subCategoryKeyToLabel(key);

const getMainCategoryOptions = (config: any) =>
  Object.entries(config?.main_categories || {}).map(([key, item]: [string, any]) => ({
    value: key,
    label: `${item?.name || key}${item?.code ? `（${item.code}）` : ''}`,
  }));

const getPartCategoryOptions = (config: any) =>
  Object.entries(config?.part_categories || {}).map(([key, item]: [string, any]) => ({
    value: key,
    label: `${item?.name || key}${item?.code ? `（${item.code}）` : ''}`,
  }));

const scopeOptions = [
  { value: 'all', label: '通用' },
  { value: 'custom', label: '定制件' },
  { value: 'purchased', label: '外购件' },
];

const splitLines = (value: string) =>
  String(value || '')
    .split(/[\n,，]+/)
    .map((item) => item.trim())
    .filter(Boolean);

const ordersToForm = (config: any) =>
  Object.entries(config?.sub_category_orders || {}).map(([orderKey, values]) => ({
    main_category_key: orderKey.includes('.') ? orderKey.split('.')[0] : orderKey,
    scope: orderKey.includes('.') ? orderKey.split('.')[1] : 'all',
    values_text: Array.isArray(values)
      ? values.map((item) => subCategoryKeyToConfigLabel(config, item)).join('\n')
      : '',
  }));

const listToEntries = (value: Record<string, any> = {}) =>
  Object.entries(value).map(([key, item]) => ({
    category_key: key,
    ...(item as Record<string, any>),
  }));

const normalizeRuleConfig = (config: any = {}, fallback: any = {}) => {
  const sourcePartCategories = config.part_categories && Object.keys(config.part_categories).length
    ? config.part_categories
    : fallback.part_categories || {};
  const sourceMainCategories = config.main_categories && Object.keys(config.main_categories).length
    ? config.main_categories
    : fallback.main_categories || {};
  const sourceSubCategories = config.sub_categories && Object.keys(config.sub_categories).length
    ? config.sub_categories
    : fallback.sub_categories || {};
  const sourceSubCategoryOrders = config.sub_category_orders && Object.keys(config.sub_category_orders).length
    ? config.sub_category_orders
    : fallback.sub_category_orders || {};

  return {
    rule_standard: config.rule_standard ?? fallback.rule_standard,
    code_length: config.code_length ?? fallback.code_length ?? 12,
    version: config.version ?? fallback.version ?? '0',
    sequence_start: config.sequence_start ?? fallback.sequence_start ?? 1,
    sequence_scope: config.sequence_scope ?? fallback.sequence_scope ?? 'part_category_code',
    segments: Array.isArray(config.segments) && config.segments.length
      ? config.segments.map((segment: any) => ({ ...segment }))
      : Array.isArray(fallback.segments)
        ? fallback.segments.map((segment: any) => ({ ...segment }))
        : [],
    // 编辑已有规则时，必须以规则自身的列表为准，否则删除一项后又会被默认配置补回来。
    part_categories: sourcePartCategories,
    main_categories: sourceMainCategories,
    sub_categories: sourceSubCategories,
    sub_category_orders: sourceSubCategoryOrders,
  };
};

const configToFormValues = (config: any = {}, rule?: PartNumberRule | null, fallbackConfig: any = {}) => {
  const normalized = normalizeRuleConfig(config, fallbackConfig);
  return {
    rule_name: rule?.rule_name || '新零件号规则',
    prefix: rule?.prefix || '',
    code_length: normalized.code_length,
    version: normalized.version,
    sequence_start: normalized.sequence_start,
    remark: rule?.remark || '',
    segments: normalized.segments,
    part_categories: listToEntries(normalized.part_categories),
    main_categories: listToEntries(normalized.main_categories),
    sub_categories: listToEntries(normalized.sub_categories),
    sub_category_orders: ordersToForm(normalized),
  };
};

const formValuesToConfig = (values: any, previousConfig: any = {}) => {
  const part_categories: Record<string, any> = {};
  (values.part_categories || []).forEach((item: any) => {
    if (!item?.category_key) return;
    part_categories[item.category_key] = {
      name: item.name || '',
      code: String(item.code || ''),
      identifier: item.identifier != null ? String(item.identifier || '') : undefined,
      description: item.description || '',
    };
  });

  const main_categories: Record<string, any> = {};
  (values.main_categories || []).forEach((item: any) => {
    if (!item?.category_key) return;
    main_categories[item.category_key] = {
      name: item.name || '',
      code: String(item.code || ''),
      parent_key: item.parent_key || '',
      description: item.description || '',
    };
  });

  const sub_categories: Record<string, any> = {};
  (values.sub_categories || []).forEach((item: any) => {
    if (!item?.category_key) return;
    sub_categories[item.category_key] = {
      name: item.name || '',
      code: String(item.code || ''),
      group: item.group || '',
    };
  });
  const configuredSubCategoryLabelToKey = Object.fromEntries(
    Object.entries(sub_categories).map(([key, item]: [string, any]) => [item.name, key])
  );
  const previousSubCategories = previousConfig?.sub_categories || {};
  const previousSubCategoryLabelToKey = Object.fromEntries(
    Object.entries(previousSubCategories).map(([key, item]: [string, any]) => [item.name, key])
  );
  const currentSubCategoryKeyByCode = Object.fromEntries(
    Object.entries(sub_categories)
      .filter(([, item]: [string, any]) => item?.code != null)
      .map(([key, item]: [string, any]) => [String(item.code).padStart(2, '0'), key])
  );

  const sub_category_orders: Record<string, string[]> = {};
  (values.sub_category_orders || []).forEach((item: any) => {
    if (!item?.main_category_key) return;
    const orderKey = item.main_category_key;
    sub_category_orders[orderKey] = splitLines(item.values_text)
      .map((line) => {
        const currentKey = configuredSubCategoryLabelToKey[line] || subCategoryLabelToKey[line];
        if (currentKey && sub_categories[currentKey]) return currentKey;

        // 三级编码改名或更换系统标识时，若仍使用原数字编码，自动迁移适用项引用。
        const previousKey = previousSubCategoryLabelToKey[line] || line;
        const previousCode = previousSubCategories[previousKey]?.code;
        if (previousCode != null) {
          return currentSubCategoryKeyByCode[String(previousCode).padStart(2, '0')] || '';
        }
        return '';
      })
      .filter(Boolean);
  });

  return {
    rule_standard: 'vsr_final_20260807',
    code_length: Number(values.code_length || 0),
    version: String(values.version ?? '0'),
    sequence_start: Number(values.sequence_start || 1),
    sequence_scope: 'part_category_code',
    segments: (values.segments || []).map((segment: any) => ({
      key: segment.key,
      name: segment.name,
      length: Number(segment.length || 0),
      source: segment.source,
      value: segment.source === 'static' ? String(segment.value ?? '') : undefined,
      description: segment.description || '',
    })),
    part_categories,
    main_categories,
    sub_categories,
    sub_category_orders,
  };
};

const PartNumberRuleManagementPage: React.FC = () => {
  const [form] = Form.useForm();
  const [rules, setRules] = useState<PartNumberRule[]>([]);
  const [defaultConfig, setDefaultConfig] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<PartNumberRule | null>(null);

  const segments = Form.useWatch('segments', form) || [];
  const codeLength = Form.useWatch('code_length', form) || 0;
  const segmentTotal = useMemo(
    () => segments.reduce((sum: number, item: any) => sum + Number(item?.length || 0), 0),
    [segments]
  );

  const activeRule = useMemo(() => rules.find((item) => item.is_active), [rules]);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const [ruleRes, defaultRes] = await Promise.all([
        api.get('/visiray/part-number-rules'),
        api.get('/visiray/part-number-rules/default-config'),
      ]);
      if (ruleRes.data.success) setRules(ruleRes.data.data || []);
      if (defaultRes.data.success) setDefaultConfig(defaultRes.data.data);
    } catch (error: any) {
      message.error(error?.response?.data?.message || error?.message || '获取零件号规则失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const resetAndLoadForm = (config: any, rule?: PartNumberRule | null) => {
    form.resetFields();
    form.setFieldsValue(configToFormValues(config, rule, defaultConfig || {}));
  };

  const openCreate = () => {
    setEditingRule(null);
    resetAndLoadForm(defaultConfig || {});
    setModalOpen(true);
  };

  const openEdit = (rule: PartNumberRule) => {
    setEditingRule(rule);
    resetAndLoadForm(rule.config || {}, rule);
    setModalOpen(true);
  };

  const applyDefaultConfig = () => {
    resetAndLoadForm(defaultConfig || {}, editingRule);
  };

  const validateRule = (values: any) => {
    const total = (values.segments || []).reduce((sum: number, item: any) => sum + Number(item?.length || 0), 0);
    if (total !== Number(values.code_length || 0)) {
      throw new Error(`编码段长度合计为 ${total}，必须等于编码总长度 ${values.code_length}`);
    }
    if (!(values.segments || []).some((item: any) => item.source === 'sequence')) {
      throw new Error('编码段里必须保留一个流水号来源');
    }
  };

  const saveRule = async () => {
    try {
      // validateFields 的返回值可能只包含当前已注册的页签字段；
      // getFieldsValue(true) 才能读取 Form.List 中所有已保留的配置。
      await form.validateFields();
      const values = form.getFieldsValue(true);
      validateRule(values);
      const payload = {
        rule_name: values.rule_name,
        prefix: values.prefix || '',
        remark: values.remark || '',
        config: formValuesToConfig(values, editingRule?.config || {}),
      };
      setSaving(true);
      if (editingRule) {
        await api.put(`/visiray/part-number-rules/${editingRule.id}`, payload);
        message.success('零件号规则已更新');
      } else {
        await api.post('/visiray/part-number-rules', payload);
        message.success('零件号规则已创建');
      }
      setModalOpen(false);
      await fetchRules();
    } catch (error: any) {
      if (error?.errorFields) return;
      message.error(error?.response?.data?.message || error?.message || '保存零件号规则失败');
    } finally {
      setSaving(false);
    }
  };

  const activateRule = async (rule: PartNumberRule) => {
    try {
      await api.post(`/visiray/part-number-rules/${rule.id}/activate`);
      message.success('零件号规则已启用');
      fetchRules();
    } catch (error: any) {
      message.error(error?.response?.data?.message || error?.message || '启用零件号规则失败');
    }
  };

  const deleteRule = async (rule: PartNumberRule) => {
    try {
      await api.delete(`/visiray/part-number-rules/${rule.id}`);
      message.success('零件号规则已删除');
      fetchRules();
    } catch (error: any) {
      message.error(error?.response?.data?.message || error?.message || '删除零件号规则失败');
    }
  };

  const columns = [
    {
      title: '规则名称',
      dataIndex: 'rule_name',
      key: 'rule_name',
      render: (text: string, record: PartNumberRule) => (
        <Space direction="vertical" size={0}>
          <Space>
            <Text strong>{text}</Text>
            {record.is_active ? <Tag color="green">当前启用</Tag> : null}
          </Space>
          <Text type="secondary">{record.remark || '-'}</Text>
        </Space>
      ),
    },
    {
      title: '前缀',
      dataIndex: 'prefix',
      key: 'prefix',
      width: 100,
      render: (text: string) => text || '无',
    },
    {
      title: '总长度',
      key: 'code_length',
      width: 90,
      render: (_: any, record: PartNumberRule) => record.config?.code_length || '-',
    },
    {
      title: '编码段',
      key: 'segments',
      render: (_: any, record: PartNumberRule) => (
        <Space wrap>
          {(record.config?.segments || []).map((segment: any) => (
            <Tag key={segment.key}>{segment.name || segment.key}:{segment.length}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (text: string) => (text ? new Date(text).toLocaleString('zh-CN', { hour12: false }) : '-'),
    },
    {
      title: '操作',
      key: 'action',
      width: 220,
      render: (_: any, record: PartNumberRule) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(record)}>编辑</Button>
          <Button type="link" icon={<CheckCircleOutlined />} disabled={record.is_active} onClick={() => activateRule(record)}>启用</Button>
          <Popconfirm
            title="确认删除该规则？"
            okText="删除"
            cancelText="取消"
            disabled={record.is_active}
            onConfirm={() => deleteRule(record)}
          >
            <Button type="link" danger icon={<DeleteOutlined />} disabled={record.is_active}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];
  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={3} style={{ margin: 0 }}>零件号规则管理</Title>
          <Text type="secondary">管理员通过表单维护 VSR + 12位数字编码规则，不需要直接编辑 JSON。</Text>
        </Col>
        <Col>
          <Space>
            <Button icon={<ReloadOutlined />} onClick={fetchRules}>刷新</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建规则</Button>
          </Space>
        </Col>
      </Row>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Text type="secondary">当前启用规则</Text>
            <div><Text strong>{activeRule?.rule_name || '-'}</Text></div>
          </Col>
          <Col span={8}>
            <Text type="secondary">公司缩写</Text>
            <div><Text strong>{activeRule?.prefix || '无'}</Text></div>
          </Col>
          <Col span={8}>
            <Text type="secondary">编码总长度</Text>
            <div><Text strong>{activeRule?.config?.code_length || '-'}</Text></div>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table rowKey="id" columns={columns} dataSource={rules} loading={loading} pagination={false} />
      </Card>

      <Modal
        title={editingRule ? '编辑零件号规则' : '新建零件号规则'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={saveRule}
        confirmLoading={saving}
        width={1100}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="rule_name" label="规则名称" rules={[{ required: true, message: '请输入规则名称' }]}>
                <Input placeholder="例如：12位物料编码规则" />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item name="prefix" label="公司缩写">
                <Input placeholder="VSR" />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item name="code_length" label="编码总长度" rules={[{ required: true, message: '请输入编码总长度' }]}>
                <InputNumber min={1} max={50} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item name="sequence_start" label="流水起始值">
                <InputNumber min={0} max={9999} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item label="校验">
                <Tag color={segmentTotal === codeLength ? 'green' : 'red'}>
                  段合计 {segmentTotal} / 总长 {codeLength || 0}
                </Tag>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="remark" label="备注">
            <Input placeholder="可填写规则用途或变更说明" />
          </Form.Item>

          <Tabs
            destroyInactiveTabPane={false}
            items={[
              {
                key: 'segments',
                label: '编码段',
                children: (
                  <Form.List name="segments">
                    {(fields, { add, remove }) => (
                      <Space direction="vertical" style={{ width: '100%' }} size={12}>
                        {fields.map((field) => (
                          <Card key={field.key} size="small">
                            <Row gutter={12}>
                              <Col span={4}>
                                <Form.Item name={[field.name, 'key']} label="字段标识" rules={[{ required: true }]}>
                                  <Input placeholder="sequence" />
                                </Form.Item>
                              </Col>
                              <Col span={4}>
                                <Form.Item name={[field.name, 'name']} label="显示名称" rules={[{ required: true }]}>
                                  <Input placeholder="流水号" />
                                </Form.Item>
                              </Col>
                              <Col span={3}>
                                <Form.Item name={[field.name, 'length']} label="位数" rules={[{ required: true }]}>
                                  <InputNumber min={1} max={20} style={{ width: '100%' }} />
                                </Form.Item>
                              </Col>
                              <Col span={5}>
                                <Form.Item name={[field.name, 'source']} label="编码来源" rules={[{ required: true }]}>
                                  <Select options={sourceOptions} />
                                </Form.Item>
                              </Col>
                              <Col span={4}>
                                <Form.Item name={[field.name, 'value']} label="固定值">
                                  <Input placeholder="仅固定值时使用" />
                                </Form.Item>
                              </Col>
                              <Col span={4}>
                                <Form.Item label="操作">
                                  <Button danger onClick={() => remove(field.name)}>删除</Button>
                                </Form.Item>
                              </Col>
                              <Col span={24}>
                                <Form.Item name={[field.name, 'description']} label="说明">
                                  <Input placeholder="给管理员看的说明" />
                                </Form.Item>
                              </Col>
                            </Row>
                          </Card>
                        ))}
                        <Button type="dashed" block icon={<PlusOutlined />} onClick={() => add({ key: '', name: '', length: 1, source: 'static', value: '', description: '' })}>
                          新增
                        </Button>
                      </Space>
                    )}
                  </Form.List>
                ),
              },
              {
                key: 'part_categories',
                label: '一级大类',
                children: (
                  <Form.List name="part_categories">
                    {(fields, { add, remove }) => (
                      <Space direction="vertical" style={{ width: '100%' }} size={12}>
                        {fields.map((field) => (
                          <Card key={field.key} size="small">
                            <Row gutter={12}>
                              <Col span={6}>
                                <Form.Item name={[field.name, 'category_key']} label="系统标识" rules={[{ required: true }]}>
                                  <Input placeholder="processed" />
                                </Form.Item>
                              </Col>
                              <Col span={6}>
                                <Form.Item name={[field.name, 'name']} label="名称" rules={[{ required: true }]}>
                                  <Input placeholder="定制件" />
                                </Form.Item>
                              </Col>
                              <Col span={6}>
                                <Form.Item name={[field.name, 'code']} label="一级编码" rules={[{ required: true }]}>
                                  <Input placeholder="10" />
                                </Form.Item>
                              </Col>
                              <Col span={6}>
                                <Form.Item name={[field.name, 'description']} label="说明">
                                  <Input placeholder="需要加工的零部件" />
                                </Form.Item>
                              </Col>
                              <Col span={24}>
                                <Button danger onClick={() => remove(field.name)}>删除</Button>
                              </Col>
                            </Row>
                          </Card>
                        ))}
                        <Button type="dashed" block icon={<PlusOutlined />} onClick={() => add({ category_key: '', name: '', code: '', description: '' })}>
                          新增
                        </Button>
                      </Space>
                    )}
                  </Form.List>
                ),
              },
              {
                key: 'main_categories',
                label: '二级类别',
                children: (
                  <Form.List name="main_categories">
                    {(fields, { add, remove }) => (
                      <Space direction="vertical" style={{ width: '100%' }} size={12}>
                        {fields.map((field) => (
                          <Card key={field.key} size="small">
                            <Row gutter={12}>
                              <Col span={5}>
                                <Form.Item name={[field.name, 'category_key']} label="系统标识" rules={[{ required: true }]}>
                                  <Input placeholder="custom_part" />
                                </Form.Item>
                              </Col>
                              <Col span={5}>
                                <Form.Item name={[field.name, 'parent_key']} label="所属一级大类" rules={[{ required: true }]}>
                                  <Select options={getPartCategoryOptions(normalizeRuleConfig(editingRule?.config || {}, defaultConfig || {}))} />
                                </Form.Item>
                              </Col>
                              <Col span={5}>
                                <Form.Item name={[field.name, 'name']} label="名称" rules={[{ required: true }]}>
                                  <Input placeholder="零件" />
                                </Form.Item>
                              </Col>
                              <Col span={5}>
                                <Form.Item name={[field.name, 'code']} label="二级编码" rules={[{ required: true }]}>
                                  <Input placeholder="2100" />
                                </Form.Item>
                              </Col>
                              <Col span={4}>
                                <Form.Item label="操作">
                                  <Button danger onClick={() => remove(field.name)}>删除</Button>
                                </Form.Item>
                              </Col>
                            </Row>
                          </Card>
                        ))}
                        <Button type="dashed" block icon={<PlusOutlined />} onClick={() => add({ category_key: '', parent_key: '', name: '', code: '' })}>
                          新增
                        </Button>
                      </Space>
                    )}
                  </Form.List>
                ),
              },
              {
                key: 'sub_categories',
                label: '三级编码',
                children: (
                  <Form.List name="sub_categories">
                    {(fields, { add, remove }) => (
                      <Space direction="vertical" style={{ width: '100%' }} size={12}>
                        {fields.map((field) => (
                          <Card key={field.key} size="small">
                            <Row gutter={12}>
                              <Col span={6}>
                                <Form.Item name={[field.name, 'category_key']} label="系统标识" rules={[{ required: true }]}>
                                  <Input placeholder="material_aluminum" />
                                </Form.Item>
                              </Col>
                              <Col span={6}>
                                <Form.Item name={[field.name, 'name']} label="名称" rules={[{ required: true }]}>
                                  <Input placeholder="铝" />
                                </Form.Item>
                              </Col>
                              <Col span={5}>
                                <Form.Item name={[field.name, 'code']} label="三级编码" rules={[{ required: true }]}>
                                  <Input placeholder="10" />
                                </Form.Item>
                              </Col>
                              <Col span={5}>
                                <Form.Item name={[field.name, 'group']} label="分组">
                                  <Select options={[
                                    { value: '材质', label: '材质' },
                                    { value: '表面处理', label: '表面处理' },
                                  ]} />
                                </Form.Item>
                              </Col>
                              <Col span={2}>
                                <Form.Item label="操作">
                                  <Button danger onClick={() => remove(field.name)}>删除</Button>
                                </Form.Item>
                              </Col>
                            </Row>
                          </Card>
                        ))}
                        <Button type="dashed" block icon={<PlusOutlined />} onClick={() => add({ category_key: '', name: '', code: '', group: '材质' })}>
                          新增
                        </Button>
                      </Space>
                    )}
                  </Form.List>
                ),
              },
              {
                key: 'sub_category_orders',
                label: '三级适用项',
                children: (
                  <Form.List name="sub_category_orders">
                    {(fields, { add, remove }) => (
                      <Space direction="vertical" style={{ width: '100%' }} size={12}>
                        {fields.map((field) => (
                          <Card key={field.key} size="small">
                            <Row gutter={12}>
                              <Col span={8}>
                                <Form.Item name={[field.name, 'main_category_key']} label="适用二级类别" rules={[{ required: true }]}>
                                  <Select options={getMainCategoryOptions(normalizeRuleConfig(editingRule?.config || {}, defaultConfig || {}))} placeholder="请选择二级类别" />
                                </Form.Item>
                              </Col>
                              <Col span={12}>
                                <Form.Item name={[field.name, 'values_text']} label="可选三级编码（中文，一行一个）">
                                  <Input.TextArea rows={4} placeholder={"例如：\n铝\n塑料\n钢\n喷砂\n阳极氧化"} />
                                </Form.Item>
                              </Col>
                              <Col span={4}>
                                <Form.Item label="操作">
                                  <Button danger onClick={() => remove(field.name)}>删除</Button>
                                </Form.Item>
                              </Col>
                            </Row>
                          </Card>
                        ))}
                        <Button type="dashed" block icon={<PlusOutlined />} onClick={() => add({ main_category_key: '', values_text: '' })}>
                          新增
                        </Button>
                      </Space>
                    )}
                  </Form.List>
                ),
              },
            ]}
          />

          <Space style={{ marginTop: 16 }}>
            <Button onClick={applyDefaultConfig}>恢复VSR最终版规则</Button>
            <Text type="secondary">一级、二级、三级编码按中文维护，保存时自动转换为系统内部编码。</Text>
          </Space>
        </Form>
      </Modal>
    </div>  );
};

export default PartNumberRuleManagementPage;






