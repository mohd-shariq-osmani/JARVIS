import React from 'react';
import { MapPin, Cloud, Clock, ShieldAlert } from 'lucide-react';

export const BottomBar: React.FC = () => {
  return (
    <div className="h-12 bg-[#050508] border-t border-zinc-800/50 flex items-center justify-between px-6">
      
      {/* Left items */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-zinc-400">
          <MapPin size={14} className="text-purple-500" />
          <span className="text-xs tracking-wider">NEW YORK, USA</span>
        </div>
        
        <div className="flex items-center gap-2 text-zinc-400">
          <Cloud size={14} className="text-purple-500" />
          <span className="text-xs tracking-wider">18°C, PARTLY CLOUDY</span>
        </div>
      </div>

      {/* Middle soundwave mockup */}
      <div className="flex-1 flex justify-center items-center gap-0.5 px-10 h-full opacity-30 pointer-events-none">
        {Array.from({ length: 40 }).map((_, i) => (
          <div 
            key={i} 
            className="w-1 bg-purple-500 rounded-full animate-pulse"
            style={{ 
              height: `${Math.max(4, Math.random() * 24)}px`,
              animationDelay: `${Math.random() * 2}s`,
              animationDuration: `${0.5 + Math.random()}s`
            }}
          />
        ))}
      </div>

      {/* Right items */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-zinc-400">
          <Clock size={14} className="text-purple-500" />
          <span className="text-xs tracking-wider uppercase">Uptime: 24h 12m</span>
        </div>

        <div className="flex items-center gap-2 text-zinc-400 pl-6 border-l border-zinc-800/80">
          <ShieldAlert size={14} className="text-purple-500" />
          <span className="text-xs tracking-wider text-purple-400">V 3.1 PRO</span>
        </div>
      </div>
      
    </div>
  );
};
