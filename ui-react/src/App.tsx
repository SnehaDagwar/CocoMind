
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { Dashboard } from './pages/Dashboard';
import { HITLReview, RTIExport, AuditChain } from './pages/Placeholders';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="hitl" element={<HITLReview />} />
          <Route path="rti" element={<RTIExport />} />
          <Route path="audit" element={<AuditChain />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
