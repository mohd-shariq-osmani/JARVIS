import React, { useEffect, useState } from 'react';
import { Settings as SettingsIcon, Save, RefreshCw, CheckCircle2, AlertCircle, Cpu, Cloud, Zap, ShieldCheck } from 'lucide-react';

interface AISettings {
  provider: string;
  lmstudio_url: string;
  lmstudio_model: string;
  openrouter_key: string;
  openrouter_model: string;
  routing_mode?: string;
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<AISettings>({
    provider: 'lmstudio',
    lmstudio_url: 'http://127.0.0.1:1234/v1',
    lmstudio_model: 'local-model',
    openrouter_key: '',
    openrouter_model: 'google/gemma-4-26b-a4b-it:free',
    routing_mode: 'manual'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  useEffect(() => {
    fetch('http://127.0.0.1:8000/settings')
      .then(res => res.json())
      .then(data => {
        setSettings(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load settings:", err);
        setLoading(false);
      });
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setSettings(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/settings/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      if (res.ok) {
        showToast('Settings saved & applied immediately!', 'success');
      } else {
        showToast('Failed to save settings.', 'error');
      }
    } catch (err) {
      showToast('Network error while saving settings.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async (provider: 'lmstudio' | 'openrouter') => {
    setTestingProvider(provider);
    try {
      const res = await fetch('http://127.0.0.1:8000/settings/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          lmstudio_url: settings.lmstudio_url,
          openrouter_key: settings.openrouter_key
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(data.message || `Successfully connected to ${provider.toUpperCase()}!`, 'success');
      } else {
        showToast(data.message || `Connection to ${provider.toUpperCase()} failed.`, 'error');
      }
    } catch (err) {
      showToast(`Error testing ${provider} connection.`, 'error');
    } finally {
      setTestingProvider(null);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full bg-[#0a0a0c] text-zinc-500 font-mono text-xs gap-3">
        <RefreshCw size={24} className="animate-spin text-[#10b981]" />
        <span>Loading Configuration...</span>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0a0a0c] p-8 overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3">
            <SettingsIcon className="text-[#10b981]" size={24} />
            <h2 className="text-2xl font-outfit font-light tracking-[0.2em] text-[#e5e7eb]">
              SYSTEM CONFIGURATION
            </h2>
          </div>
          <p className="text-xs text-zinc-500 font-mono mt-1">
            Configure local LM Studio, OpenRouter cloud intelligence, and auto-routing.
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#10b981] text-black font-mono font-bold text-xs tracking-widest hover:bg-[#10b981]/90 shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all disabled:opacity-50"
        >
          <Save size={15} />
          {saving ? 'APPLYING...' : 'SAVE CONFIGURATION'}
        </button>
      </div>

      {/* Toast Alert */}
      {toast && (
        <div className={`mb-6 flex items-center gap-2 px-4 py-3 rounded-xl border text-xs font-mono transition-all ${
          toast.type === 'success' ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300' : 'bg-red-950/40 border-red-500/30 text-red-300'
        }`}>
          {toast.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          <span>{toast.message}</span>
        </div>
      )}

      <div className="max-w-3xl space-y-6">
        {/* Active AI Provider Card */}
        <div className="bg-black/50 border border-white/5 rounded-2xl p-6 backdrop-blur-sm shadow-[0_4px_20px_rgba(0,0,0,0.3)]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-mono font-bold tracking-widest text-zinc-300 uppercase flex items-center gap-2">
              <Zap size={14} className="text-[#10b981]" />
              AI Routing Mode
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 border border-white/10 text-zinc-400">
              Active: {settings.provider.toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { id: 'lmstudio', label: 'LM Studio (Local)', icon: Cpu, desc: 'Zero cloud latency, fully private on your GPU' },
              { id: 'openrouter', label: 'OpenRouter (Cloud)', icon: Cloud, desc: 'Access Gemma, Claude, GPT, or Gemini' },
              { id: 'auto', label: 'Auto Fallback', icon: ShieldCheck, desc: 'Local first, fallback to cloud if offline' }
            ].map(item => (
              <button
                type="button"
                key={item.id}
                onClick={() => setSettings(prev => ({ ...prev, provider: item.id }))}
                className={`p-4 rounded-xl border flex flex-col text-left transition-all ${
                  settings.provider === item.id
                    ? 'border-[#10b981] bg-[#10b981]/10 text-white shadow-[0_0_15px_rgba(16,185,129,0.15)]'
                    : 'border-white/5 bg-black/30 text-zinc-400 hover:border-white/15'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <item.icon size={16} className={settings.provider === item.id ? 'text-[#10b981]' : 'text-zinc-500'} />
                  <span className="text-xs font-mono font-bold tracking-wide">{item.label}</span>
                </div>
                <p className="text-[11px] font-mono text-zinc-500 leading-normal">{item.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* LM Studio Configuration */}
        <div className={`bg-black/50 border rounded-2xl p-6 backdrop-blur-sm transition-all ${
          settings.provider === 'lmstudio' || settings.provider === 'auto' ? 'border-white/10 opacity-100' : 'border-white/5 opacity-50'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-mono font-bold tracking-widest text-zinc-300 uppercase flex items-center gap-2">
              <Cpu size={14} className="text-[#10b981]" />
              LM Studio (Local Engine)
            </h3>
            <button
              type="button"
              onClick={() => handleTestConnection('lmstudio')}
              disabled={testingProvider === 'lmstudio'}
              className="text-[10px] font-mono uppercase tracking-wider px-3 py-1 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-300 transition-all flex items-center gap-1.5"
            >
              <RefreshCw size={11} className={testingProvider === 'lmstudio' ? 'animate-spin' : ''} />
              Test Connection
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest block mb-1.5">
                Local Server Endpoint
              </label>
              <input
                name="lmstudio_url"
                value={settings.lmstudio_url}
                onChange={handleChange}
                placeholder="http://127.0.0.1:1234/v1"
                className="w-full bg-[#050505] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-zinc-200 font-mono outline-none focus:border-[#10b981]/50 transition-colors"
              />
            </div>
            <div>
              <label className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest block mb-1.5">
                Local Model Identifier
              </label>
              <input
                name="lmstudio_model"
                value={settings.lmstudio_model}
                onChange={handleChange}
                placeholder="e.g. local-model or gemma-4-e4b"
                className="w-full bg-[#050505] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-zinc-200 font-mono outline-none focus:border-[#10b981]/50 transition-colors"
              />
            </div>
          </div>
        </div>

        {/* OpenRouter Configuration */}
        <div className={`bg-black/50 border rounded-2xl p-6 backdrop-blur-sm transition-all ${
          settings.provider === 'openrouter' || settings.provider === 'auto' ? 'border-white/10 opacity-100' : 'border-white/5 opacity-50'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-mono font-bold tracking-widest text-zinc-300 uppercase flex items-center gap-2">
              <Cloud size={14} className="text-[#3b82f6]" />
              OpenRouter (Cloud Intelligence)
            </h3>
            <button
              type="button"
              onClick={() => handleTestConnection('openrouter')}
              disabled={testingProvider === 'openrouter'}
              className="text-[10px] font-mono uppercase tracking-wider px-3 py-1 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-300 transition-all flex items-center gap-1.5"
            >
              <RefreshCw size={11} className={testingProvider === 'openrouter' ? 'animate-spin' : ''} />
              Validate Key
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest block mb-1.5">
                API Key
              </label>
              <input
                name="openrouter_key"
                type="password"
                value={settings.openrouter_key}
                onChange={handleChange}
                placeholder="sk-or-v1-..."
                className="w-full bg-[#050505] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-zinc-200 font-mono outline-none focus:border-[#3b82f6]/50 transition-colors"
              />
            </div>
            <div>
              <label className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest block mb-1.5">
                Model ID
              </label>
              <input
                name="openrouter_model"
                value={settings.openrouter_model}
                onChange={handleChange}
                placeholder="google/gemma-4-26b-a4b-it:free"
                className="w-full bg-[#050505] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-zinc-200 font-mono outline-none focus:border-[#3b82f6]/50 transition-colors"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
