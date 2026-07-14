"use client";

import React, { useState } from "react";
import Link from "next/link";
import { KeyRound, ArrowLeft, Plus, Eye, EyeOff, ShieldCheck } from "lucide-react";
import { SpotlightCard } from "@/components/SpotlightCard";

export default function SecretsPage() {
  const [secrets, setSecrets] = useState([
    { key: "OPENAI_API_KEY", value: "sk-proj-********************", masked: true },
    { key: "ANTHROPIC_API_KEY", value: "sk-ant-********************", masked: true },
    { key: "SLACK_BOT_TOKEN", value: "xoxb-********************", masked: true },
  ]);

  const toggleMask = (index: number) => {
    setSecrets((prev) =>
      prev.map((s, i) => (i === index ? { ...s, masked: !s.masked } : s))
    );
  };

  return (
    <div className="flex flex-col min-h-screen bg-black text-zinc-50 font-sans">
      <header className="flex items-center justify-between border-b border-zinc-900 bg-black px-6 py-4 relative z-50">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-1.5 hover:bg-zinc-900 border border-zinc-900 rounded transition text-zinc-400 hover:text-zinc-200 flex items-center justify-center">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="flex items-center gap-2.5">
            <div className="h-5 w-5 rounded bg-emerald-500 flex items-center justify-center">
              <KeyRound className="h-3 w-3 text-black stroke-[2.5]" />
            </div>
            <span className="font-semibold text-sm tracking-tight text-zinc-100">
              Secrets
            </span>
          </div>
        </div>
        <button className="flex items-center gap-1.5 bg-zinc-100 hover:bg-zinc-200 text-black text-xs font-semibold px-4 py-2 rounded transition-colors duration-150">
          <Plus className="h-3.5 w-3.5 stroke-[2.5]" /> Add Secret
        </button>
      </header>

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full flex flex-col gap-6">
        <SpotlightCard className="p-0">
          <div className="p-6 flex flex-col gap-5">
            <div className="flex items-center justify-between border-b border-zinc-900 pb-4 mb-1">
              <div className="flex items-center gap-2 text-zinc-450 text-xs font-medium">
                <ShieldCheck className="h-4 w-4 text-emerald-500" />
                <span>Credentials are encrypted on-disk using AES-256 GCM</span>
              </div>
            </div>

            <div className="flex flex-col gap-3">
              {secrets.map((sec, index) => (
                <div key={sec.key} className="flex items-center justify-between border border-zinc-900 bg-zinc-950/40 p-4 rounded-lg hover:border-zinc-800 transition duration-150">
                  <div className="flex-1 flex flex-col sm:flex-row sm:items-center justify-between pr-6 gap-2">
                    <span className="text-xs font-semibold text-zinc-300 tracking-tight">
                      {sec.key}
                    </span>
                    <span className="font-mono text-xs text-zinc-550 select-all">
                      {sec.masked ? "••••••••••••••••••••" : sec.value}
                    </span>
                  </div>
                  <button
                    onClick={() => toggleMask(index)}
                    className="p-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-850 rounded text-zinc-450 hover:text-zinc-200 transition duration-150"
                  >
                    {sec.masked ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </SpotlightCard>
      </main>
    </div>
  );
}
