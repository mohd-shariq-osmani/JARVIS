import React, { useState, useEffect } from 'react';

const Dashboard: React.FC = () => {
  const [status, setStatus] = useState('READY');
  const [voiceState, setVoiceState] = useState('SPEAKING');
  const [cpu, setCpu] = useState('5.7%');
  const [ram, setRam] = useState('75.4%');
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("How may I assist you?");
  const [input, setInput] = useState('');
  const [isInputFocused, setIsInputFocused] = useState(false);

  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8000/ws/telemetry');
    ws.onmessage = (e) => {
      try {
         const data = JSON.parse(e.data);
         if (data.cpu) setCpu(`${data.cpu.toFixed(1)}%`);
         if (data.ram) setRam(`${data.ram.percent.toFixed(1)}%`);
      } catch (err) {}
    }

    const voiceWs = new WebSocket('ws://127.0.0.1:8000/ws/voice');
    voiceWs.onmessage = (e) => {
      try {
         const data = JSON.parse(e.data);
         if (data.state) setVoiceState(data.state);
         
         if (data.transcript) {
           if (data.state === 'SPEAKING') {
             setResponse(data.transcript);
           } else {
             setTranscript(data.transcript);
           }
         }
      } catch (err) {}
    }

    return () => {
        ws.close();
        voiceWs.close();
    }
  }, []);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    setTranscript(input.trim());
    setInput('');
    setVoiceState('PROCESSING');
    
    try {
       await fetch('http://127.0.0.1:8000/chat', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ message: input.trim() })
       });
    } catch(err) {
       console.error(err);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center relative w-full h-full p-8 bg-[#0a0a0c] bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-[#111116] via-[#0a0a0c] to-[#0a0a0c]">
       
       <div className="flex flex-col items-center w-full max-w-3xl flex-1 justify-center relative z-10 transition-all duration-700 ease-in-out">
         
         {/* Title */}
         <h1 className="text-[3.5rem] font-outfit font-extralight tracking-[0.5em] mb-8 text-transparent bg-clip-text bg-gradient-to-r from-white via-gray-300 to-gray-500 drop-shadow-lg">
           JARVIS
         </h1>
         
         {/* Ready Indicator */}
         <div className="flex items-center space-x-3 mb-10 bg-black/40 px-4 py-1.5 rounded-full border border-white/5 backdrop-blur-sm">
           <div className={`w-2 h-2 rounded-full ${status === 'READY' ? 'bg-[#10b981] shadow-[0_0_10px_rgba(16,185,129,1)] animate-pulse-slow' : 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,1)]'}`}></div>
           <span className="font-mono font-medium tracking-[0.25em] text-[10px] text-zinc-400">{status}</span>
         </div>

         {/* Telemetry */}
         <div className="flex space-x-4 mb-12">
           <div className="px-6 py-2 rounded-full bg-black/60 border border-white/10 flex items-center space-x-4 shadow-[0_4px_20px_rgba(0,0,0,0.5)] backdrop-blur-md transition-all duration-300 hover:border-white/20 hover:shadow-[0_4px_20px_rgba(16,185,129,0.1)]">
             <span className="text-[10px] font-mono tracking-widest text-zinc-500">CPU</span>
             <span className="text-[11px] font-mono font-bold text-[#10b981]">{cpu}</span>
           </div>
           <div className="px-6 py-2 rounded-full bg-black/60 border border-white/10 flex items-center space-x-4 shadow-[0_4px_20px_rgba(0,0,0,0.5)] backdrop-blur-md transition-all duration-300 hover:border-white/20 hover:shadow-[0_4px_20px_rgba(16,185,129,0.1)]">
             <span className="text-[10px] font-mono tracking-widest text-zinc-500">RAM</span>
             <span className="text-[11px] font-mono font-bold text-[#10b981]">{ram}</span>
           </div>
         </div>

         {/* Voice State Pill */}
         {voiceState !== 'SLEEPING' && (
           <div className={`px-8 py-2 rounded-full border text-[11px] font-mono font-bold tracking-[0.2em] mb-14 transition-all duration-500 shadow-[0_0_20px_rgba(0,0,0,0.3)]
             ${voiceState === 'PROCESSING' ? 'border-[#78350f] text-[#f59e0b] shadow-[0_0_15px_rgba(245,158,11,0.2)] bg-[#78350f]/10' : 
               voiceState === 'LISTENING' ? 'border-[#064e3b] text-[#10b981] shadow-[0_0_15px_rgba(16,185,129,0.2)] bg-[#064e3b]/10 animate-pulse-slow' : 
               'border-[#1e3a8a] text-[#3b82f6] shadow-[0_0_15px_rgba(59,130,246,0.2)] bg-[#1e3a8a]/10'}`}>
             {voiceState}
           </div>
         )}
         
         {voiceState === 'SLEEPING' && (
           <div className="px-8 py-2 rounded-full border border-white/10 text-zinc-600 font-mono font-bold tracking-[0.2em] text-[11px] mb-14 bg-black/30 backdrop-blur-sm">
             SLEEPING
           </div>
         )}

         {/* Transcript */}
         {transcript && (
           <p className="text-[15px] text-center text-zinc-400 font-serif italic max-w-xl mb-4 font-light leading-relaxed tracking-wide transition-opacity duration-500">
             "{transcript}"
           </p>
         )}

         {/* Response */}
         {response && (
           <p className="text-[18px] text-center text-zinc-200 font-serif italic max-w-2xl font-light leading-relaxed tracking-wide transition-opacity duration-500 text-shadow-sm mb-16">
             "{response}"
           </p>
         )}
       </div>

       {/* Input Box Area at the absolute bottom */}
       <div className="w-full absolute bottom-0 left-0 p-8 z-20">
         <form onSubmit={sendMessage} className="w-full max-w-3xl mx-auto relative group">
            <div className={`absolute -inset-0.5 rounded-2xl blur opacity-30 transition duration-500 ${isInputFocused ? 'bg-gradient-to-r from-[#10b981] to-[#3b82f6] opacity-60' : 'bg-white/5 group-hover:opacity-50'}`}></div>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onFocus={() => setIsInputFocused(true)}
              onBlur={() => setIsInputFocused(false)}
              className="relative w-full bg-[#050505] border border-white/10 rounded-2xl px-6 py-4 text-sm text-[#e5e7eb] outline-none font-mono tracking-wide placeholder:text-zinc-700 transition-all duration-300 focus:border-[#10b981]/50 focus:bg-black"
              placeholder={isInputFocused ? "" : "Type a command..."}
            />
         </form>
       </div>
    </div>
  )
}

export default Dashboard;
