import React from 'react';
import { ShieldAlert, Check, X } from 'lucide-react';

export interface AccessRequestData {
  id: string;
  action: string;
  resource: string;
  reason: string;
}

interface AccessModalProps {
  request: AccessRequestData | null;
  onRespond: (requestId: string, grant: boolean) => void;
}

export const AccessModal: React.FC<AccessModalProps> = ({ request, onRespond }) => {
  if (!request) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-md bg-[#0c1017] border border-[#ff3b30]/60 rounded-xl shadow-[0_0_50px_rgba(255,59,48,0.25)] p-6 overflow-hidden">
        {/* Sci-Fi Top Accent Line */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#ff3b30] to-transparent animate-pulse" />

        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-[#ff3b30]/10 border border-[#ff3b30]/40 text-[#ff3b30]">
            <ShieldAlert size={22} className="animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-mono tracking-widest text-[#ff3b30] uppercase font-bold">
              Access Authorization Required
            </h3>
            <p className="text-xs text-white/50 font-mono">JARVIS Security Protocol</p>
          </div>
        </div>

        {/* Request Details */}
        <div className="bg-black/40 border border-white/10 rounded-lg p-4 mb-6 space-y-2">
          <div>
            <span className="text-[10px] tracking-wider uppercase font-mono text-white/40 block">Action</span>
            <span className="text-sm text-white font-medium">{request.action}</span>
          </div>
          <div>
            <span className="text-[10px] tracking-wider uppercase font-mono text-white/40 block">Target Resource</span>
            <span className="text-xs text-[#00f2fe] font-mono">{request.resource}</span>
          </div>
          <div>
            <span className="text-[10px] tracking-wider uppercase font-mono text-white/40 block">Reason</span>
            <span className="text-xs text-white/70">{request.reason}</span>
          </div>
        </div>

        <p className="text-[11px] text-center text-white/40 font-mono mb-4">
          You can also speak: <span className="text-white font-semibold">"Grant access"</span> or <span className="text-white font-semibold">"Deny"</span>
        </p>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => onRespond(request.id, false)}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-white/5 hover:bg-white/10 border border-white/20 text-white/80 font-mono text-xs tracking-wider transition-all duration-200"
          >
            <X size={14} />
            DENY
          </button>
          <button
            onClick={() => onRespond(request.id, true)}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-[#00f2fe]/20 hover:bg-[#00f2fe]/30 border border-[#00f2fe] text-[#00f2fe] font-mono text-xs font-semibold tracking-wider shadow-[0_0_15px_rgba(0,242,254,0.3)] transition-all duration-200"
          >
            <Check size={14} />
            GRANT ACCESS
          </button>
        </div>
      </div>
    </div>
  );
};
