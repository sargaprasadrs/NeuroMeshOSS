"use client";

import React, { useState } from "react";
import Link from "next/link";
import { KeyRound, ArrowLeft, Plus, Eye, EyeOff, ShieldCheck } from "lucide-react";

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
    <div className="flex flex-col min-h-screen bg-zinc-950 text-zinc-50">
      <header className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/50 backdrop-blur px-6 py-4">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-1 bg-zinc-800 hover:bg-zinc-700 rounded transition text-zinc-300">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="flex items-center gap-2">
            <KeyRound className="h-6 w-6 text-emerald-500" />
            <span className="font-bold text-lg text-zinc-100">Secrets Manager</span>
          </div>
        </div>
        <button className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 px-4 py-2 rounded-lg text-sm font-semibold transition">
          <Plus className="h-4 w-4" /> Register Secret
        </button>
      </header>

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full flex flex-col gap-6">
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6 flex flex-col gap-4">
          <div className="flex items-center gap-2 mb-2 text-emerald-500 text-sm font-medium">
            <ShieldCheck className="h-4 w-4" /> Credentials are encrypted on-disk using AES-256 GCM wrappers.
          </div>
          <div className="flex flex-col gap-3">
            {secrets.map((sec, index) => (
              <div key={sec.key} className="flex items-center justify-between bg-zinc-900/60 border border-zinc-800 p-4 rounded-xl">
                <div className="flex-1 flex items-center justify-between pr-6">
                  <span className="text-sm font-semibold text-zinc-300">{sec.key}</span>
                  <span className="font-mono text-sm text-zinc-500">
                    {sec.masked ? "••••••••••••••••••••" : sec.value}
                  </span>
                </div>
                <button onClick={() => toggleMask(index)} className="p-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-zinc-400 hover:text-white transition">
                  {sec.masked ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                </button>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
