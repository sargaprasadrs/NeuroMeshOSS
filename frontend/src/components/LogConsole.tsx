"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface LogConsoleProps {
  logs: string[];
}

export const LogConsole: React.FC<LogConsoleProps> = React.memo(({ logs }) => {
  return (
    <div className="bg-neutral-800/30 border border-neutral-800 rounded-xl p-5 h-full flex flex-col min-h-[300px]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">Trace Stream</h3>
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs text-neutral-600">Live</span>
        </div>
      </div>

      <div
        role="log"
        aria-live="polite"
        className="flex-1 overflow-y-auto max-h-[300px] font-mono text-xs leading-relaxed"
      >
        {logs.length === 0 ? (
          <div className="text-neutral-600 italic text-center py-8">Awaiting workflow triggers...</div>
        ) : (
          logs.map((log, index) => (
            <div
              key={index}
              className={cn(
                "py-1.5 border-l-2 pl-3 mb-0.5",
                log.includes("[error]") ? "border-red-500/50 text-red-400/80" :
                log.includes("[engine]") ? "border-emerald-500/50 text-emerald-400/80" :
                log.includes("[queue]") ? "border-blue-500/50 text-blue-400/80" :
                "border-neutral-700/50 text-neutral-500"
              )}
            >
              {log}
            </div>
          ))
        )}
      </div>
    </div>
  );
});

LogConsole.displayName = "LogConsole";
