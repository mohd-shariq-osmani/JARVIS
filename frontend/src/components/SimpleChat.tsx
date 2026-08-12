import React, { useState } from 'react';
import { Send, Mic } from 'lucide-react';

const SimpleChat: React.FC = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<{role: string, content: string}[]>([
    {role: 'assistant', content: 'Good evening, Sir. All systems operating at normal parameters.'}
  ]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    setMessages(prev => [...prev, {role: 'user', content: input.trim()}]);
    setInput('');
    
    try {
       await fetch('http://127.0.0.1:8000/chat', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ message: input.trim() })
       });
    } catch(e) {
        console.error(e);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full bg-[#0a0a0f] text-zinc-100 font-sans">
      <div className="flex items-center justify-center p-4 border-b border-zinc-800/50 bg-[#050508]">
        <h1 className="text-xl font-bold tracking-widest text-zinc-300">JARVIS</h1>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 w-full flex flex-col items-center">
        <div className="w-full max-w-3xl flex flex-col">
          {messages.map((msg, idx) => (
            <div key={idx} className={`mb-6 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`p-4 rounded-2xl max-w-[80%] ${msg.role === 'user' ? 'bg-zinc-800 text-zinc-100' : 'bg-transparent text-zinc-300'}`}>
                {msg.content}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="p-4 bg-[#050508] border-t border-zinc-800/50 flex justify-center">
        <form onSubmit={sendMessage} className="w-full max-w-3xl flex items-center bg-[#0a0a0f] rounded-full border border-zinc-800 px-4 py-2">
          <button type="button" className="p-2 text-zinc-500 hover:text-zinc-300 transition-colors">
            <Mic size={20} />
          </button>
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            className="flex-1 bg-transparent border-none outline-none text-zinc-100 px-4 py-2"
            placeholder="Type a message..."
          />
          <button type="submit" className="p-2 text-zinc-500 hover:text-zinc-300 transition-colors">
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default SimpleChat;
