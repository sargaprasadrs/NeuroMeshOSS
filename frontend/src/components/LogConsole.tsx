"use client";

import React from "react";
import { SpotlightCard } from "./SpotlightCard";

interface LogConsoleProps {
  logs: string[];
}

export const LogConsole: React.FC<LogConsoleProps> = React.memo(({ logs }) => {
  return (
    <SpotlightCard className="lg:col-span-3 h-full flex flex-col p-0">
      <div 
        className="p-5 flex flex-col gap-4 font-mono text-xs h-full"
        aria-label="Execution logs output trace"
      >
        <div className="flex items-center justify-between font-sans border-b border-zinc-900 pb-3">
          <h4 className="font-semibold text-zinc-300">Live Execution Trace</h4>
          <span className="flex items-center gap-1.5 text-[10px] text-zinc-400 font-mono">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
            Streaming
          </span>
        </div>
        
        <div 
          role="log" 
          aria-live="polite" 
          className="flex-1 bg-zinc-950/40 rounded border border-zinc-900/60 p-3.5 overflow-y-auto max-h-[380px] flex flex-col gap-2.5 text-zinc-400 font-mono text-[11px] focus:outline-none focus:ring-1 focus:ring-zinc-800"
          tabIndex={0}
        >
          {logs.length === 0 ? (
            <div className="text-zinc-600 italic text-center py-6">No execution traces generated.</div>
          ) : (
            logs.map((log, index) => (
              <div key={index} className="leading-relaxed border-l border-zinc-800 pl-3">
                {log.replace(/\[\d+\] /, "") /* clean up binary prefix numbers if present */}
              </div>
            ))
          )}
        </div>
      </div>
    </SpotlightCard>
  );
});

LogConsole.displayName = "LogConsole";
