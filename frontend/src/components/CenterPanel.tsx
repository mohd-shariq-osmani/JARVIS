import React, { useState, useEffect } from 'react';
import { Mic, Send, Search, Calendar, FileText, Activity, BrainCircuit } from 'lucide-react';

interface CenterPanelProps {
  status?: string;
}

export const CenterPanel: React.FC<CenterPanelProps> = ({ status = 'READY' }) => {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [voiceState, setVoiceState] = useState<string>('SLEEPING');
  const [voiceTranscript, setVoiceTranscript] = useState<string>('');

  useEffect(() => {
    const voiceWs = new WebSocket('ws://127.0.0.1:8000/ws/voice');
    voiceWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.state) setVoiceState(data.state);
        if (data.transcript) setVoiceTranscript(data.transcript);
        if (data.state === 'SLEEPING') setVoiceTranscript('');
      } catch (e) {
        console.error("Failed to parse voice state:", e);
      }
    };
    return () => voiceWs.close();
  }, []);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    // Minimal mock for now as we don't have the full message list rendering here yet.
    // Real implementation would append to a messages array.
    setInput('');
    setIsLoading(true);
    try {
      await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input.trim() })
      });
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 relative overflow-hidden bg-[#050508]">
      
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-purple-500/5 rounded-full blur-[100px] pointer-events-none"></div>

      {/* Main Graphic */}
      <div className="relative flex flex-col items-center justify-center mb-16">
        
        {/* Outer dotted rings */}
        <div className="absolute w-[300px] h-[300px] rounded-full border border-purple-500/20 border-dashed animate-[spin_20s_linear_infinite]"></div>
        <div className="absolute w-[260px] h-[260px] rounded-full border border-purple-500/30 border-dashed animate-[spin_15s_linear_infinite_reverse]"></div>
        
        {/* Inner solid rings with glow */}
        <div className="absolute w-[220px] h-[220px] rounded-full border border-purple-500/40 shadow-[0_0_30px_rgba(168,85,247,0.2)]"></div>
        <div className="absolute w-[180px] h-[180px] rounded-full border-2 border-purple-400 shadow-[inset_0_0_20px_rgba(168,85,247,0.5),0_0_20px_rgba(168,85,247,0.5)]"></div>
        
        {/* Core center */}
        <div className="w-[120px] h-[120px] bg-purple-950/50 backdrop-blur-md rounded-full border border-purple-400/50 flex flex-col items-center justify-center shadow-[inset_0_0_30px_rgba(168,85,247,0.8),0_0_50px_rgba(168,85,247,0.4)] z-10">
          <div className="w-16 h-16 bg-purple-500 rounded-full animate-pulse blur-[8px] absolute"></div>
          <span className="relative text-white font-bold tracking-widest text-lg z-20">JARVIS</span>
        </div>
      </div>

      <div className="text-center mb-10 z-10 min-h-[4rem]">
        {voiceState !== 'SLEEPING' ? (
          <div className="flex flex-col items-center animate-fade-in">
            <div className={`px-4 py-1 rounded-full border text-xs font-mono tracking-widest mb-2 ${
              voiceState === 'LISTENING' ? 'border-purple-500/50 text-purple-400 animate-pulse bg-purple-950/30' :
              voiceState === 'PROCESSING' ? 'border-amber-500/50 text-amber-400 animate-pulse bg-amber-950/30' :
              'border-blue-500/50 text-blue-400 animate-pulse bg-blue-950/30'
            }`}>
              {voiceState}
            </div>
            {voiceTranscript && (
              <div className="text-lg text-zinc-300 italic max-w-md text-center">
                "{voiceTranscript}"
              </div>
            )}
          </div>
        ) : (
          <>
            <h2 className="text-2xl font-light text-zinc-100 tracking-wide">Good evening, <span className="font-semibold text-white">Sir</span>.</h2>
            <p className="text-zinc-400 mt-2">All systems operating at normal parameters.</p>
          </>
        )}
      </div>

      {/* Input Area */}
      <form onSubmit={sendMessage} className="w-full max-w-2xl relative z-10">
        <div className="relative group">
          <div className="absolute inset-0 bg-purple-500/20 rounded-2xl blur-xl transition-all duration-500 group-hover:bg-purple-500/30 group-hover:blur-2xl"></div>
          <div className="relative bg-[#0a0a0f] border border-purple-500/30 rounded-2xl p-2 flex items-center shadow-[0_0_15px_rgba(168,85,247,0.15)]">
            <button className="p-3 text-zinc-400 hover:text-purple-400 transition-colors bg-zinc-900 rounded-xl mr-2 border border-zinc-800">
              <Mic size={20} />
            </button>
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="How may I assist you?" 
              className="flex-1 bg-transparent border-none outline-none text-zinc-100 placeholder-zinc-500 text-lg px-2"
              disabled={isLoading || status !== 'READY'}
            />
            <button 
              type="submit"
              disabled={isLoading}
              className="p-3 text-purple-400 hover:text-purple-300 transition-colors bg-purple-500/10 hover:bg-purple-500/20 rounded-xl ml-2 border border-purple-500/30"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </form>

      {/* Quick Actions & Cards */}
      <div className="w-full max-w-3xl grid grid-cols-2 gap-4 mt-12 z-10">
        
        {/* Memory Card */}
        <div className="bg-[#0a0a0f] border border-zinc-800/80 rounded-xl p-5 hover:border-purple-500/30 transition-colors cursor-pointer group">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
              <BrainCircuit size={18} />
            </div>
            <h4 className="text-sm font-semibold text-zinc-200 tracking-wide">MEMORY RECALL</h4>
          </div>
          <p className="text-xs text-zinc-400 mb-4 line-clamp-2">"You mentioned you wanted to review the Q3 architecture document before the meeting tomorrow."</p>
          <div className="flex justify-between items-center text-xs">
            <span className="text-zinc-600">Saved 2 hours ago</span>
            <span className="text-purple-400 group-hover:underline">Open Note</span>
          </div>
        </div>

        {/* Quick Actions Grid */}
        <div className="grid grid-cols-2 gap-3">
          <button className="flex flex-col items-center justify-center p-4 bg-[#0a0a0f] border border-zinc-800/80 rounded-xl hover:border-purple-500/30 hover:bg-purple-500/5 transition-all text-zinc-400 hover:text-purple-400 group">
            <Search size={20} className="mb-2" />
            <span className="text-xs tracking-wider">Search Web</span>
          </button>
          <button className="flex flex-col items-center justify-center p-4 bg-[#0a0a0f] border border-zinc-800/80 rounded-xl hover:border-purple-500/30 hover:bg-purple-500/5 transition-all text-zinc-400 hover:text-purple-400 group">
            <Calendar size={20} className="mb-2" />
            <span className="text-xs tracking-wider">Calendar</span>
          </button>
          <button className="flex flex-col items-center justify-center p-4 bg-[#0a0a0f] border border-zinc-800/80 rounded-xl hover:border-purple-500/30 hover:bg-purple-500/5 transition-all text-zinc-400 hover:text-purple-400 group">
            <FileText size={20} className="mb-2" />
            <span className="text-xs tracking-wider">Summarize</span>
          </button>
          <button className="flex flex-col items-center justify-center p-4 bg-[#0a0a0f] border border-zinc-800/80 rounded-xl hover:border-purple-500/30 hover:bg-purple-500/5 transition-all text-zinc-400 hover:text-purple-400 group">
            <Activity size={20} className="mb-2" />
            <span className="text-xs tracking-wider">System Info</span>
          </button>
        </div>

      </div>

    </div>
  );
};
