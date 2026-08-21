import api from './api';
import { ApiResponse, User, LoginForm, RegisterForm } from '@/types';

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  permissions: string[];
}

class AuthService {
  // 本地登录
  async login(data: LoginForm): Promise<AuthResponse> {
    const response = await api.post<ApiResponse<AuthResponse>>('/auth/login', data);
    return response.data.data!;
  }

  // 用户注册
  async register(data: RegisterForm): Promise<User> {
    const response = await api.post<ApiResponse<{ user: User }>>('/auth/register', data);
    return response.data.data!.user;
  }

  // 登出
  async logout(): Promise<void> {
    await api.post('/auth/logout');
  }

  // 获取当前用户信息
  async getCurrentUser(): Promise<{ user: User; permissions: string[] }> {
    const response = await api.get<ApiResponse<{ user: User; permissions: string[] }>>('/auth/me');
    return response.data.data!;
  }

  // 刷新token
  async refreshToken(): Promise<{ access_token: string }> {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await api.post<ApiResponse<{ access_token: string }>>(
      '/auth/refresh',
      {},
      {
        headers: {
          Authorization: `Bearer ${refreshToken}`,
        },
      }
    );
    return response.data.data!;
  }

  // 修改密码
  async changePassword(data: { old_password: string; new_password: string }): Promise<void> {
    await api.post('/auth/password/change', data);
  }

  // 更新用户信息
  async updateUserInfo(userId: number, data: Partial<User>): Promise<User> {
    const response = await api.put<ApiResponse<{ user: User }>>(`/users/${userId}`, data);
    return response.data.data!.user;
  }

  // 获取SSO状态
  async getSSOStatus(): Promise<{ sso_enabled: boolean; providers: string[] }> {
    const response = await api.get<ApiResponse<{ sso_enabled: boolean; providers: string[] }>>(
      '/auth/sso/status'
    );
    return response.data.data!;
  }

  // 获取SSO重定向URL
  async getSSORedirectUrl(): Promise<{ redirect_url: string }> {
    const response = await api.get<ApiResponse<{ redirect_url: string }>>(
      '/auth/sso/redirect'
    );
    return response.data.data!;
  }

  // 获取用户权限
  async getUserPermissions(): Promise<{ permissions: string[] }> {
    const response = await api.get<ApiResponse<{ permissions: string[] }>>(
      '/auth/permissions'
    );
    return response.data.data!;
  }

  // 保存认证信息到本地存储
  saveAuthData(authData: AuthResponse): void {
    localStorage.setItem('access_token', authData.access_token);
    localStorage.setItem('refresh_token', authData.refresh_token);
    localStorage.setItem('user', JSON.stringify(authData.user));
    localStorage.setItem('permissions', JSON.stringify(authData.permissions));
  }

  // 清除认证信息
  clearAuthData(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('permissions');
  }

  // 检查是否已登录
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }

  // 获取本地存储的用户信息
  getLocalUser(): User | null {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  // 获取本地存储的权限
  getLocalPermissions(): string[] {
    const permissionsStr = localStorage.getItem('permissions');
    return permissionsStr ? JSON.parse(permissionsStr) : [];
  }

  // 检查用户是否有指定权限
  hasPermission(permission: string): boolean {
    const permissions = this.getLocalPermissions();
    return permissions.includes(permission);
  }

  // 检查用户是否有任一权限
  hasAnyPermission(permissions: string[]): boolean {
    const userPermissions = this.getLocalPermissions();
    return permissions.some(permission => userPermissions.includes(permission));
  }

  // 检查用户是否有所有权限
  hasAllPermissions(permissions: string[]): boolean {
    const userPermissions = this.getLocalPermissions();
    return permissions.every(permission => userPermissions.includes(permission));
  }

  // 检查用户是否为管理员
  isAdmin(): boolean {
    const user = this.getLocalUser();
    if (!user || !user.roles) return false;
    
    // 检查用户是否具有admin角色
    return user.roles.some(role => role.code === 'admin');
  }
}

export default new AuthService();