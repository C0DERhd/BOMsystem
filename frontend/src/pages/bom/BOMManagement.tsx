import React from 'react';
import { Navigate, Routes, Route } from 'react-router-dom';

import { usePermissions } from '@/hooks/usePermissions';

import BOMDetail from './BOMDetail';
import BOMEditor from './BOMEditor';
import BOMList from './BOMList';

const BOMManagement: React.FC = () => {
  const { isAdmin } = usePermissions();
  const editorElement = isAdmin() ? <BOMEditor /> : <Navigate to="/bom" replace />;

  return (
    <Routes>
      <Route index element={<BOMList />} />
      <Route path="create" element={editorElement} />
      <Route path=":id" element={<BOMDetail />} />
      <Route path=":id/edit" element={editorElement} />
    </Routes>
  );
};

export default BOMManagement;
