import React, { useState, useEffect } from 'react';
import { Database, Search, Plus, Trash2, Calendar, AlertCircle, RefreshCw, CheckCircle2 } from 'lucide-react';

interface MemoryItem {
  id: string;
  content: string;
  type: string;
  created_at: string;
  metadata?: Record<string, any>;
}

const Memory: React.FC = () => {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isAdding, setIsAdding] = useState<boolean>(false);
  const [newContent, setNewContent] = useState<string>('');
  const [newType, setNewType] = useState<string>('fact');
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const fetchMemories = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/memory/');
      if (res.ok) {
        const data = await res.json();
        setMemories(data.memories || []);
      }
    } catch (err) {
      console.error('Failed to fetch memories:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, []);

  const showStatus = (text: string, type: 'success' | 'error') => {
    setStatusMessage({ text, type });
    setTimeout(() => setStatusMessage(null), 3000);
  };

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContent.trim()) return;

    try {
      const res = await fetch('http://127.0.0.1:8000/memory/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: newContent.trim(), type: newType })
      });
      if (res.ok) {
        setNewContent('');
        setIsAdding(false);
        showStatus('Memory stored successfully', 'success');
        fetchMemories();
      } else {
        showStatus('Failed to store memory', 'error');
      }
    } catch (err) {
      showStatus('Network error while saving memory', 'error');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/memory/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setMemories(prev => prev.filter(m => m.id !== id));
        showStatus('Memory deleted', 'success');
      } else {
        showStatus('Failed to delete memory', 'error');
      }
    } catch (err) {
      showStatus('Network error while deleting', 'error');
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to delete all stored long-term memories?')) return;
    try {
      const res = await fetch('http://127.0.0.1:8000/memory/', {
        method: 'DELETE'
      });
      if (res.ok) {
        setMemories([]);
        showStatus('All memories cleared', 'success');
      }
    } catch (err) {
      showStatus('Error clearing memories', 'error');
    }
  };

  const filteredMemories = memories.filter(m =>
    m.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getTypeBadgeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'preference':
        return 'border-purple-500/30 text-purple-400 bg-purple-500/10';
      case 'fact':
        return 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10';
      case 'instruction':
        return 'border-amber-500/30 text-amber-400 bg-amber-500/10';
      case 'device':
        return 'border-blue-500/30 text-blue-400 bg-blue-500/10';
      default:
        return 'border-zinc-700 text-zinc-400 bg-zinc-800/40';
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0a0a0c] p-8 overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3">
            <Database className="text-[#10b981]" size={24} />
            <h2 className="text-2xl font-outfit font-light tracking-[0.2em] text-[#e5e7eb]">
              LONG-TERM MEMORY
            </h2>
          </div>
          <p className="text-xs text-zinc-500 font-mono mt-1">
            ChromaDB Persistent Vector Vault & Context Injector
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsAdding(!isAdding)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#10b981]/10 border border-[#10b981]/30 text-[#10b981] hover:bg-[#10b981]/20 transition-all text-xs font-mono tracking-wider font-semibold"
          >
            <Plus size={15} />
            {isAdding ? 'CANCEL' : 'ADD MEMORY'}
          </button>
          
          <button
            onClick={fetchMemories}
            title="Refresh"
            className="p-2 rounded-xl bg-black/40 border border-white/5 text-zinc-400 hover:text-zinc-200 hover:border-white/10 transition-all"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>

          {memories.length > 0 && (
            <button
              onClick={handleClearAll}
              title="Clear All Memories"
              className="p-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition-all text-xs font-mono"
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Status Alert */}
      {statusMessage && (
        <div className={`mb-6 flex items-center gap-2 px-4 py-2.5 rounded-xl border text-xs font-mono transition-all ${
          statusMessage.type === 'success' ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300' : 'bg-red-950/40 border-red-500/30 text-red-300'
        }`}>
          {statusMessage.type === 'success' ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Add Memory Form */}
      {isAdding && (
        <form onSubmit={handleAddMemory} className="mb-8 bg-black/60 border border-white/10 rounded-2xl p-6 backdrop-blur-md transition-all">
          <h3 className="text-xs font-mono font-bold tracking-widest text-zinc-400 uppercase mb-4">Store New Memory Record</h3>
          <div className="space-y-4">
            <div>
              <textarea
                value={newContent}
                onChange={e => setNewContent(e.target.value)}
                placeholder="Enter information to store (e.g. User preference, specific system specification, favorite color...)"
                rows={3}
                className="w-full bg-[#050505] border border-white/10 rounded-xl p-4 text-sm text-zinc-200 font-mono placeholder:text-zinc-700 outline-none focus:border-[#10b981]/50 transition-colors resize-none"
              />
            </div>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-zinc-500">Category:</span>
                {['fact', 'preference', 'instruction', 'device', 'person'].map((t) => (
                  <button
                    type="button"
                    key={t}
                    onClick={() => setNewType(t)}
                    className={`px-3 py-1 rounded-lg text-xs font-mono uppercase tracking-wider transition-all ${
                      newType === t
                        ? 'bg-[#10b981] text-black font-bold shadow-[0_0_10px_rgba(16,185,129,0.5)]'
                        : 'bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-white/5'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <button
                type="submit"
                className="px-6 py-2 rounded-xl bg-[#10b981] text-black font-mono font-bold text-xs tracking-widest hover:bg-[#10b981]/90 shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all"
              >
                SAVE TO VAULT
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Search & Filter Bar */}
      <div className="mb-6 relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={16} />
        <input
          type="text"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="Search stored memories by content or tag..."
          className="w-full bg-black/40 border border-white/5 rounded-xl pl-11 pr-4 py-3 text-xs font-mono text-zinc-300 placeholder:text-zinc-700 outline-none focus:border-white/20 transition-all"
        />
      </div>

      {/* Memories List */}
      <div className="flex-1">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-48 text-zinc-600 font-mono text-xs gap-3">
            <RefreshCw size={24} className="animate-spin text-[#10b981]" />
            <span>Scanning Vector Database...</span>
          </div>
        ) : filteredMemories.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 border border-dashed border-white/5 rounded-2xl p-8 text-center bg-black/20">
            <Database size={36} className="text-zinc-700 mb-3" />
            <p className="text-sm font-mono text-zinc-400 mb-1">
              {searchQuery ? 'No matching memories found.' : 'No memories stored in ChromaDB yet.'}
            </p>
            <p className="text-xs text-zinc-600 font-mono max-w-sm">
              You can add memories manually above or ask JARVIS in chat: <br />
              <span className="text-[#10b981] italic">"Remember that my favorite editor is VS Code."</span>
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredMemories.map((m) => (
              <div
                key={m.id}
                className="bg-black/50 border border-white/5 hover:border-white/15 rounded-xl p-5 flex flex-col justify-between group transition-all duration-300 backdrop-blur-sm shadow-[0_4px_20px_rgba(0,0,0,0.3)]"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-mono uppercase tracking-wider border ${getTypeBadgeColor(m.type)}`}>
                      {m.type || 'fact'}
                    </span>
                    <button
                      onClick={() => handleDelete(m.id)}
                      title="Delete Memory"
                      className="text-zinc-600 hover:text-red-400 transition-colors p-1 opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                  <p className="text-sm font-mono text-zinc-200 leading-relaxed break-words mb-4">
                    "{m.content}"
                  </p>
                </div>

                <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-600 pt-3 border-t border-white/5">
                  <Calendar size={12} />
                  <span>{m.created_at || 'Stored'}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Memory;
