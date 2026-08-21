import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Supplier } from '@/types';

interface SupplierState {
  suppliers: Supplier[];
  currentSupplier: Supplier | null;
  loading: boolean;
  error: string | null;
}

const initialState: SupplierState = {
  suppliers: [],
  currentSupplier: null,
  loading: false,
  error: null,
};

const supplierSlice = createSlice({
  name: 'supplier',
  initialState,
  reducers: {
    setSuppliers: (state, action: PayloadAction<Supplier[]>) => {
      state.suppliers = action.payload;
    },
    setCurrentSupplier: (state, action: PayloadAction<Supplier | null>) => {
      state.currentSupplier = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const { setSuppliers, setCurrentSupplier, setLoading, setError } = supplierSlice.actions;
export default supplierSlice.reducer;