import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Card, Form, Select, Input, Button, message, Row, Col, Divider, Typography, Space, List, Table, Tag, Modal } from 'antd';
import { PlusOutlined, CopyOutlined, ReloadOutlined } from '@ant-design/icons';
import api from '@/services/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface PartNumberRecord {
  part_id: string;
  category: string;
  main_type: string;
  sub_type: string;
  part_name?: string;
  unit?: string;
  standard_cost?: number;
  created_by?: number;
  created_by_name?: string | null;
  editable?: boolean;
  created_at: string;
}

type PartNumberSegmentRow = { key: string; name: string; value: string; description: string };
type SelectOptionItem = { value: string; label: string };

const subCategoryMapping: Record<string, string> = {
  light_source: '光源器件类',
  light_transmission: '光传输器件类',
  lens_prism: '光学透镜/棱镜类',
  optical_filter: '光学滤光片类',
  optical_sensor: '光学传感器类',
  light_modulator: '光调制器件类',
  display_imaging: '显示与成像类',
  optical_other: '其他',
  aluminum_profile: '铝型材类',
  transmission: '传动类',
  fasteners: '紧固件类',
  spring: '弹簧类',
  net_filter: '网及筛滤器类',
  mechanical_other: '其他',
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
  electrical_other: '其他',
  custom_power: '电源与储能类',
  custom_sensor: '传感器类',
  wire_harness: '线束类',
  drive_control: '驱控类',
  custom_electrical_other: '其他',
  system_software: '系统与基础软件',
  office_software: '通用办公软件',
  security_software: '安全与管理软件',
  engineering_software: '工程与研发通用软件',
  development_tools: '开发工具',
  software_other: '其他外购软件',
  custom_platform: '定制平台类',
  custom_development_tools: '定制研发工具',
  custom_information_visualization: '定制信息化与可视化',
  custom_software_other: '其他定制软件',
  inorganic: '基础无机化学品',
  organic: '有机化学品',
  reagent: '试剂与实验室化学品',
  functional: '功能化学品',
  material_chemical: '材料化学品',
  hazardous: '危险化学品',
  chemical_other: '其他化学品',
  custom_formulation: '定制配方化学品',
  custom_polymer: '定制高分子材料',
  custom_coating: '定制涂层与胶粘剂',
  custom_functional: '定制功能化学品',
  custom_material: '定制材料化学品',
  custom_environmental: '定制环境与工业化学品',
  custom_chemical_other: '其他化学品',
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

const defaultSubCategoryOrders: Record<string, string[]> = {
  processed_structure_machining: ['material_aluminum', 'material_plastic', 'material_steel', 'material_glass', 'material_other', 'surface_sandblast', 'surface_anodized', 'surface_spray', 'surface_sandblast_anodized'],
  custom_part: ['material_aluminum', 'material_plastic', 'material_steel', 'material_glass', 'material_other', 'surface_sandblast', 'surface_anodized', 'surface_spray', 'surface_sandblast_anodized'],
  standard_mechanical: ['material_aluminum', 'material_plastic', 'material_steel', 'material_glass', 'material_other', 'surface_sandblast', 'surface_anodized', 'surface_spray', 'surface_sandblast_anodized'],
  optical: ['light_source', 'light_transmission', 'lens_prism', 'optical_filter', 'optical_sensor', 'light_modulator', 'display_imaging', 'optical_other'],
  'mechanical.purchased': ['aluminum_profile', 'transmission', 'fasteners', 'spring', 'net_filter', 'mechanical_other'],
  'mechanical.custom': ['iron_steel', 'copper_aluminum_titanium', 'other_metal', 'plastic', 'rubber', 'glass_ceramic', 'material_other'],
  'electrical.purchased': ['passive', 'semiconductor', 'electromechanical', 'power', 'sensor', 'electrical_other'],
  'electrical.custom': ['custom_power', 'custom_sensor', 'wire_harness', 'drive_control', 'custom_electrical_other'],
  'software.purchased': ['system_software', 'office_software', 'security_software', 'engineering_software', 'development_tools', 'software_other'],
  'software.custom': ['custom_platform', 'custom_development_tools', 'custom_information_visualization', 'custom_software_other'],
  'chemical.purchased': ['inorganic', 'organic', 'reagent', 'functional', 'material_chemical', 'hazardous', 'chemical_other'],
  'chemical.custom': ['custom_formulation', 'custom_polymer', 'custom_coating', 'custom_functional', 'custom_material', 'custom_environmental', 'custom_chemical_other'],
};
const PartNumberApplicationPage: React.FC = () => {
  const [form] = Form.useForm();
  const [partCategory, setPartCategory] = useState<string | null>(null);
  const [mainCategory, setMainCategory] = useState<string | null>(null);
  const [subCategory, setSubCategory] = useState<string | null>(null);
  const [isMainCategoryDisabled, setIsMainCategoryDisabled] = useState(true);
  const [isSubCategoryDisabled, setIsSubCategoryDisabled] = useState(true);
  const [loading, setLoading] = useState(false);
  const [generatedPartNumber, setGeneratedPartNumber] = useState<string | null>(null);
  const [partNumberDetails, setPartNumberDetails] = useState<{
    partCategoryCode: string;
    mainCategoryCode: string;
    subCategoryCode: string;
    productNumber: string;
    versionNumber: string;
  } | null>(null);
  const [partNumberList, setPartNumberList] = useState<PartNumberRecord[]>([]);
  const [partNumberPagination, setPartNumberPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [listLoading, setListLoading] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [detailPartNumber, setDetailPartNumber] = useState<string | null>(null);
  const [detailDetails, setDetailDetails] = useState<{
    partCategoryCode: string;
    mainCategoryCode: string;
    subCategoryCode: string;
    productNumber: string;
    versionNumber: string;
  } | null>(null);
  const [detailCreatorName, setDetailCreatorName] = useState<string | null>(null);
  const [activeRulePrefix, setActiveRulePrefix] = useState<string>('');
  const [activeRuleConfig, setActiveRuleConfig] = useState<any>(null);

  const getConfiguredPartCategoryOptions = () => {
    const categories = activeRuleConfig?.part_categories || {};
    return Object.entries(categories).map(([value, info]: [string, any]) => ({
      value,
      label: info?.name || value,
    }));
  };

  const getConfiguredMainCategoryOptions = () => {
    const categories = activeRuleConfig?.main_categories || {};
    return Object.entries(categories)
      .filter(([, info]: [string, any]) => !partCategory || !info?.parent_key || info.parent_key === partCategory)
      .map(([value, info]: [string, any]) => ({
        value,
        label: `${info?.name || value}${info?.code ? `（${info.code}）` : ''}`,
      }));
  };

  const getSubCategoryOrder = (pc: string | null, mc: string | null) => {
    if (!pc || !mc) return [] as string[];
    const configuredOrders = activeRuleConfig?.sub_category_orders || {};
    return configuredOrders[`${mc}.${pc}`]
      || configuredOrders[mc]
      || defaultSubCategoryOrders[`${mc}.${pc}`]
      || defaultSubCategoryOrders[mc]
      || [];
  };

  const getConfiguredSubCategoryOptions = (pc: string | null, mc: string | null) => {
    if (!pc || !mc) return [] as { value: string; label: string }[];
    const values = getSubCategoryOrder(pc, mc);
    return values.map((value: string) => ({
      value,
      label: activeRuleConfig?.sub_categories?.[value]?.name || subCategoryMapping[value] || value,
    }));
  };

  const getPartCategoryByCode = (code: string, field: 'code' | 'identifier' = 'code') => {
    const categories = activeRuleConfig?.part_categories || {};
    return Object.entries(categories).find(([, info]: [string, any]) => String(info?.[field] ?? '') === String(code));
  };

  const getMainCategoryByConfiguredCode = (code: string) => {
    const categories = activeRuleConfig?.main_categories || {};
    return Object.entries(categories).find(([, info]: [string, any]) => String(info?.code ?? '') === String(code));
  };

  const getSelectedSubCategoryLabelByIndex = (code: string) => {
    const matched = Object.entries(activeRuleConfig?.sub_categories || {}).find(([, info]: [string, any]) => String(info?.code ?? '').padStart(2, '0') === String(code).padStart(2, '0'));
    if (matched) return (matched[1] as any)?.name || matched[0];
    const pc = form.getFieldValue('partCategory') || partCategory;
    const mc = form.getFieldValue('mainCategory') || mainCategory;
    const order = getSubCategoryOrder(pc, mc);
    const index = Number(code);
    const key = Number.isFinite(index) ? order[index] : undefined;
    return key ? subCategoryMapping[key] || key : '';
  };

  const describeSegmentValue = (segment: any, value: string) => {
    const source = segment?.source;
    if (source === 'part_category_code') {
      const matched = getPartCategoryByCode(value, 'code');
      return matched ? `${(matched[1] as any)?.name || matched[0]}，一级编码=${value}` : '来自一级大类编码';
    }
    if (source === 'part_category_identifier') {
      const matched = getPartCategoryByCode(value, 'identifier');
      return matched ? `${(matched[1] as any)?.name || matched[0]}，标识码=${value}` : '来自旧版标识码';
    }
    if (source === 'main_category_code') {
      const matched = getMainCategoryByConfiguredCode(value);
      return matched ? `${(matched[1] as any)?.name || matched[0]}，二级编码=${value}` : '来自二级类别编码';
    }
    if (source === 'sub_category_index') {
      const label = getSelectedSubCategoryLabelByIndex(value);
      return label ? `${label}，三级编码=${value}` : '来自三级编码（材质及表面处理）';
    }
    if (source === 'sequence') {
      const length = Number(segment?.length || value.length || 0);
      return `自动流水号，范围: ${'0'.repeat(length)}-${'9'.repeat(length)}`;
    }
    if (source === 'static') {
      return `固定值: ${String(segment?.value ?? value)}`;
    }
    return segment?.description || '';
  };

  const getPartNumberSegmentRows = (partNumber?: string | null): PartNumberSegmentRow[] => {
    if (!partNumber) return [];
    const digits = stripConfiguredPrefix(partNumber);
    const segments = activeRuleConfig?.segments || [];
    const totalLength = segments.reduce((sum: number, segment: any) => sum + Number(segment.length || 0), 0);
    if (!segments.length || totalLength !== digits.length) return [];

    let cursor = 0;
    return segments.map((segment: any) => {
      const length = Number(segment.length || 0);
      const value = digits.slice(cursor, cursor + length);
      cursor += length;
      return {
        key: segment.key || `${cursor}`,
        name: segment.name || segment.key || '编码段',
        value,
        description: describeSegmentValue(segment, value),
      };
    });
  };

  const renderPartNumberDetailsTable = (partNumber?: string | null, creatorName?: string | null) => {
    const rows = getPartNumberSegmentRows(partNumber);
    if (!rows.length) return null;
    return (
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #d9d9d9' }}>
          <thead>
            <tr>
              <th style={{ backgroundColor: '#f5f5f5', color: '#666', padding: '12px 8px', border: '1px solid #d9d9d9', textAlign: 'left' }}>标签名</th>
              <th style={{ backgroundColor: '#f5f5f5', color: '#666', padding: '12px 8px', border: '1px solid #d9d9d9', textAlign: 'left' }}>编号值</th>
              <th style={{ backgroundColor: '#f5f5f5', color: '#666', padding: '12px 8px', border: '1px solid #d9d9d9', textAlign: 'left' }}>信息和范围</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.key}>
                <td style={{ padding: '12px 8px', border: '1px solid #d9d9d9' }}>{row.name}</td>
                <td style={{ padding: '12px 8px', border: '1px solid #d9d9d9' }}>{row.value}</td>
                <td style={{ padding: '12px 8px', border: '1px solid #d9d9d9' }}>{row.description}</td>
              </tr>
            ))}
            {creatorName !== undefined && (
              <tr>
                <td style={{ padding: '12px 8px', border: '1px solid #d9d9d9' }}>创建人</td>
                <td style={{ padding: '12px 8px', border: '1px solid #d9d9d9' }}>{creatorName || '-'}</td>
                <td style={{ padding: '12px 8px', border: '1px solid #d9d9d9' }} />
              </tr>
            )}
          </tbody>
        </table>
      </div>
    );
  };

  const stripConfiguredPrefix = (value: string) => {
    if (activeRulePrefix && value.startsWith(activeRulePrefix)) {
      return value.slice(activeRulePrefix.length);
    }
    if (value.startsWith('VISB') || value.startsWith('VSR4')) {
      return value.slice(4);
    }
    return value;
  };

  const parseByConfiguredSegments = (digits: string) => {
    const segments = activeRuleConfig?.segments || [];
    const totalLength = segments.reduce((sum: number, segment: any) => sum + Number(segment.length || 0), 0);
    if (!segments.length || totalLength !== digits.length) return null;

    let cursor = 0;
    const parsed = {
      partCategoryCode: '',
      mainCategoryCode: '',
      subCategoryCode: '',
      productNumber: '',
      versionNumber: '',
    };
    segments.forEach((segment: any) => {
      const length = Number(segment.length || 0);
      const part = digits.slice(cursor, cursor + length);
      cursor += length;
      if (segment.source === 'part_category_code' || segment.key === 'part_type') parsed.partCategoryCode = part;
      if (segment.source === 'main_category_code' || segment.key === 'main_category') parsed.mainCategoryCode = part;
      if (segment.source === 'sub_category_index' || segment.key === 'classification') parsed.subCategoryCode = part;
      if (segment.source === 'sequence' || segment.key === 'sequence') parsed.productNumber = part;
      if (segment.key === 'version') parsed.versionNumber = part;
    });
    return parsed;
  };

  const parsePartNumber = (value: string) => {
    if (!value) return null;
    // xyh modi
    //const digits = value.startsWith('VISB') ? value.slice(4) : value;
    const digits = stripConfiguredPrefix(value);
    const configured = parseByConfiguredSegments(digits);
    if (configured) return configured;
    if (digits.length === 12) {
      return {
        partCategoryCode: digits.substring(0, 2),
        mainCategoryCode: digits.substring(3, 5),
        subCategoryCode: digits.substring(5, 7),
        productNumber: digits.substring(7, 11),
        versionNumber: digits.substring(11, 12)
      };
    }
    if (digits.length !== 11) return null;
    return {
      partCategoryCode: digits.substring(0, 1),
      mainCategoryCode: digits.substring(1, 3),
      subCategoryCode: digits.substring(3, 5),
      productNumber: digits.substring(5, 9),
      versionNumber: digits.substring(9, 11)
    };
  };

  // xyh modi
  //const ensurePrefix = (value: string) => (value?.startsWith('VISB') ? value : `VISB${value || ''}`);
  const ensurePrefix = (value: string) => {
    if (!value) return value;
    if (activeRulePrefix && value.startsWith(activeRulePrefix)) return value;
    if (value.startsWith('VISB') || value.startsWith('VSR4')) return value;
    return activeRulePrefix ? `${activeRulePrefix}${value}` : value;
  };

  const handleClickPart = (text: string) => {
    const normalized = ensurePrefix(text);
    const details = parsePartNumber(normalized);
    try {
      // xyh modi
      //const digitsId = normalized.startsWith('VISB') ? normalized.slice(4) : normalized;
      const digitsId = activeRulePrefix && normalized.startsWith(activeRulePrefix)
        ? normalized.slice(activeRulePrefix.length)
        : ((normalized.startsWith('VISB') || normalized.startsWith('VSR4')) ? normalized.slice(4) : normalized);
      const rec = partNumberList.find(r => r.part_id === normalized || r.part_id === digitsId);
      setDetailCreatorName(rec?.created_by_name ?? (rec?.created_by != null ? String(rec.created_by) : null));
    } catch {
      setDetailCreatorName(null);
    }
    setDetailPartNumber(normalized);
    setDetailDetails(details);
    setDetailVisible(true);
  };

  const getMainCategoryByCode = (codeNum: number) => {
    const categories = activeRuleConfig?.main_categories || {};
    const matched = Object.entries(categories).find(([, info]: [string, any]) => Number(info?.code) === codeNum);
    if (matched) return matched[0];
    if (codeNum >= 0 && codeNum <= 19) return 'optical';
    if (codeNum >= 20 && codeNum <= 39) return 'mechanical';
    if (codeNum >= 40 && codeNum <= 59) return 'electrical';
    if (codeNum >= 60 && codeNum <= 69) return 'software';
    if (codeNum >= 70 && codeNum <= 79) return 'chemical';
    return 'other';
  };

  const getSubCategoryOptionsBy = (pc: string, mc: string) => {
    return getConfiguredSubCategoryOptions(pc, mc);
  };
  const getSubLabelByCodes = (digits: {partCategoryCode:string; mainCategoryCode:string; subCategoryCode:string}) => {
    try {
      const matchedPart = getPartCategoryByCode(digits.partCategoryCode, 'code');
      const partCat = matchedPart ? matchedPart[0] : 'custom';
      const matchedMain = getMainCategoryByConfiguredCode(digits.mainCategoryCode);
      const main = matchedMain ? matchedMain[0] : getMainCategoryByCode(parseInt(digits.mainCategoryCode));
      const matchedSub = Object.entries(activeRuleConfig?.sub_categories || {}).find(([, info]: [string, any]) => String(info?.code ?? '').padStart(2, '0') === String(digits.subCategoryCode).padStart(2, '0'));
      if (matchedSub) return (matchedSub[1] as any)?.name || matchedSub[0];
      const opts = getSubCategoryOptionsBy(partCat, main);
      const idx = Math.floor(parseInt(digits.subCategoryCode) / 10);
      return opts[idx]?.label || '';
    } catch {
      return '';
    }
  };

  const [importForm] = Form.useForm();
  const [importLoading, setImportLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const searchTimerRef = useRef<any>(null);
  const [importVisible, setImportVisible] = useState(false);
  const [editVisible, setEditVisible] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [editRecord, setEditRecord] = useState<PartNumberRecord | null>(null);
  const [editForm] = Form.useForm();
  const handleEditName = (record: PartNumberRecord) => {
    setEditRecord(record);
    setEditVisible(true);
    editForm.setFieldsValue({
      part_name: record.part_name || '',
      unit: record.unit || 'pcs'
    });
  };
  const submitEditName = async () => {
    try {
      const values = await editForm.validateFields();
      if (!editRecord) return;
      setEditLoading(true);
      const res = await api.patch(`/visiray/part-number/${ensurePrefix(editRecord.part_id)}`, {
        part_name: values.part_name,
        unit: values.unit
      });
      if (res.data.success) {
        message.success('更新成功');
        setEditVisible(false);
        setEditRecord(null);
        fetchPartNumbers(partNumberPagination.current, partNumberPagination.pageSize, searchKeyword.trim() || undefined);
      } else {
        message.error(res.data.message || '更新失败');
      }
    } catch (e: any) {
      const msg = e?.response?.data?.message || e?.message || '更新失败';
      message.error(msg);
    } finally {
      setEditLoading(false);
    }
  };
  const handleImport = async () => {
    try {
      const values = await importForm.validateFields();
      const payload = {
        part_id: ensurePrefix(values.part_id),
        part_name: values.part_name,
        unit: values.unit || 'pcs'
      };
      setImportLoading(true);
      const res = await api.post('/visiray/part-number/import', payload);
      if (res.data.success) {
        message.success(res.data.message || '添加成功');
        fetchPartNumbers(1, partNumberPagination.pageSize);
        handleClickPart(payload.part_id);
        importForm.resetFields();
        setImportVisible(false);
      } else {
        message.error(res.data.message || '添加失败');
      }
    } catch (e: any) {
      message.error(e?.response?.data?.message || '添加失败');
    } finally {
      setImportLoading(false);
    }
  };

  // 大类选项
  const mainCategoryOptions = [
    { value: 'custom_part', label: '零件（2100）' },
    { value: 'custom_product', label: '产品（2200）' },
    { value: 'standard_mechanical', label: '机械类（3100）' },
    { value: 'standard_optical', label: '光学类（3200）' },
    { value: 'standard_electrical', label: '电气类（3300）' },
  ];

  const getSubCategoryOptions = () => {
    if (!partCategory || !mainCategory) return [];
    return getConfiguredSubCategoryOptions(partCategory, mainCategory);
  };
  // 处理零部件类别变化
  const handlePartCategoryChange = (value: string) => {
    setPartCategory(value);
    setMainCategory(null);
    setSubCategory(null);
    form.setFieldsValue({ mainCategory: null, subCategory: null });
    
    if (value) {
      setIsMainCategoryDisabled(false);
      setIsSubCategoryDisabled(true);
    } else {
      setIsMainCategoryDisabled(true);
      setIsSubCategoryDisabled(true);
    }
  };

  // 处理大类变化
  const handleMainCategoryChange = (value: string) => {
    setMainCategory(value);
    setSubCategory(null);
    form.setFieldsValue({ subCategory: null });
    
    if (value && value !== 'other') {
      setIsSubCategoryDisabled(false);
    } else {
      setIsSubCategoryDisabled(true);
    }
  };

  // 处理小类变化
  const handleSubCategoryChange = (value: string) => {
    setSubCategory(value);
  };

  // 复制零件号到剪贴板
  const copyToClipboard = () => {
    if (generatedPartNumber) {
      navigator.clipboard.writeText(generatedPartNumber);
      message.success('零件号已复制到剪贴板');
    }
  };

  // 鎻愪氦琛ㄥ崟
  const onFinish = async (values: any) => {
    try {
      setLoading(true);
      const payload = {
        ...values,
        partCategory: values.partCategory || partCategory,
        mainCategory: values.mainCategory || mainCategory,
        subCategory: values.subCategory || subCategory,
      };
      const response = await api.post('/visiray/part-number/apply', payload);
      
      if (response.data.success) {
        const newPartNumber = response.data.data.part_number;
        setGeneratedPartNumber(newPartNumber);
        const details = parsePartNumber(newPartNumber);
        setPartNumberDetails(details);
        
        message.success("零件号申请成功");
        
        // 重新加载零件号列表
        fetchPartNumbers(1, partNumberPagination.pageSize);
      } else {
        message.error(response.data.message || "零件号申请失败");
      }
    } catch (error: any) {
      console.error("申请零件号失败", error);
      const msg = error?.response?.data?.message || (error?.message ?? "零件号申请失败，请稍后重试");
      message.error(msg);
    } finally {
      setLoading(false);
    }
  };

  // 获取零件号列表
  const fetchPartNumbers = async (
    page = partNumberPagination.current,
    pageSize = partNumberPagination.pageSize,
    keyword = searchKeyword.trim() || undefined
  ) => {
    try {
      setListLoading(true);
      const response = await api.get('/visiray/part-numbers', {
        params: {
          page,
          per_page: pageSize,
          ...(keyword ? { keyword } : {}),
        },
        timeout: 60000,
      });
      
      if (response.data.success) {
        const data = response.data.data || {};
        setPartNumberList(data.items || []);
        setPartNumberPagination({
          current: data.current_page || page,
          pageSize: data.per_page || pageSize,
          total: data.total || 0,
        });
      } else {
        message.error(response.data.message || "获取零件号列表失败");
      }
    } catch (error) {
      console.error("获取零件号列表失败", error);
      message.error("获取零件号列表失败，请稍后重试");
    } finally {
      setListLoading(false);
    }
  };

  const fetchActivePartNumberRule = async () => {
    try {
      const response = await api.get('/visiray/part-number-rules/active');
      if (response.data.success) {
        setActiveRulePrefix(response.data.data?.prefix || '');
        setActiveRuleConfig(response.data.data?.config || null);
      }
    } catch (error) {
      console.error("获取零件号规则失败", error);
    }
  };

  // 清空零件号列表
  // const clearPartNumberList = () => {
  //   setPartNumberList([]);
  //   message.success('列表已清空');
  // };

  // 清空数据库中的所有零件号记录
  // const clearAllPartNumbers = async () => {
  //   try {
  //     // 调用后端 API 清空数据库中的记录
  //     const response = await api.delete('/visiray/part-numbers/clear');
  //     
  //     if (response.data.success) {
  //       // 清空显示列表
  //       setPartNumberList([]);
  //       message.success('已清空所有零件号记录');
  //     } else {
  //       message.error(response.data.message || '清空零件号记录失败');
  //     }
  //   } catch (error) {
  //     console.error('清空零件号记录失败', error);
  //     message.error('清空零件号记录失败，请稍后重试');
  //   }
  // };

  // 页面加载时恢复状态
  useEffect(() => {
    // 从 localStorage 或其他状态管理中恢复状态
    const savedState = localStorage.getItem('partNumberAppState');
    if (savedState) {
      try {
        const state = JSON.parse(savedState);
        if (state.partCategory) setPartCategory(state.partCategory);
        if (state.mainCategory) setMainCategory(state.mainCategory);
        if (state.subCategory) setSubCategory(state.subCategory);
        if (state.generatedPartNumber) setGeneratedPartNumber(state.generatedPartNumber);
        if (state.partNumberDetails) setPartNumberDetails(state.partNumberDetails);
        
        // 使用 setTimeout 确保在组件完全挂载后设置表单值
        setTimeout(() => {
          if (state.partCategory) form.setFieldsValue({
            partCategory: state.partCategory,
            mainCategory: state.mainCategory,
            subCategory: state.subCategory
          });
        }, 0);
        
        // 设置禁用状态
        if (state.partCategory) {
          setIsMainCategoryDisabled(false);
          if (state.mainCategory) {
            setIsSubCategoryDisabled(false);
          }
        }
      } catch (e) {
        console.error('恢复状态失败', e);
      }
    }
    
    fetchActivePartNumberRule();
    fetchPartNumbers(1, partNumberPagination.pageSize);
  }, []); // 空依赖数组，只在组件挂载时执行一次

  // 状态变化时，同步更新表单字段
  useEffect(() => {
    if (partCategory || mainCategory || subCategory) {
      form.setFieldsValue({
        partCategory: partCategory,
        mainCategory: mainCategory,
        subCategory: subCategory
      });
    }
  }, [partCategory, mainCategory, subCategory, form]);

  // 状态变化时保存到 localStorage
  useEffect(() => {
    const state = {
      partCategory,
      mainCategory,
      subCategory,
      generatedPartNumber,
      partNumberDetails
    };
    localStorage.setItem('partNumberAppState', JSON.stringify(state));
  }, [partCategory, mainCategory, subCategory, generatedPartNumber, partNumberDetails]);

  // 零件号列表表格列定义
  const columns = [
    {
      title: '零件号',
      dataIndex: 'part_id',
      key: 'part_id',
      render: (text: string) => (
        <a onClick={() => handleClickPart(ensurePrefix(text))} style={{ textDecoration: 'none' }}>
          <Text code style={{ fontSize: '16px', padding: '4px 8px', backgroundColor: '#e6f7ff', borderRadius: 4, border: '1px solid #91d5ff', color: '#1890ff', fontWeight: 'bold' }}>
            {ensurePrefix(text)}
          </Text>
        </a>
      )
    },
    {
      title: '创建人',
      dataIndex: 'created_by_name',
      key: 'created_by_name',
      render: (text: string | null, record: PartNumberRecord) => text || (record.created_by != null ? String(record.created_by) : '-')
    },
    {
      title: '零件名称',
      dataIndex: 'part_name',
      key: 'part_name',
      render: (text: string) => text || '-'
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
      width: 80,
      render: (text: string) => text || 'pcs'
    },
    {
      title: '一级大类',
      dataIndex: 'category',
      key: 'category',
      render: (text: string) => {
        const name = activeRuleConfig?.part_categories?.[text]?.name || (text === 'custom' ? '定制件' : text === 'purchased' ? '外购件' : text);
        return <Tag color={text === 'custom' ? 'blue' : 'green'}>{name}</Tag>;
      }
    },
    {
      title: '二级类别',
      dataIndex: 'main_type',
      key: 'main_type',
      render: (text: string) => activeRuleConfig?.main_categories?.[text]?.name || mainCategoryOptions.find((item) => item.value === text)?.label || text
    },
    {
      title: '三级编码',
      dataIndex: 'sub_type',
      key: 'sub_type_name',
      render: (text: string) => activeRuleConfig?.sub_categories?.[text]?.name || subCategoryMapping[text] || text || '-'
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => text ? new Date(text).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }) : '-'
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: PartNumberRecord) => (
        <Space>
          <Button type="link" disabled={!record.editable} onClick={() => handleEditName(record)}>编辑名称</Button>
        </Space>
      )
    }
  ];

  return (
    <Card>
      <Title level={3} style={{ margin: '0 0 20px 0' }}>零件号一键申请</Title>
      
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="partCategory"
              label="一级大类"
              rules={[{ required: true, message: "请选择一级大类" }]}
            >
              <Select
                placeholder="请选择一级大类"
                onChange={handlePartCategoryChange}
                value={partCategory || undefined}
              >
                {(getConfiguredPartCategoryOptions().length > 0
                  ? getConfiguredPartCategoryOptions()
                  : [
                      { value: 'custom', label: '定制件' },
                      { value: 'standard', label: '标准件' }
                    ]).map(option => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          
          <Col span={8}>
            <Form.Item
              name="mainCategory"
              label="二级类别"
              rules={[{ required: true, message: "请选择二级类别" }]}
            >
              <Select
                placeholder="请选择二级类别"
                onChange={handleMainCategoryChange}
                disabled={isMainCategoryDisabled}
                value={mainCategory || undefined}
              >
                {(getConfiguredMainCategoryOptions().length > 0
                  ? getConfiguredMainCategoryOptions()
                  : mainCategoryOptions).map(option => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          
          <Col span={8}>
            <Form.Item
              name="subCategory"
              label="三级编码（材质/表面处理）"
              rules={[{ required: mainCategory !== null, message: "请选择三级编码" }]}
            >
              <Select
                placeholder="请选择三级编码"
                onChange={handleSubCategoryChange}
                disabled={isSubCategoryDisabled}
                value={subCategory || undefined}
                showSearch
                optionFilterProp="label"
                filterOption={(input, option) =>
                  (option?.label?.toString() ?? '').toLowerCase().includes(input.toLowerCase())
                }
              >
                {getSubCategoryOptions().map((option: SelectOptionItem) => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={16}>
            <Form.Item
              name="part_name"
              label="零件名称"
              rules={[
                { required: true, whitespace: true, message: "请输入零件名称" },
                { max: 200, message: "零件名称不超过200字符" },
              ]}
            >
              <Input placeholder="例如：铝型材导轨、压缩弹簧、12V电源模块" />
            </Form.Item>
          </Col>
          <Col span={4}>
            <Form.Item name="unit" label="单位" initialValue="pcs">
              <Input placeholder="pcs" />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<PlusOutlined />} loading={loading}>
            申请零件号
          </Button>
        </Form.Item>
      </Form>
      
      {/* 显示生成的零件号 */}
      {generatedPartNumber && (
        <div style={{ marginTop: 20, padding: 20, backgroundColor: '#f0f2f5', borderRadius: 8 }}>
          <Title level={4} style={{ margin: '0 0 16px 0', color: '#1890ff' }}>生成的零件号</Title>
          <Space size="large" style={{ marginBottom: 16 }}>
            <Text 
              code 
              style={{ 
                fontSize: '24px', 
                padding: '12px 20px', 
                backgroundColor: '#e6f7ff', 
                borderRadius: 6, 
                border: '1px solid #91d5ff',
                color: '#1890ff',
                fontWeight: 'bold'
              }}
            >
              {generatedPartNumber}
            </Text>
            <Button 
              icon={<CopyOutlined />} 
              onClick={copyToClipboard}
              type="primary"
              size="large"
            >
              复制
            </Button>
          </Space>
          {renderPartNumberDetailsTable(generatedPartNumber)}
          </div>
        )}

        

        {/* 显示所有已生成的零件号列表 */}
          <div style={{ marginTop: 30 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={4} style={{ margin: 0 }}>已生成的零件号列表</Title>
          <div>
            <Input.Search
              placeholder="按零件号/类别/大类搜索"
              allowClear
              style={{ width: 320, marginRight: 8 }}
              value={searchKeyword}
              onChange={(e) => {
                const v = e.target.value;
                setSearchKeyword(v);
                if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
                searchTimerRef.current = setTimeout(() => {
                  fetchPartNumbers(1, partNumberPagination.pageSize, v.trim() || undefined);
                }, 300);
              }}
              onSearch={(v) => {
                const kw = (v || '').trim();
                setSearchKeyword(kw);
                fetchPartNumbers(1, partNumberPagination.pageSize, kw || undefined);
              }}
            />
            <Button icon={<ReloadOutlined />} onClick={() => fetchPartNumbers(partNumberPagination.current, partNumberPagination.pageSize, searchKeyword.trim() || undefined)} loading={listLoading}>
              刷新
            </Button>
          </div>
        </div>
        <Table
          dataSource={partNumberList}
          columns={columns}
          loading={listLoading}
          pagination={{
            current: partNumberPagination.current,
            pageSize: partNumberPagination.pageSize,
            total: partNumberPagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => fetchPartNumbers(page, pageSize || partNumberPagination.pageSize, searchKeyword.trim() || undefined),
          }}
          rowKey="part_id"
        />

        <Modal
          open={detailVisible}
          title="零件号详情"
          onCancel={() => setDetailVisible(false)}
          footer={null}
          width={760}
        >
          <Space size="large" style={{ marginBottom: 16 }}>
            <Text 
              code 
              style={{ 
                fontSize: '20px', 
                padding: '10px 16px', 
                backgroundColor: '#e6f7ff', 
                borderRadius: 6, 
                border: '1px solid #91d5ff',
                color: '#1890ff',
                fontWeight: 'bold'
              }}
            >
              {detailPartNumber}
            </Text>
            <Button 
              icon={<CopyOutlined />} 
              onClick={() => {
                if (detailPartNumber) {
                  navigator.clipboard.writeText(detailPartNumber);
                  message.success("零件号已复制到剪贴板");
                }
              }}
              type="primary"
            >
              复制
            </Button>
          </Space>
          {renderPartNumberDetailsTable(detailPartNumber, detailCreatorName)}
        </Modal>
        <Modal
          open={editVisible}
          title="编辑零件名称"
          onCancel={() => setEditVisible(false)}
          onOk={submitEditName}
          confirmLoading={editLoading}
          destroyOnHidden
        >
          <Form form={editForm} layout="vertical">
            <Form.Item name="part_name" label="零件名称" rules={[{ required: true, message: "请输入零件名称" }]}> 
              <Input placeholder="请输入零件名称" />
            </Form.Item>
            <Form.Item name="unit" label="单位">
              <Input placeholder="pcs" />
            </Form.Item>
          </Form>
        </Modal>
        <Modal
          open={importVisible}
          title="添加已有零件号"
          onCancel={() => setImportVisible(false)}
          onOk={handleImport}
          confirmLoading={importLoading}
          destroyOnHidden
        >
          <Form form={importForm} layout="vertical">
            <Form.Item name="part_id" label="零件号" rules={[{ required: true, message: "请输入零件号" }]}> 
              <Input placeholder="支持带前缀或纯数字零件号" />
            </Form.Item>
            <Form.Item name="part_name" label="零件名称">
              <Input placeholder="可选" />
            </Form.Item>
            <Form.Item name="unit" label="单位" initialValue="pcs">
              <Input placeholder="pcs" />
            </Form.Item>
            <div style={{ color: '#888' }}>
              系统将自动识别类别与大类，无需手动填写。
            </div>
          </Form>
        </Modal>
      </div>
    </Card>
  );
};

export default PartNumberApplicationPage;






