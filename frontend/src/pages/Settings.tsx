import React, { useEffect, useState } from 'react';

interface AISettings {
  provider: string;
  lmstudio_url: string;
  lmstudio_model: string;
  openrouter_key: string;
  openrouter_model: string;
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<AISettings>({
    provider: 'lmstudio',
    lmstudio_url: '',
    lmstudio_model: '',
    openrouter_key: '',
    openrouter_model: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

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
      await fetch('http://127.0.0.1:8000/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
    } catch (err) {
      console.error("Failed to save settings:", err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-8 h-full text-zinc-400">Loading settings...</div>;

  return (
    <div className="p-8 h-full flex flex-col">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-3xl font-light tracking-widest text-zinc-200">Settings</h2>
        <button 
          onClick={handleSave}
          disabled={saving}
          className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-colors disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>

      <div className="max-w-2xl space-y-6">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-6 space-y-4">
          <h3 className="text-xl text-zinc-300 font-medium mb-4">AI Provider</h3>
          
          <div className="flex flex-col space-y-2">
            <label className="text-xs font-mono text-zinc-500 uppercase tracking-wider">Active Provider</label>
            <select 
              name="provider" 
              value={settings.provider} 
              onChange={handleChange}
              className="bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-zinc-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="lmstudio">LM Studio (Local)</option>
              <option value="openrouter">OpenRouter (Cloud)</option>
            </select>
          </div>
        </div>

        <div className={`bg-zinc-900/50 border border-zinc-800 rounded-lg p-6 space-y-4 transition-opacity ${settings.provider !== 'lmstudio' ? 'opacity-50' : 'opacity-100'}`}>
          <h3 className="text-xl text-zinc-300 font-medium mb-4">LM Studio Settings</h3>
          
          <div className="flex flex-col space-y-2">
            <label className="text-xs font-mono text-zinc-500 uppercase tracking-wider">Base URL</label>
            <input 
              name="lmstudio_url" 
              value={settings.lmstudio_url} 
              onChange={handleChange}
              className="bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-zinc-200 focus:outline-none focus:border-emerald-500 font-mono text-sm"
            />
          </div>
          
          <div className="flex flex-col space-y-2">
            <label className="text-xs font-mono text-zinc-500 uppercase tracking-wider">Model Name</label>
            <input 
              name="lmstudio_model" 
              value={settings.lmstudio_model} 
              onChange={handleChange}
              placeholder="e.g. local-model"
              className="bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-zinc-200 focus:outline-none focus:border-emerald-500 font-mono text-sm"
            />
          </div>
        </div>

        <div className={`bg-zinc-900/50 border border-zinc-800 rounded-lg p-6 space-y-4 transition-opacity ${settings.provider !== 'openrouter' ? 'opacity-50' : 'opacity-100'}`}>
          <h3 className="text-xl text-zinc-300 font-medium mb-4">OpenRouter Settings</h3>
          
          <div className="flex flex-col space-y-2">
            <label className="text-xs font-mono text-zinc-500 uppercase tracking-wider">API Key</label>
            <input 
              name="openrouter_key" 
              type="password"
              value={settings.openrouter_key} 
              onChange={handleChange}
              placeholder="sk-or-v1-..."
              className="bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-zinc-200 focus:outline-none focus:border-emerald-500 font-mono text-sm"
            />
          </div>

          <div className="flex flex-col space-y-2">
            <label className="text-xs font-mono text-zinc-500 uppercase tracking-wider">Model ID</label>
            <input 
              name="openrouter_model" 
              value={settings.openrouter_model} 
              onChange={handleChange}
              placeholder="google/gemini-pro-1.5"
              className="bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-zinc-200 focus:outline-none focus:border-emerald-500 font-mono text-sm"
            />
          </div>
        </div>

      </div>
    </div>
  );
};

export default Settings;
