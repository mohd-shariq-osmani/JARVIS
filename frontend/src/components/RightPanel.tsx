import React from 'react';
import { Calendar, CheckCircle2, Smartphone, Monitor, Watch, Server } from 'lucide-react';

export const RightPanel: React.FC = () => {
  return (
    <div className="w-80 bg-[#0a0a0f] border-l border-zinc-800/50 flex flex-col h-full overflow-y-auto">
      
      {/* Upcoming Events */}
      <div className="p-6 border-b border-zinc-800/50">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-zinc-300 tracking-wider">UPCOMING EVENTS</h3>
          <Calendar size={16} className="text-purple-500" />
        </div>
        
        <div className="space-y-4">
          <div className="relative pl-4 border-l-2 border-purple-500">
            <div className="absolute w-2 h-2 bg-purple-500 rounded-full -left-[5px] top-1.5"></div>
            <div className="text-sm text-zinc-200">Team Sync</div>
            <div className="text-xs text-zinc-500 mt-1">10:00 AM - 11:00 AM</div>
          </div>
          
          <div className="relative pl-4 border-l-2 border-zinc-700">
            <div className="absolute w-2 h-2 bg-zinc-700 rounded-full -left-[5px] top-1.5"></div>
            <div className="text-sm text-zinc-400">Project Review</div>
            <div className="text-xs text-zinc-600 mt-1">2:00 PM - 3:30 PM</div>
          </div>
        </div>
      </div>

      {/* Active Tasks */}
      <div className="p-6 border-b border-zinc-800/50">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-zinc-300 tracking-wider">ACTIVE TASKS</h3>
          <CheckCircle2 size={16} className="text-purple-500" />
        </div>

        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-xs mb-1.5">
              <span className="text-zinc-400">System Backup</span>
              <span className="text-purple-400">75%</span>
            </div>
            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-purple-500 w-3/4 shadow-[0_0_8px_rgba(168,85,247,0.6)]"></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1.5">
              <span className="text-zinc-400">Model Fine-tuning</span>
              <span className="text-blue-400">42%</span>
            </div>
            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 w-[42%] shadow-[0_0_8px_rgba(59,130,246,0.6)]"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Connected Devices */}
      <div className="p-6 flex-1">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-zinc-300 tracking-wider">CONNECTED DEVICES</h3>
          <Monitor size={16} className="text-purple-500" />
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-zinc-800/50">
            <div className="flex items-center gap-3">
              <Server size={16} className="text-zinc-400" />
              <span className="text-sm text-zinc-300">Local Node</span>
            </div>
            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_5px_rgba(16,185,129,0.8)]"></div>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-zinc-800/50">
            <div className="flex items-center gap-3">
              <Smartphone size={16} className="text-zinc-400" />
              <span className="text-sm text-zinc-300">iPhone 15 Pro</span>
            </div>
            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_5px_rgba(16,185,129,0.8)]"></div>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-zinc-800/50 opacity-60">
            <div className="flex items-center gap-3">
              <Watch size={16} className="text-zinc-500" />
              <span className="text-sm text-zinc-500">Apple Watch</span>
            </div>
            <div className="w-2 h-2 rounded-full bg-zinc-600"></div>
          </div>
        </div>
      </div>

    </div>
  );
};
