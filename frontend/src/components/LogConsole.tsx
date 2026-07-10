"use client";

import React from "react";

interface LogConsoleProps {
  logs: string[];
}

export const LogConsole: React.FC<LogConsoleProps> = React.memo(({ logs }) => {
  return (
    <section 
      className="lg:col-span-3 bg-zinc-950 border border-zinc-800 rounded-xl p-4 flex flex-col gap-3 font-mono text-xs focus-within:ring-1 focus-within:ring-emerald-500/50"
      aria-label="Real-Time Execution Logs Console"
    >
      <h4 className="font-semibold font-sans text-zinc-300">Real-Time Trace Stream</h4>
      <div 
        role="log" 
        aria-live="polite" 
        aria-label="Log Stream Console Outputs"
        className="flex-1 bg-black/60 rounded-lg p-3 overflow-y-auto max-h-[400px] flex flex-col gap-2 text-emerald-400 border border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-800"
        tabIndex={0}
      >
        {logs.length === 0 ? (
          <div className="text-zinc-650 italic text-center py-6">Awaiting active workflow triggers...</div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="leading-relaxed border-l-2 border-emerald-950 pl-2">
              {log}
            </div>
          ))
        )}
      </div>
    </section>
  );
});

LogConsole.displayName = "LogConsole";
