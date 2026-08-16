import React, { useState, useEffect, useRef } from 'react';
import { Square, ArrowUp } from 'lucide-react';
import { AccessModal, type AccessRequestData } from './AccessModal';

interface LogMessage {
  id: string;
  role: 'user' | 'jarvis';
  text: string;
}

const Dashboard: React.FC = () => {
  const [voiceState, setVoiceState] = useState<'SLEEPING' | 'LISTENING' | 'PROCESSING' | 'SPEAKING' | 'QUEUED'>('SLEEPING');
  const [cpu, setCpu] = useState('5.7%');
  const [ram, setRam] = useState('75.4%');
  const [clock, setClock] = useState('00:00:00');
  const [queueCount, setQueueCount] = useState(0);
  const [input, setInput] = useState('');
  const [isInputFocused, setIsInputFocused] = useState(false);
  const [accessRequest, setAccessRequest] = useState<AccessRequestData | null>(null);
  const [logs, setLogs] = useState<LogMessage[]>([
    { id: '1', role: 'jarvis', text: 'All systems online. How may I assist you, sir?' }
  ]);

  const inputRef = useRef<HTMLInputElement>(null);

  // Live Clock
  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setClock(d.toLocaleTimeString('en-GB', { hour12: false }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // WebSockets for Telemetry and Voice
  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8000/ws/telemetry');
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.cpu) setCpu(`${data.cpu.toFixed(1)}%`);
        if (data.ram) setRam(`${data.ram.percent.toFixed(1)}%`);
      } catch (err) {}
    };

    const voiceWs = new WebSocket('ws://127.0.0.1:8000/ws/voice');
    voiceWs.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.state) {
          const rawState = data.state.toUpperCase();
          if (['SLEEPING', 'LISTENING', 'PROCESSING', 'SPEAKING', 'QUEUED'].includes(rawState)) {
            setVoiceState(rawState as any);
          }
          if (rawState === 'READY' || rawState === 'SLEEPING' || rawState === 'LISTENING') {
            setQueueCount(0);
          }
        }
        if (data.queue_size !== undefined) {
          setQueueCount(data.queue_size);
        }

        if (data.type === 'ACCESS_REQUEST' || data.state === 'ACCESS_REQUEST') {
          const req = data.payload || data;
          if (req.id && req.action) {
            setAccessRequest(req);
          }
        }

        if (data.transcript) {
          const text = data.transcript.trim();
          if (text && !text.startsWith('JARVIS activated.')) {
            if (data.state === 'SPEAKING' || data.state === 'READY') {
              setLogs(prev => {
                const next = [...prev, { id: String(Date.now()), role: 'jarvis' as const, text }];
                return next.slice(-4);
              });
            } else if (data.state === 'PROCESSING' || data.state === 'QUEUED') {
              setLogs(prev => {
                const next = [...prev, { id: String(Date.now()), role: 'user' as const, text }];
                return next.slice(-4);
              });
            }
          }
        }
      } catch (err) {}
    };

    return () => {
      ws.close();
      voiceWs.close();
    };
  }, []);

  const handleAccessResponse = async (requestId: string, grant: boolean) => {
    setAccessRequest(null);
    try {
      await fetch('http://127.0.0.1:8000/api/access/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: requestId, grant })
      });
    } catch (err) {
      console.error('Failed to respond to access request:', err);
    }
  };

  const sendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setInput('');
    
    // Add to logs immediately
    setLogs(prev => {
      const next = [...prev, { id: String(Date.now()), role: 'user' as const, text: userMsg }];
      return next.slice(-4);
    });

    try {
      await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
    } catch (err) {
      console.error(err);
    }
  };

  const stopJarvis = async () => {
    try {
      await fetch('http://127.0.0.1:8000/chat/stop', { method: 'POST' });
      setVoiceState('SLEEPING');
      setQueueCount(0);
      setLogs(prev => [...prev, { id: String(Date.now()), role: 'jarvis' as const, text: '[Halted]' }].slice(-4));
    } catch (err) {
      console.error('Stop request failed:', err);
    }
  };

  const handleCoreClick = () => {
    if (isBusy) {
      stopJarvis();
    } else {
      inputRef.current?.focus();
    }
  };

  const isBusy = voiceState === 'SPEAKING' || voiceState === 'PROCESSING' || voiceState === 'QUEUED';
  const isListening = voiceState === 'LISTENING';
  const isProcessing = voiceState === 'PROCESSING';

  // Map state to css class
  const stateClass = 
    voiceState === 'LISTENING' ? 'state-listening' :
    voiceState === 'PROCESSING' || voiceState === 'QUEUED' ? 'state-processing' :
    voiceState === 'SPEAKING' ? 'state-speaking' : 'state-idle';

  // Status label text
  const statusLabel = 
    voiceState === 'LISTENING' ? 'Listening' :
    voiceState === 'PROCESSING' ? (queueCount > 0 ? `Processing (${queueCount} queued)` : 'Processing') :
    voiceState === 'SPEAKING' ? 'Responding' :
    voiceState === 'QUEUED' ? `Queued (${queueCount})` : 'Standing By';

  return (
    <div className={`relative w-full h-full flex flex-col justify-between p-6 sm:p-10 bg-[#08090a] overflow-hidden select-none ${stateClass}`}>
      
      {/* Background Radial Glow & Faint Scanlines */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_120%_80%_at_50%_20%,rgba(255,255,255,0.03),transparent_60%)] pointer-events-none" />
      <div 
        className="absolute inset-0 pointer-events-none opacity-40"
        style={{
          background: 'repeating-linear-gradient(to bottom, rgba(255,255,255,0.012) 0px, rgba(255,255,255,0.012) 1px, transparent 1px, transparent 3px)'
        }}
      />

      {/* Corner Brackets */}
      <div className={`absolute top-6 left-6 w-7 h-7 border-t border-l transition-colors duration-700 pointer-events-none ${isListening ? 'border-[#b9e4ff]/60' : 'border-white/10'}`} />
      <div className={`absolute top-6 right-6 w-7 h-7 border-t border-r transition-colors duration-700 pointer-events-none ${isListening ? 'border-[#b9e4ff]/60' : 'border-white/10'}`} />
      <div className={`absolute bottom-6 left-6 w-7 h-7 border-b border-l transition-colors duration-700 pointer-events-none ${isListening ? 'border-[#b9e4ff]/60' : 'border-white/10'}`} />
      <div className={`absolute bottom-6 right-6 w-7 h-7 border-b border-r transition-colors duration-700 pointer-events-none ${isListening ? 'border-[#b9e4ff]/60' : 'border-white/10'}`} />

      {/* Top Header */}
      <header className="relative z-10 flex justify-between items-start">
        <div className="flex flex-col gap-1">
          <div className="font-outfit font-semibold text-sm tracking-[0.28em] text-[#f2f2ef] uppercase">
            J · A · R · V · I · S
          </div>
          <div className="font-mono text-[9px] tracking-[0.15em] text-[#74777d] uppercase">
            Autonomous Desktop Assistant
          </div>
        </div>

        {/* Telemetry */}
        <div className="text-right font-mono text-[10.5px] tracking-wide text-[#74777d] flex flex-col gap-1">
          <div className="flex items-center justify-end gap-2.5">
            <span>SYS</span>
            <span className="text-[#c9c9c4] font-semibold">NOMINAL</span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] shadow-[0_0_8px_#10b981]" />
          </div>
          <div className="flex items-center justify-end gap-2.5">
            <span>MIC</span>
            <span className={`font-semibold ${isListening ? 'text-[#b9e4ff]' : 'text-[#c9c9c4]'}`}>
              {isListening ? 'ACTIVE' : 'STANDBY'}
            </span>
            <span className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${isListening ? 'bg-[#b9e4ff] shadow-[0_0_8px_#b9e4ff]' : 'bg-[#3a3c40]'}`} />
          </div>
          <div className="flex items-center justify-end gap-2.5">
            <span>CPU</span>
            <span className="text-[#10b981] font-bold">{cpu}</span>
            <span className="text-zinc-600">|</span>
            <span>RAM</span>
            <span className="text-[#10b981] font-bold">{ram}</span>
          </div>
          <div className="flex items-center justify-end gap-2.5 text-zinc-400 text-[10px]">
            <span>TIME</span>
            <span className="text-zinc-200">{clock}</span>
          </div>
        </div>
      </header>

      {/* Center Voice Interface Core */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center my-4">
        
        {/* Status Indicator Label */}
        <div className="relative mb-8">
          <div className={`font-outfit text-xs sm:text-sm tracking-[0.32em] uppercase font-light transition-all duration-500 ${
            isListening ? 'text-[#b9e4ff] drop-shadow-[0_0_10px_rgba(185,228,255,0.6)]' :
            isProcessing ? 'text-[#f2f2ef] drop-shadow-[0_0_10px_rgba(242,242,239,0.5)]' :
            'text-[#74777d]'
          }`}>
            {statusLabel}
          </div>
        </div>

        {/* Single Unified Concentric Visualizer Core */}
        <div className="relative flex items-center justify-center">
          
          <button
            onClick={handleCoreClick}
            className="jarvis-core-wrap bg-transparent border-0 cursor-pointer outline-none"
            aria-label="JARVIS Core Visualizer"
          >
            {/* 48 Radial Ticks */}
            <div className="jarvis-ticks">
              {Array.from({ length: 48 }).map((_, i) => (
                <div
                  key={i}
                  style={{
                    transform: `rotate(${i * (360 / 48)}deg)`,
                    height: i % 6 === 0 ? '10px' : '6px',
                    opacity: i % 6 === 0 ? 0.9 : 0.4
                  }}
                />
              ))}
            </div>

            {/* Concentric Rings */}
            <div className="jarvis-ring r1" />
            <div className="jarvis-ring r2" />
            <div className="jarvis-ring r3" />

            {/* Center Core Lens */}
            <div className="jarvis-center">
              
              {/* Dynamic 9-Bar Waveform */}
              <div className="jarvis-wave">
                {[
                  { delay: '0.0s', speakH: '14px' },
                  { delay: '0.12s', speakH: '26px' },
                  { delay: '0.24s', speakH: '38px' },
                  { delay: '0.36s', speakH: '22px' },
                  { delay: '0.0s', speakH: '44px' },
                  { delay: '0.36s', speakH: '24px' },
                  { delay: '0.24s', speakH: '36px' },
                  { delay: '0.12s', speakH: '26px' },
                  { delay: '0.0s', speakH: '14px' },
                ].map((bar, idx) => (
                  <span
                    key={idx}
                    style={{
                      animationDelay: bar.delay,
                      height: voiceState === 'SPEAKING' ? bar.speakH : undefined
                    }}
                  />
                ))}
              </div>
            </div>
          </button>
        </div>

        {/* Quick Stop Button / Sub-hint */}
        <div className="mt-8 flex items-center gap-3">
          {isBusy ? (
            <button
              onClick={stopJarvis}
              className="flex items-center gap-2 px-5 py-2 rounded-full bg-red-950/50 border border-red-500/50 text-red-400 text-[10.5px] font-mono font-semibold tracking-[0.2em] hover:bg-red-900/70 hover:border-red-400 hover:text-red-200 transition-all duration-300 shadow-[0_0_20px_rgba(239,68,68,0.25)] cursor-pointer"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>STOP JARVIS</span>
            </button>
          ) : (
            <div className="font-mono text-[9.5px] tracking-[0.16em] text-[#3a3c40] uppercase">
              Click Core or say &quot;JARVIS&quot; — Say &quot;STOP JARVIS&quot; to interrupt
            </div>
          )}
        </div>
      </div>

      {/* Footer Area: Conversation Log & Input Bar */}
      <footer className="relative z-10 flex flex-col gap-4 mt-2">
        
        {/* Activity / Conversation Log (Last 4 Exchanges) */}
        <div className="flex flex-col gap-2 max-h-24 overflow-hidden justify-end">
          {logs.map((log) => (
            <div
              key={log.id}
              className={`flex gap-3 text-xs font-mono tracking-wide log-rise ${
                log.role === 'user' ? 'text-[#c9c9c4]' : 'text-[#f2f2ef]'
              }`}
            >
              <span className={`min-w-16 uppercase text-[10px] tracking-wider font-semibold ${
                log.role === 'user' ? 'text-[#b9e4ff]/80' : 'text-[#74777d]'
              }`}>
                {log.role === 'user' ? 'YOU' : 'JARVIS'}
              </span>
              <span className="leading-relaxed break-words font-light">
                {log.text}
              </span>
            </div>
          ))}
        </div>

        {/* High-Tech Glowing Input Box */}
        <form onSubmit={sendMessage} className="relative w-full group">
          <div className={`absolute -inset-0.5 rounded-xl blur transition duration-500 ${
            isInputFocused 
              ? 'bg-gradient-to-r from-[#b9e4ff]/30 via-white/20 to-[#b9e4ff]/30 opacity-70' 
              : 'bg-white/5 group-hover:opacity-30'
          }`} />
          <div className="relative flex items-center bg-[#050507] border border-white/10 rounded-xl px-4 py-3 transition-all duration-300 focus-within:border-[#b9e4ff]/50 focus-within:bg-[#090a0d]">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onFocus={() => setIsInputFocused(true)}
              onBlur={() => setIsInputFocused(false)}
              className="flex-1 bg-transparent text-sm text-[#f2f2ef] outline-none font-mono tracking-wide placeholder:text-[#74777d] placeholder:text-xs"
              placeholder={isInputFocused ? "" : "Type a command or query (e.g. 'what is the weather in Hyderabad')..."}
            />
            {input.trim() && (
              <button
                type="submit"
                className="ml-2 p-1.5 rounded-lg bg-zinc-800 hover:bg-[#b9e4ff] text-zinc-400 hover:text-black transition-colors cursor-pointer"
                title="Send command"
              >
                <ArrowUp className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>

        {/* Footer Meta Rule */}
        <div className="flex justify-between items-center pt-2 border-t border-white/5 font-mono text-[9px] tracking-[0.14em] text-[#3a3c40] uppercase">
          <span>JARVIS AI CORE — ACTIVE SESSION</span>
          <span>STATE: {voiceState}</span>
        </div>
      </footer>

      {/* Interactive Permission / Access Request Modal */}
      <AccessModal request={accessRequest} onRespond={handleAccessResponse} />
    </div>
  );
};

export default Dashboard;
