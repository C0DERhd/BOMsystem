import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { BOM } from '@/types';

interface BOMState {
  boms: BOM[];
  currentBOM: BOM | null;
  loading: boolean;
  error: string | null;
}

const initialState: BOMState = {
  boms: [],
  currentBOM: null,
  loading: false,
  error: null,
};

const bomSlice = createSlice({
  name: 'bom',
  initialState,
  reducers: {
    setBOMs: (state, action: PayloadAction<BOM[]>) => {
      state.boms = action.payload;
    },
    setCurrentBOM: (state, action: PayloadAction<BOM | null>) => {
      state.currentBOM = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const { setBOMs, setCurrentBOM, setLoading, setError } = bomSlice.actions;
export default bomSlice.reducer;