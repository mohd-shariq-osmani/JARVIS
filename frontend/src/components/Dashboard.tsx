import React, { useState, useEffect } from 'react';

const Dashboard: React.FC = () => {
  const [status, setStatus] = useState('READY');
  const [voiceState, setVoiceState] = useState('SPEAKING');
  const [cpu, setCpu] = useState('5.7%');
  const [ram, setRam] = useState('75.4%');
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
    <div className="flex-1 flex flex-col items-center justify-center relative w-full h-full p-8 bg-[#0f1013]">
       
       <div className="flex flex-col items-center w-full max-w-3xl flex-1 justify-center relative">
         
         {/* Title */}
         <h1 className="text-[3rem] font-extralight tracking-[0.5em] mb-6 text-[#f3f4f6]">
           JARVIS
         </h1>
         
         {/* Ready Indicator */}
         <div className="flex items-center space-x-3 mb-8">
           <div className={`w-2.5 h-2.5 rounded-full ${status === 'READY' ? 'bg-[#10b981] shadow-[0_0_8px_rgba(16,185,129,0.8)]' : 'bg-red-500'}`}></div>
           <span className="font-semibold tracking-[0.2em] text-[10px] text-zinc-400">{status}</span>
         </div>

         {/* Telemetry */}
         <div className="flex space-x-3 mb-10">
           <div className="px-5 py-1.5 rounded-full bg-[#050505] border border-white/5 flex items-center space-x-3 shadow-inner">
             <span className="text-[10px] font-semibold text-zinc-500">CPU</span>
             <span className="text-[10px] font-bold text-[#10b981]">{cpu}</span>
           </div>
           <div className="px-5 py-1.5 rounded-full bg-[#050505] border border-white/5 flex items-center space-x-3 shadow-inner">
             <span className="text-[10px] font-semibold text-zinc-500">RAM</span>
             <span className="text-[10px] font-bold text-[#10b981]">{ram}</span>
           </div>
         </div>

         {/* Voice State Pill */}
         {voiceState !== 'SLEEPING' && (
           <div className={`px-6 py-1.5 rounded-full border text-[10px] font-bold tracking-[0.15em] mb-12 shadow-sm
             ${voiceState === 'PROCESSING' ? 'border-[#78350f] text-[#f59e0b] bg-transparent' : 
               voiceState === 'LISTENING' ? 'border-[#064e3b] text-[#10b981] bg-transparent' : 
               'border-[#1e3a8a] text-[#3b82f6] bg-transparent'}`}>
             {voiceState}
           </div>
         )}
         
         {voiceState === 'SLEEPING' && (
           <div className="px-6 py-1.5 rounded-full border border-white/5 text-zinc-600 font-bold tracking-[0.15em] text-[10px] mb-12 bg-transparent">
             SLEEPING
           </div>
         )}

         {/* Transcript */}
         {transcript && (
           <p className="text-[14px] text-center text-[#d1d5db] font-serif italic max-w-xl mb-24 font-light leading-relaxed">
             "{transcript}"
           </p>
         )}

         {/* Response */}
         {response && (
           <p className="text-[16px] text-center text-[#9ca3af] font-serif italic max-w-2xl font-light leading-relaxed">
             "{response}"
           </p>
         )}
       </div>

       {/* Input Box Area at the absolute bottom */}
       <div className="w-full absolute bottom-0 left-0 p-8">
         <form onSubmit={sendMessage} className="w-full max-w-3xl mx-auto">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              className="w-full bg-[#050505] border border-white/5 rounded-xl px-6 py-3.5 text-sm text-[#d1d5db] outline-none focus:border-[#10b981]/30 transition-colors shadow-inner"
              placeholder=""
            />
         </form>
       </div>
    </div>
  )
}

export default Dashboard;
