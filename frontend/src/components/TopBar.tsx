import React, { useState, useEffect } from 'react';
import { TerminalSquare, Bell } from 'lucide-react';

export const TopBar: React.FC = () => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="h-20 flex items-center justify-between px-8 bg-[#050508] border-b border-zinc-800/50">
      {/* Status */}
      <div className="flex items-center gap-3">
        <div className="relative flex items-center justify-center w-3 h-3">
          <div className="absolute w-full h-full bg-purple-500 rounded-full animate-ping opacity-75"></div>
          <div className="relative w-2 h-2 bg-purple-500 rounded-full"></div>
        </div>
        <span className="text-zinc-300 font-medium text-sm tracking-wide">JARVIS <span className="text-purple-500">Online</span></span>
      </div>

      {/* Center Time/Date */}
      <div className="flex flex-col items-center">
        <span className="text-xl font-light tracking-wider text-zinc-100">
          {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
        <span className="text-xs text-zinc-400 tracking-widest mt-1">
          {time.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
        </span>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-6">
        <button className="text-zinc-400 hover:text-purple-400 transition-colors">
          <TerminalSquare size={20} />
        </button>
        <button className="text-zinc-400 hover:text-purple-400 transition-colors relative">
          <Bell size={20} />
          <div className="absolute -top-1 -right-1 w-2 h-2 bg-purple-500 rounded-full"></div>
        </button>
        
        {/* Profile / Core badge */}
        <div className="flex items-center gap-3 pl-4 border-l border-zinc-800/80">
          <div className="relative w-10 h-10 rounded-full border border-purple-500 flex items-center justify-center bg-purple-500/10 shadow-[0_0_10px_rgba(168,85,247,0.3)]">
            <span className="text-xs font-bold text-purple-400">100%</span>
            <div className="absolute inset-0 rounded-full border-t-2 border-purple-400 animate-[spin_4s_linear_infinite]"></div>
          </div>
          <span className="text-xs font-bold tracking-widest text-zinc-300">JARVIS CORE</span>
        </div>
      </div>
    </div>
  );
};
