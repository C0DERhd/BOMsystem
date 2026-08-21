import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// Vite环境变量类型声明
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_APP_NAME: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// 请求拦截器
api.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
let isRefreshing = false;
let pendingRequests: Array<(token: string) => void> = [];

function onRefreshed(token: string) {
  pendingRequests.forEach((cb) => cb(token));
  pendingRequests = [];
}

api.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response;
    if (data.hasOwnProperty('success') && !data.success) {
      return Promise.reject(new Error(data.message || '请求失败'));
    }
    return response;
  },
  async (error) => {
    const { response, config } = error;
    if (response) {
      const { status, data } = response;
      if (status === 401) {
        const originalRequest = config as any;
        if (originalRequest && !originalRequest._retry) {
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            originalRequest._retry = true;
            if (!isRefreshing) {
              isRefreshing = true;
              try {
                const res = await api.post(
                  '/auth/refresh',
                  {},
                  { headers: { Authorization: `Bearer ${refreshToken}` } }
                );
                const newToken = res.data?.data?.access_token;
                if (newToken) {
                  localStorage.setItem('access_token', newToken);
                  onRefreshed(newToken);
                }
              } catch (e) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
                isRefreshing = false;
                return Promise.reject(error);
              }
              isRefreshing = false;
            }
            const retryOriginalRequest = new Promise((resolve) => {
              pendingRequests.push((token: string) => {
                originalRequest.headers = originalRequest.headers || {};
                originalRequest.headers.Authorization = `Bearer ${token}`;
                resolve(api(originalRequest));
              });
            });
            return retryOriginalRequest;
          } else {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
            return Promise.reject(error);
          }
        }
        return Promise.reject(error);
      }
      if (status === 403) {
        console.warn('权限不足');
        return Promise.reject(error);
      }
      if (status === 404) {
        console.warn('请求的资源不存在');
        return Promise.reject(error);
      }
      if (status === 422) {
        console.warn('请求参数错误');
        return Promise.reject(error);
      }
      if (status === 500) {
        console.error('服务器内部错误');
        return Promise.reject(error);
      }
      console.error(data?.message || `请求失败 (${status})`);
      return Promise.reject(error);
    } else {
      console.error('网络连接失败，请检查网络设置');
      return Promise.reject(error);
    }
  }
);

export default api;
