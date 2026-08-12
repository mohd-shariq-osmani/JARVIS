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
    <div className="w-56 bg-[#050505] flex flex-col h-screen py-10 relative">
      {/* Title */}
      <div className="px-8 mb-14">
        <h1 className="text-xl font-outfit font-light tracking-[0.3em] text-[#e5e7eb]">J.A.R.V.I.S.</h1>
      </div>

      {/* Navigation */}
      <div className="flex-1 px-4 space-y-3">
        {navItems.map((item) => {
          const isActive = location.pathname === item.id || (item.id !== '/' && location.pathname.startsWith(item.id));
          return (
            <button
              key={item.id}
              onClick={() => navigate(item.id)}
              className={`w-full flex items-center gap-4 px-5 py-3.5 rounded-xl text-sm transition-all duration-300 relative group overflow-hidden ${
                isActive
                  ? 'text-[#10b981] bg-gradient-to-r from-[#10b981]/10 to-transparent'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/5'
              }`}
            >
              {isActive && (
                <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[#10b981] rounded-r-full shadow-[0_0_10px_#10b981]"></div>
              )}
              <item.icon size={18} className={`transition-transform duration-300 ${isActive ? 'text-[#10b981] scale-110' : 'group-hover:scale-110'}`} />
              <span className={`font-medium tracking-wide transition-all ${isActive ? 'font-semibold' : ''}`}>{item.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
