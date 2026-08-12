import React from 'react';

const Diagnostics: React.FC = () => {
  return (
    <div className="p-8 h-full">
      <h2 className="text-3xl font-light tracking-widest text-zinc-200 mb-8">Diagnostics</h2>
      <div className="max-w-2xl bg-zinc-900/50 border border-zinc-800 rounded-lg p-6">
        <p className="text-zinc-400">System health and diagnostics will go here...</p>
      </div>
    </div>
  );
};

export default Diagnostics;
