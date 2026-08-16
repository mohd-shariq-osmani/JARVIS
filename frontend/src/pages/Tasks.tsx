import React, { useState, useEffect } from 'react';
import { Clock, Plus, Trash2, Play, Pause, RefreshCw, CheckCircle2, AlertCircle, Calendar, Repeat, Bell } from 'lucide-react';

interface TaskItem {
  id: string;
  title: string;
  description?: string;
  action: string;
  schedule_type: 'once' | 'interval' | 'daily';
  schedule_value: any;
  status: 'active' | 'completed' | 'paused' | 'failed';
  created_at: string;
  next_run: number;
  last_run?: string;
  last_result?: string;
}

const Tasks: React.FC = () => {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [title, setTitle] = useState('');
  const [action, setAction] = useState('');
  const [scheduleType, setScheduleType] = useState<'once' | 'interval' | 'daily'>('once');
  const [scheduleValue, setScheduleValue] = useState<string>('60');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/tasks/');
      if (res.ok) {
        const data = await res.json();
        setTasks(data.tasks || []);
      }
    } catch (err) {
      console.error('Failed to fetch tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !action.trim()) return;

    let parsedVal: any = scheduleValue;
    if (scheduleType === 'once' || scheduleType === 'interval') {
      parsedVal = parseInt(scheduleValue, 10) || 60;
    }

    try {
      const res = await fetch('http://127.0.0.1:8000/tasks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          action: action.trim(),
          schedule_type: scheduleType,
          schedule_value: parsedVal
        })
      });

      if (res.ok) {
        setTitle('');
        setAction('');
        setIsAdding(false);
        showToast('Task scheduled successfully!', 'success');
        fetchTasks();
      } else {
        showToast('Failed to schedule task.', 'error');
      }
    } catch (err) {
      showToast('Network error scheduling task.', 'error');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/tasks/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setTasks(prev => prev.filter(t => t.id !== id));
        showToast('Task removed', 'success');
      }
    } catch (err) {
      showToast('Error deleting task', 'error');
    }
  };

  const handleToggle = async (id: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/tasks/${id}/toggle`, {
        method: 'POST'
      });
      if (res.ok) {
        fetchTasks();
      }
    } catch (err) {
      showToast('Error toggling task', 'error');
    }
  };

  const formatNextRun = (timestamp: number) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10';
      case 'completed':
        return 'border-blue-500/30 text-blue-400 bg-blue-500/10';
      case 'paused':
        return 'border-amber-500/30 text-amber-400 bg-amber-500/10';
      case 'failed':
        return 'border-red-500/30 text-red-400 bg-red-500/10';
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
            <Clock className="text-[#10b981]" size={24} />
            <h2 className="text-2xl font-outfit font-light tracking-[0.2em] text-[#e5e7eb]">
              TASK SCHEDULER & AUTOMATION
            </h2>
          </div>
          <p className="text-xs text-zinc-500 font-mono mt-1">
            Async background cron engine, recurring actions, and smart alarms.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsAdding(!isAdding)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#10b981]/10 border border-[#10b981]/30 text-[#10b981] hover:bg-[#10b981]/20 transition-all text-xs font-mono tracking-wider font-semibold"
          >
            <Plus size={15} />
            {isAdding ? 'CANCEL' : 'SCHEDULE TASK'}
          </button>
          <button
            onClick={fetchTasks}
            title="Refresh"
            className="p-2 rounded-xl bg-black/40 border border-white/5 text-zinc-400 hover:text-zinc-200 hover:border-white/10 transition-all"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Toast Alert */}
      {toast && (
        <div className={`mb-6 flex items-center gap-2 px-4 py-2.5 rounded-xl border text-xs font-mono transition-all ${
          toast.type === 'success' ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300' : 'bg-red-950/40 border-red-500/30 text-red-300'
        }`}>
          {toast.type === 'success' ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
          <span>{toast.message}</span>
        </div>
      )}

      {/* Add Task Form */}
      {isAdding && (
        <form onSubmit={handleCreateTask} className="mb-8 bg-black/60 border border-white/10 rounded-2xl p-6 backdrop-blur-md transition-all">
          <h3 className="text-xs font-mono font-bold tracking-widest text-zinc-400 uppercase mb-4">
            Schedule New Automated Action
          </h3>
          <div className="space-y-4">
            <div>
              <label className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest block mb-1.5">
                Task Name / Reminder Title
              </label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="e.g. Daily Standup Reminder, GPU Temperature Watchdog"
                className="w-full bg-[#050505] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-zinc-200 font-mono outline-none focus:border-[#10b981]/50 transition-colors"
              />
            </div>

            <div>
              <label className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest block mb-1.5">
                Agent Action / Prompt to Execute
              </label>
              <input
                type="text"
                value={action}
                onChange={e => setAction(e.target.value)}
                placeholder="e.g. Check system RAM and tell me, or Remind me to submit code"
                className="w-full bg-[#050505] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-zinc-200 font-mono outline-none focus:border-[#10b981]/50 transition-colors"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest block mb-1.5">
                  Schedule Type
                </label>
                <div className="flex gap-2">
                  {[
                    { id: 'once', label: 'One-Time' },
                    { id: 'interval', label: 'Recurring' },
                    { id: 'daily', label: 'Daily' }
                  ].map(t => (
                    <button
                      type="button"
                      key={t.id}
                      onClick={() => {
                        setScheduleType(t.id as any);
                        if (t.id === 'daily') setScheduleValue('09:00');
                        else if (t.id === 'interval') setScheduleValue('300');
                        else setScheduleValue('60');
                      }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-mono tracking-wider flex-1 transition-all ${
                        scheduleType === t.id
                          ? 'bg-[#10b981] text-black font-bold'
                          : 'bg-zinc-900 text-zinc-400 border border-white/5'
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest block mb-1.5">
                  {scheduleType === 'daily' ? 'Time (HH:MM 24h)' : 'Delay / Interval (Seconds)'}
                </label>
                <input
                  type="text"
                  value={scheduleValue}
                  onChange={e => setScheduleValue(e.target.value)}
                  placeholder={scheduleType === 'daily' ? '09:00' : '60'}
                  className="w-full bg-[#050505] border border-white/10 rounded-xl px-4 py-2 text-xs text-zinc-200 font-mono outline-none focus:border-[#10b981]/50 transition-colors"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                className="px-6 py-2 rounded-xl bg-[#10b981] text-black font-mono font-bold text-xs tracking-widest hover:bg-[#10b981]/90 shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all"
              >
                CREATE SCHEDULE
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Task List */}
      <div className="flex-1">
        {loading && tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-zinc-600 font-mono text-xs gap-3">
            <RefreshCw size={24} className="animate-spin text-[#10b981]" />
            <span>Scanning Task Scheduler...</span>
          </div>
        ) : tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 border border-dashed border-white/5 rounded-2xl p-8 text-center bg-black/20">
            <Clock size={36} className="text-zinc-700 mb-3" />
            <p className="text-sm font-mono text-zinc-400 mb-1">No scheduled tasks found.</p>
            <p className="text-xs text-zinc-600 font-mono max-w-sm">
              Schedule tasks manually above or speak to JARVIS: <br />
              <span className="text-[#10b981] italic">"Remind me in 10 minutes to take a break."</span>
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {tasks.map(t => (
              <div
                key={t.id}
                className="bg-black/50 border border-white/5 hover:border-white/15 rounded-2xl p-5 flex flex-col justify-between group transition-all duration-300 backdrop-blur-sm shadow-[0_4px_20px_rgba(0,0,0,0.3)]"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-mono uppercase tracking-wider border ${getStatusBadge(t.status)}`}>
                        {t.status}
                      </span>
                      <span className="text-[10px] font-mono text-zinc-500 uppercase flex items-center gap-1">
                        {t.schedule_type === 'daily' ? <Calendar size={11} /> : t.schedule_type === 'interval' ? <Repeat size={11} /> : <Bell size={11} />}
                        {t.schedule_type}
                      </span>
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleToggle(t.id)}
                        title={t.status === 'active' ? 'Pause' : 'Activate'}
                        className="text-zinc-500 hover:text-[#10b981] p-1 transition-colors"
                      >
                        {t.status === 'active' ? <Pause size={14} /> : <Play size={14} />}
                      </button>
                      <button
                        onClick={() => handleDelete(t.id)}
                        title="Delete Task"
                        className="text-zinc-600 hover:text-red-400 p-1 transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>

                  <h4 className="text-sm font-outfit font-semibold text-zinc-100 mb-1 tracking-wide">{t.title}</h4>
                  <p className="text-xs font-mono text-zinc-400 mb-3 bg-black/40 p-2.5 rounded-xl border border-white/5">
                    "{t.action}"
                  </p>

                  {t.last_result && (
                    <div className="text-[11px] font-mono text-emerald-400/80 mb-3 pl-2 border-l-2 border-emerald-500/50">
                      Last Output: {t.last_result}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between text-[10px] font-mono text-zinc-600 pt-3 border-t border-white/5">
                  <span>Next: {t.status === 'active' ? formatNextRun(t.next_run) : 'Paused'}</span>
                  <span>Created: {t.created_at}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Tasks;
