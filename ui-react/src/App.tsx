import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { getStoredUser } from './api';
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import { TenderWorkspace } from './pages/TenderWorkspace';
import { AuditChain, HITLReview, RTIExport } from './pages/Placeholders';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="tenders/:tenderId" element={<TenderWorkspace />} />
          <Route path="hitl" element={<HITLReview />} />
          <Route path="rti" element={<RTIExport />} />
          <Route path="audit" element={<AuditChain />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

function ProtectedLayout() {
  if (!getStoredUser()) {
    return <Navigate to="/login" replace />;
  }
  return <Layout />;
}

export default App;
