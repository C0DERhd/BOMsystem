import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UIState {
  sidebarCollapsed: boolean;
  loading: boolean;
  theme: 'light' | 'dark';
  language: 'zh-CN' | 'en-US';
}

const initialState: UIState = {
  sidebarCollapsed: false,
  loading: false,
  theme: 'light',
  language: 'zh-CN',
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
    },
    setLanguage: (state, action: PayloadAction<'zh-CN' | 'en-US'>) => {
      state.language = action.payload;
    },
  },
});

export const {
  toggleSidebar,
  setSidebarCollapsed,
  setLoading,
  setTheme,
  setLanguage,
} = uiSlice.actions;

export default uiSlice.reducer;