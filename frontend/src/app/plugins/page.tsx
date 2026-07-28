"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowLeft, DownloadCloud, Sparkles } from "lucide-react";
import { Header } from "@/components/header";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const plugins = [
  { name: "github-sync", version: "0.1.0", desc: "Syncs workflow configurations with remote GitHub repositories.", active: true },
  { name: "slack-notification", version: "0.1.0", desc: "Posts execution summaries and approvals to Slack channels.", active: true },
  { name: "filesystem-tool", version: "0.1.0", desc: "Enables secure local file operations for agent nodes.", active: false },
];

export default function PluginsPage() {
  const [items, setItems] = useState(plugins);

  const togglePlugin = (index: number) => {
    setItems((prev) =>
      prev.map((p, i) => (i === index ? { ...p, active: !p.active } : p))
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
                <h1 className="text-3xl font-bold tracking-tight text-white">Plugins</h1>
                <p className="text-sm text-neutral-500 mt-1">Installed extensions and integrations</p>
              </div>
            </div>
            <Button variant="secondary" size="sm" className="gap-1.5">
              <DownloadCloud className="h-3.5 w-3.5" /> Install
            </Button>
          </div>

          <div className="flex flex-col gap-3">
            {items.map((plugin, index) => (
              <Card key={plugin.name} className="p-5 hover:border-neutral-700 transition-all duration-300">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-semibold text-neutral-200">{plugin.name}</h4>
                      <Badge variant="default">v{plugin.version}</Badge>
                    </div>
                    <p className="text-sm text-neutral-500">{plugin.desc}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge variant={plugin.active ? "success" : "default"}>
                      {plugin.active ? "Enabled" : "Disabled"}
                    </Badge>
                    <button
                      onClick={() => togglePlugin(index)}
                      className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
                        plugin.active ? "bg-emerald-500" : "bg-neutral-700"
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform duration-200 ${
                          plugin.active ? "translate-x-5" : "translate-x-0"
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
