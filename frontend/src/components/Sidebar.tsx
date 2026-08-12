import React from 'react';
import { Terminal, Database, Activity, Settings } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const navItems = [
    { id: '/', icon: Terminal, label: 'Terminal' },
    { id: '/memory', icon: Database, label: 'Memory' },
    { id: '/diagnostics', icon: Activity, label: 'Diagnostics' },
    { id: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="w-56 bg-[#050505] flex flex-col h-screen py-8">
      {/* Title */}
      <div className="px-8 mb-12">
        <h1 className="text-xl font-light tracking-[0.25em] text-[#e5e7eb]">J.A.R.V.I.S.</h1>
      </div>

      {/* Navigation */}
      <div className="flex-1 px-4 space-y-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.id || (item.id !== '/' && location.pathname.startsWith(item.id));
          return (
            <button
              key={item.id}
              onClick={() => navigate(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-all ${
                isActive
                  ? 'border border-[#10b981]/50 bg-[#10b981]/10 text-[#10b981]'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/5'
              }`}
            >
              <item.icon size={18} className={isActive ? 'text-[#10b981]' : ''} />
              <span className="font-medium tracking-wide">{item.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
