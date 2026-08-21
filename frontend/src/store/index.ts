import { configureStore } from '@reduxjs/toolkit';
import authSlice from './slices/authSlice';
import bomSlice from './slices/bomSlice';
import materialSlice from './slices/materialSlice';
import supplierSlice from './slices/supplierSlice';
import uiSlice from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    bom: bomSlice,
    material: materialSlice,
    supplier: supplierSlice,
    ui: uiSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;