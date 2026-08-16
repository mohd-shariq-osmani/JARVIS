import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Settings from './pages/Settings';
import Diagnostics from './pages/Diagnostics';
import Memory from './pages/Memory';
import Tasks from './pages/Tasks';

function App() {
  useEffect(() => {
    fetch('http://127.0.0.1:8000/health')
      .catch(err => {
        console.error("Backend connection failed:", err);
      });
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="settings" element={<Settings />} />
          <Route path="diagnostics" element={<Diagnostics />} />
          <Route path="memory" element={<Memory />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
