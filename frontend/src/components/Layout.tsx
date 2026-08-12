import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

const Layout: React.FC = () => {
  return (
    <div className="flex h-screen bg-[#050505] text-white font-sans overflow-hidden">
      <Sidebar />
      <div className="flex-1 p-6 flex flex-col min-w-0 bg-[#050505]">
        <main className="flex-1 flex flex-col bg-[#0f1013] rounded-2xl border border-white/5 relative overflow-hidden shadow-2xl">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
