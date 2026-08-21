import React from 'react';
import { useAppSelector } from '@/store/hooks';
import authService from '@/services/auth';

interface PermissionProps {
  permission?: string;
  permissions?: string[];
  requireAll?: boolean;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * 权限控制组件
 * @param permission 单个权限码
 * @param permissions 权限码数组
 * @param requireAll 是否需要拥有所有权限（默认false，只需要拥有其中一个）
 * @param children 有权限时渲染的内容
 * @param fallback 无权限时渲染的内容
 */
const Permission: React.FC<PermissionProps> = ({
  permission,
  permissions,
  requireAll = false,
  children,
  fallback = null
}) => {
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  // 未登录直接返回fallback
  if (!isAuthenticated) {
    return <>{fallback}</>;
  }

  let hasPermission = false;

  if (permission) {
    // 检查单个权限
    hasPermission = authService.hasPermission(permission);
  } else if (permissions && permissions.length > 0) {
    // 检查多个权限
    if (requireAll) {
      hasPermission = authService.hasAllPermissions(permissions);
    } else {
      hasPermission = authService.hasAnyPermission(permissions);
    }
  } else {
    // 没有指定权限，默认有权限（仅需要登录）
    hasPermission = true;
  }

  return hasPermission ? <>{children}</> : <>{fallback}</>;
};

export default Permission;