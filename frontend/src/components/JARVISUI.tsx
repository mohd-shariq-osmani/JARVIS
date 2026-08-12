import React, { useState, useEffect } from 'react';

const JARVISUI: React.FC = () => {
  const [status, setStatus] = useState('READY');
  const [voiceState, setVoiceState] = useState('LISTENING');
  const [cpu, setCpu] = useState('0.0%');
  const [ram, setRam] = useState('0.0%');
  const [transcript, setTranscript] = useState("Wi-Fi has been turned off.");
  const [response, setResponse] = useState("How may I assist you?");
  const [input, setInput] = useState('');

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
    <div className="flex flex-col items-center min-h-screen bg-[#0a0a0c] text-white font-sans overflow-hidden p-6 selection:bg-[#10b981]/30 relative">
       
       <div className="flex flex-col items-center w-full max-w-3xl flex-1 pt-16 relative">
         
         {/* Title */}
         <h1 className="text-5xl font-extralight tracking-[0.4em] mb-8 text-[#f3f4f6] relative">
           JARVIS
           {/* Tiny blinking cursor effect over R? */}
         </h1>
         
         {/* Ready Indicator */}
         <div className="flex items-center space-x-2 mb-8">
           <div className={`w-2.5 h-2.5 rounded-full ${status === 'READY' ? 'bg-[#10b981] shadow-[0_0_8px_rgba(16,185,129,0.8)]' : 'bg-red-500'}`}></div>
           <span className="font-semibold tracking-[0.2em] text-xs text-[#9ca3af]">{status}</span>
         </div>

         {/* Telemetry */}
         <div className="flex space-x-4 mb-10">
           <div className="px-4 py-1.5 rounded-full bg-[#111113] border border-[#1f2124] flex items-center space-x-2">
             <span className="text-[10px] font-semibold text-[#6b7280]">CPU</span>
             <span className="text-[10px] font-bold text-[#10b981]">{cpu}</span>
           </div>
           <div className="px-4 py-1.5 rounded-full bg-[#111113] border border-[#1f2124] flex items-center space-x-2">
             <span className="text-[10px] font-semibold text-[#6b7280]">RAM</span>
             <span className="text-[10px] font-bold text-[#10b981]">{ram}</span>
           </div>
         </div>

         {/* Voice State Pill */}
         {voiceState !== 'SLEEPING' && (
           <div className="px-6 py-1.5 rounded-full border border-[#064e3b] text-[#10b981] font-semibold tracking-widest text-[11px] mb-12 bg-[#022c22]/50 shadow-[0_0_15px_rgba(6,78,59,0.5)]">
             {voiceState}
           </div>
         )}
         
         {voiceState === 'SLEEPING' && (
           <div className="px-6 py-1.5 rounded-full border border-[#1f2124] text-[#6b7280] font-semibold tracking-widest text-[11px] mb-12 bg-[#111113]">
             SLEEPING
           </div>
         )}

         {/* Transcript */}
         {transcript && (
           <p className="text-[15px] text-center text-[#d1d5db] font-serif italic max-w-xl mb-32 font-light">
             "{transcript}"
           </p>
         )}

         {/* Response */}
         {response && (
           <p className="text-[17px] text-center text-[#9ca3af] font-serif italic max-w-2xl font-light">
             "{response}"
           </p>
         )}
       </div>

       {/* Input Box Area */}
       <div className="w-full max-w-3xl pb-6">
         <form onSubmit={sendMessage} className="w-full">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              className="w-full bg-[#0d0d0f] border border-[#1f2124] rounded-xl px-5 py-3 text-sm text-[#d1d5db] outline-none focus:border-[#10b981]/50 transition-colors shadow-inner"
              placeholder=""
            />
         </form>
       </div>
    </div>
  )
}

export default JARVISUI;
