import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Material } from '@/types';

interface MaterialState {
  materials: Material[];
  currentMaterial: Material | null;
  loading: boolean;
  error: string | null;
}

const initialState: MaterialState = {
  materials: [],
  currentMaterial: null,
  loading: false,
  error: null,
};

const materialSlice = createSlice({
  name: 'material',
  initialState,
  reducers: {
    setMaterials: (state, action: PayloadAction<Material[]>) => {
      state.materials = action.payload;
    },
    setCurrentMaterial: (state, action: PayloadAction<Material | null>) => {
      state.currentMaterial = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const { setMaterials, setCurrentMaterial, setLoading, setError } = materialSlice.actions;
export default materialSlice.reducer;