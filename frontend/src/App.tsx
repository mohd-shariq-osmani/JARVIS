import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Settings from './pages/Settings';
import Diagnostics from './pages/Diagnostics';
import Memory from './pages/Memory';

function App() {
  const [status, setStatus] = useState<string>("CONNECTING");

  useEffect(() => {
    fetch('http://127.0.0.1:8000/health')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setStatus("READY");
        }
      })
      .catch(err => {
        setStatus("BACKEND OFFLINE");
        console.error("Backend connection failed:", err);
      });
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="settings" element={<Settings />} />
          <Route path="diagnostics" element={<Diagnostics />} />
          <Route path="memory" element={<Memory />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
