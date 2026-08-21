// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  name: string;
  phone?: string;
  department?: string;
  position?: string;
  is_active: boolean;
  is_verified: boolean;
  auth_type: 'local' | 'sso';
  last_login?: string;
  created_at: string;
  roles?: Role[];
  permissions?: string[];
}

export interface Role {
  id: number;
  name: string;
  code: string;
  description?: string;
  is_active: boolean;
  permissions: Permission[];
}

export interface Permission {
  id: number;
  name: string;
  code: string;
  description?: string;
  resource?: string;
  action?: string;
}

// 物料相关类型
export interface Material {
  id: number;
  material_code: string;
  material_name: string;
  specification?: string;
  unit: string;
  category_id?: number;
  category_name?: string;
  standard_cost: number;
  currency: string;
  material_type: 'custom' | 'purchase';
  status: 'active' | 'inactive' | 'obsolete';
  safety_stock: number;
  current_stock: number;
  weight?: number;
  volume?: number;
  color?: string;
  material_grade?: string;
  remark?: string;
  is_active: boolean;
  created_at: string;
  suppliers?: MaterialSupplier[];
}

export interface PartNumberVersion {
  id: number;
  part_id: string;
  version_no: string;
  version_number?: string;
  status: 'active' | 'obsolete';
  is_current: boolean;
  remark?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MaterialCategory {
  id: number;
  category_code: string;
  category_name: string;
  parent_id?: number;
  level: number;
  part_type?: number;
  type_identifier?: number;
  part_category?: number;
  classification?: number;
  description?: string;
  is_active: boolean;
  sort_order: number;
  children?: MaterialCategory[];
}

export interface MaterialSupplier {
  id: number;
  material_id: number;
  supplier_id: number;
  part_version_id?: number;
  version_no?: string;
  supplier_name?: string;
  price: number;
  currency: string;
  price_date: string;
  valid_from?: string;
  valid_to?: string;
  is_primary: boolean;
  lead_time?: number;
  min_order_qty?: number;
  supplier_part_no?: string;
  status: 'active' | 'inactive';
  remark?: string;
}

// BOM相关类型
export interface BOM {
  id: number;
  bom_code: string;
  product_name: string;
  product_model?: string;
  product_spec?: string;
  version: string;
  parent_bom_id?: number;
  status: 'draft' | 'active' | 'inactive' | 'obsolete';
  base_quantity: number;
  unit: string;
  total_cost: number;
  material_cost: number;
  labor_cost: number;
  overhead_cost: number;
  process_route?: string;
  lead_time?: number;
  effective_date?: string;
  expiry_date?: string;
  remark?: string;
  is_active: boolean;
  approved_by?: number;
  approved_at?: string;
  created_by: number;
  created_at: string;
  items?: BOMItem[];
  tree_structure?: BOMTreeNode[];
}

export interface BOMItem {
  id: number;
  bom_id: number;
  material_id?: number;
  part_version_id?: number;
  version_no?: string;
  version_status?: string;
  version_options?: PartNumberVersion[];
  material_code?: string;
  material_name?: string;
  sub_bom_id?: number;
  sub_bom_code?: string;
  parent_item_id?: number;
  level: number;
  sort_order: number;
  item_no?: string;
  quantity: number;
  unit: string;
  is_key_material: boolean;
  is_optional: boolean;
  usage_rate: number;
  selected_supplier_id?: number;
  selected_supplier_name?: string;
  selected_supplier_price?: number;
  supplier_options?: MaterialSupplier[];
  has_multiple_suppliers?: boolean;
  substitute_group?: string;
  substitute_priority: number;
  process_step?: string;
  assembly_note?: string;
  effective_date?: string;
  expiry_date?: string;
  remark?: string;
  is_active: boolean;
  item_cost: number;
  children?: BOMItem[];
}

export interface BOMTreeNode {
  key: string;
  title: string;
  material_code?: string;
  quantity: number;
  unit: string;
  item_cost: number;
  children?: BOMTreeNode[];
}

export interface BOMShortageItem {
  material_id?: number;
  material_code?: string;
  part_id?: string;
  part_version_id?: number;
  version_no?: string;
  material_name?: string;
  unit: string;
  required_quantity: number;
  stock_quantity: number;
  shortage_quantity: number;
  stock_source: 'visiray_inventory' | 'material_current_stock';
  inventory_goods_id?: number;
  inventory_name?: string;
  inventory_supplier?: string;
  is_key_material: boolean;
  is_optional: boolean;
  substitute_group?: string;
  substitute_priority?: number;
  paths: string[];
}

export interface BOMShortageReport {
  bom_id: number;
  bom_code: string;
  product_name: string;
  base_quantity: number;
  production_quantity: number;
  items: BOMShortageItem[];
  shortage_items: BOMShortageItem[];
  summary: {
    item_count: number;
    shortage_item_count: number;
    total_required_quantity: number;
    total_stock_quantity: number;
    total_shortage_quantity: number;
  };
}

export interface BOMVersion {
  id: number;
  bom_id: number;
  version_number: string;
  version_note?: string;
  change_type: 'create' | 'update' | 'delete';
  change_reason?: string;
  is_current: boolean;
  created_by: number;
  creator_name?: string;
  created_at: string;
}

// 供应商相关类型
export interface Supplier {
  id: number;
  supplier_code: string;
  supplier_name: string;
  supplier_name_en?: string;
  contact_person?: string;
  phone?: string;
  mobile?: string;
  fax?: string;
  email?: string;
  website?: string;
  country?: string;
  province?: string;
  city?: string;
  address?: string;
  postal_code?: string;
  legal_person?: string;
  registered_capital?: number;
  business_license?: string;
  tax_number?: string;
  supplier_type: 'material' | 'service' | 'equipment' | 'other';
  supplier_level: 'A' | 'B' | 'C' | 'D';
  iso_certification?: string;
  quality_certification?: string;
  payment_terms?: string;
  currency: string;
  credit_limit?: number;
  lead_time?: number;
  delivery_terms?: string;
  quality_rating?: number;
  delivery_rating?: number;
  service_rating?: number;
  overall_rating?: number;
  status: 'active' | 'inactive' | 'blacklist';
  cooperation_status: 'potential' | 'cooperation' | 'terminated';
  remark?: string;
  is_active: boolean;
  created_at: string;
  materials_count: number;
  materials?: MaterialSupplier[];
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
}

export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  pages: number;
  current_page: number;
  per_page: number;
  has_prev: boolean;
  has_next: boolean;
}

// 表单类型
export interface LoginForm {
  username: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterForm {
  username: string;
  email: string;
  name: string;
  password: string;
  phone?: string;
  department?: string;
  position?: string;
}

export interface MaterialForm {
  material_code?: string;
  material_name: string;
  specification?: string;
  unit: string;
  category_id?: number;
  standard_cost?: number;
  currency?: string;
  material_type?: 'custom' | 'purchase';
  safety_stock?: number;
  current_stock?: number;
  weight?: number;
  volume?: number;
  color?: string;
  material_grade?: string;
  remark?: string;
  suppliers?: MaterialSupplierForm[];
}

export interface MaterialSupplierForm {
  supplier_id: number;
  part_version_id?: number;
  price: number;
  currency?: string;
  valid_from?: string;
  valid_to?: string;
  is_primary?: boolean;
  lead_time?: number;
  min_order_qty?: number;
  supplier_part_no?: string;
  remark?: string;
}

export interface BOMForm {
  bom_code?: string;
  product_name: string;
  product_model?: string;
  product_spec?: string;
  version?: string;
  parent_bom_id?: number;
  base_quantity?: number;
  unit?: string;
  process_route?: string;
  lead_time?: number;
  effective_date?: string;
  expiry_date?: string;
  remark?: string;
  items?: BOMItemForm[];
}

export interface BOMItemForm {
  material_id?: number;
  part_id?: string;
  part_version_id?: number;
  sub_bom_id?: number;
  parent_item_id?: number;
  level?: number;
  sort_order?: number;
  item_no?: string;
  quantity: number;
  unit?: string;
  is_key_material?: boolean;
  is_optional?: boolean;
  usage_rate?: number;
  selected_supplier_id?: number;
  substitute_group?: string;
  substitute_priority?: number;
  process_step?: string;
  assembly_note?: string;
  effective_date?: string;
  expiry_date?: string;
  remark?: string;
}

export interface SupplierForm {
  supplier_code?: string;
  supplier_name: string;
  supplier_name_en?: string;
  contact_person?: string;
  phone?: string;
  mobile?: string;
  fax?: string;
  email?: string;
  website?: string;
  country?: string;
  province?: string;
  city?: string;
  address?: string;
  postal_code?: string;
  legal_person?: string;
  registered_capital?: number;
  business_license?: string;
  tax_number?: string;
  supplier_type?: 'material' | 'service' | 'equipment' | 'other';
  supplier_level?: 'A' | 'B' | 'C' | 'D';
  iso_certification?: string;
  quality_certification?: string;
  payment_terms?: string;
  currency?: string;
  credit_limit?: number;
  lead_time?: number;
  delivery_terms?: string;
  quality_rating?: number;
  delivery_rating?: number;
  service_rating?: number;
  remark?: string;
}
