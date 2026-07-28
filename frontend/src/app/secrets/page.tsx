"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Plus, Eye, EyeOff, ShieldCheck } from "lucide-react";
import { Header } from "@/components/header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const secrets = [
  { key: "OPENAI_API_KEY", value: "sk-proj-********************", masked: true },
  { key: "ANTHROPIC_API_KEY", value: "sk-ant-********************", masked: true },
  { key: "SLACK_BOT_TOKEN", value: "xoxb-********************", masked: true },
];

export default function SecretsPage() {
  const [items, setItems] = useState(secrets);

  const toggleMask = (index: number) => {
    setItems((prev) =>
      prev.map((s, i) => (i === index ? { ...s, masked: !s.masked } : s))
    );
  };

  return (
    <div className="min-h-screen">
      <Header />

      <main className="pt-24 pb-16">
        <div className="container-custom">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <Link href="/" className="p-2 rounded-lg text-neutral-500 hover:text-white hover:bg-white/5 transition-colors">
                <ArrowLeft className="h-4 w-4" />
              </Link>
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-white">Secrets</h1>
                <p className="text-sm text-neutral-500 mt-1">Encrypted credential management</p>
              </div>
            </div>
            <Button variant="secondary" size="sm" className="gap-1.5">
              <Plus className="h-3.5 w-3.5" /> Add Secret
            </Button>
          </div>

          <Card className="p-6">
            <div className="flex items-center gap-2 mb-5 text-emerald-500 text-xs font-medium">
              <ShieldCheck className="h-3.5 w-3.5" />
              Credentials encrypted with AES-256 GCM
            </div>

            <div className="flex flex-col gap-2">
              {items.map((sec, index) => (
                <div
                  key={sec.key}
                  className="flex items-center justify-between p-4 rounded-xl bg-neutral-800/30 border border-neutral-800 hover:border-neutral-700 transition-all duration-200"
                >
                  <div className="flex-1 flex items-center justify-between pr-4">
                    <span className="text-sm font-medium text-neutral-200">{sec.key}</span>
                    <span className="font-mono text-sm text-neutral-600">
                      {sec.masked ? "••••••••••••••••" : sec.value}
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 shrink-0"
                    onClick={() => toggleMask(index)}
                  >
                    {sec.masked ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
