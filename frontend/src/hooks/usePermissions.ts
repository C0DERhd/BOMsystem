import { useAppSelector } from '@/store/hooks';
import authService from '@/services/auth';

/**
 * 权限管理Hook
 */
export const usePermissions = () => {
  const { isAuthenticated, user, permissions } = useAppSelector((state) => state.auth);

  const hasPermission = (permission: string): boolean => {
    if (!isAuthenticated) return false;
    return authService.hasPermission(permission);
  };

  const hasAnyPermission = (permissions: string[]): boolean => {
    if (!isAuthenticated) return false;
    return authService.hasAnyPermission(permissions);
  };

  const hasAllPermissions = (permissions: string[]): boolean => {
    if (!isAuthenticated) return false;
    return authService.hasAllPermissions(permissions);
  };

  const hasRole = (roleCode: string): boolean => {
    if (!isAuthenticated || !user) return false;
    return user.roles?.some(role => role.code === roleCode) || false;
  };

  const hasAnyRole = (roleCodes: string[]): boolean => {
    if (!isAuthenticated || !user) return false;
    return roleCodes.some(roleCode => hasRole(roleCode));
  };

  const isAdmin = (): boolean => {
    return hasRole('admin');
  };

  return {
    isAuthenticated,
    user,
    permissions,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    isAdmin
  };
};

/**
 * 权限常量定义
 */
export const PERMISSIONS = {
  // 用户管理权限
  USER_READ: 'user_read',
  USER_CREATE: 'user_create',
  USER_UPDATE: 'user_update',
  USER_DELETE: 'user_delete',
  USER_ROLE_ASSIGN: 'user_role_assign',

  // 物料管理权限
  MATERIAL_READ: 'material_read',
  MATERIAL_CREATE: 'material_create',
  MATERIAL_UPDATE: 'material_update',
  MATERIAL_DELETE: 'material_delete',
  MATERIAL_CATEGORY_MANAGE: 'material_category_manage',

  // BOM管理权限
  BOM_READ: 'bom_read',
  BOM_CREATE: 'bom_create',
  BOM_UPDATE: 'bom_update',
  BOM_DELETE: 'bom_delete',
  BOM_APPROVE: 'bom_approve',

  // 供应商管理权限
  SUPPLIER_READ: 'supplier_read',
  SUPPLIER_CREATE: 'supplier_create',
  SUPPLIER_UPDATE: 'supplier_update',
  SUPPLIER_DELETE: 'supplier_delete',

  // 系统管理权限
  SYSTEM_CONFIG: 'system_config',
  DATA_IMPORT_EXPORT: 'data_import_export'
} as const;

/**
 * 角色常量定义
 */
export const ROLES = {
  ADMIN: 'admin',
  BOM_ADMIN: 'bom_admin',
  USER: 'user'
} as const;