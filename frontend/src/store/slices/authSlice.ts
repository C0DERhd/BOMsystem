import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { User, LoginForm } from '@/types';
import authService, { AuthResponse } from '@/services/auth';

interface AuthState {
  user: User | null;
  permissions: string[];
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: authService.getLocalUser(),
  permissions: authService.getLocalPermissions(),
  isAuthenticated: authService.isAuthenticated(),
  loading: false,
  error: null,
};

// 异步操作
export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginForm, { rejectWithValue }) => {
    try {
      const authData = await authService.login(credentials);
      authService.saveAuthData(authData);
      return authData;
    } catch (error: any) {
      return rejectWithValue(error.message || '登录失败');
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout();
      authService.clearAuthData();
    } catch (error: any) {
      // 即使请求失败也要清除本地数据
      authService.clearAuthData();
      return rejectWithValue(error.message || '登出失败');
    }
  }
);

export const getCurrentUser = createAsyncThunk(
  'auth/getCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const data = await authService.getCurrentUser();
      // 更新本地存储
      localStorage.setItem('user', JSON.stringify(data.user));
      localStorage.setItem('permissions', JSON.stringify(data.permissions));
      return data;
    } catch (error: any) {
      return rejectWithValue(error.message || '获取用户信息失败');
    }
  }
);

export const updateUserInfo = createAsyncThunk(
  'auth/updateUserInfo',
  async ({ userId, data }: { userId: number; data: Partial<User> }, { rejectWithValue }) => {
    try {
      const updatedUser = await authService.updateUserInfo(userId, data);
      // 更新本地存储
      const currentUser = authService.getLocalUser();
      if (currentUser) {
        const newUser = { ...currentUser, ...updatedUser };
        localStorage.setItem('user', JSON.stringify(newUser));
      }
      return updatedUser;
    } catch (error: any) {
      return rejectWithValue(error.message || '更新用户信息失败');
    }
  }
);

export const refreshToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { rejectWithValue }) => {
    try {
      const data = await authService.refreshToken();
      localStorage.setItem('access_token', data.access_token);
      return data;
    } catch (error: any) {
      // Token刷新失败，清除认证信息
      authService.clearAuthData();
      return rejectWithValue(error.message || 'Token刷新失败');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    updateUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      localStorage.setItem('user', JSON.stringify(action.payload));
    },
    updatePermissions: (state, action: PayloadAction<string[]>) => {
      state.permissions = action.payload;
      localStorage.setItem('permissions', JSON.stringify(action.payload));
    },
  },
  extraReducers: (builder) => {
    builder
      // 登录
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action: PayloadAction<AuthResponse>) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.permissions = action.payload.permissions;
        state.error = null;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.permissions = [];
        state.error = action.payload as string;
      })
      // 登出
      .addCase(logout.fulfilled, (state) => {
        state.isAuthenticated = false;
        state.user = null;
        state.permissions = [];
        state.error = null;
      })
      // 获取当前用户
      .addCase(getCurrentUser.pending, (state) => {
        state.loading = true;
      })
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.permissions = action.payload.permissions;
        state.isAuthenticated = true;
      })
      .addCase(getCurrentUser.rejected, (state, action) => {
        state.loading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.permissions = [];
        state.error = action.payload as string;
      })
      // 更新用户信息
      .addCase(updateUserInfo.fulfilled, (state, action) => {
        state.user = action.payload;
        state.loading = false;
      })
      .addCase(updateUserInfo.rejected, (state, action) => {
        state.error = action.payload as string;
        state.loading = false;
      })
      // 刷新Token
      .addCase(refreshToken.rejected, (state, action) => {
        state.isAuthenticated = false;
        state.user = null;
        state.permissions = [];
        state.error = action.payload as string;
      });
  },
});

export const { clearError, updateUser, updatePermissions } = authSlice.actions;
export default authSlice.reducer;