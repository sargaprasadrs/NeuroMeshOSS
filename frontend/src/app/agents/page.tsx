"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, Sliders } from "lucide-react";
import { Header } from "@/components/header";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const agents = [
  { id: "researcher_llama", model: "llama3:8b", role: "Researcher", temp: 0.2, maxTokens: 4096 },
  { id: "writer_llama", model: "llama3:8b", role: "Copywriter", temp: 0.7, maxTokens: 2048 },
  { id: "triager_phi", model: "phi3:medium", role: "Triager", temp: 0.0, maxTokens: 1024 },
];

export default function AgentsPage() {
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
                <h1 className="text-3xl font-bold tracking-tight text-white">Agents</h1>
                <p className="text-sm text-neutral-500 mt-1">Registered AI agents and their configurations</p>
              </div>
            </div>
            <Button variant="secondary" size="sm" className="gap-1.5">
              <Sliders className="h-3.5 w-3.5" /> Register Agent
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <Card key={agent.id} className="p-5 hover:border-neutral-700 transition-all duration-300 group">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h4 className="font-semibold text-neutral-200">{agent.id}</h4>
                    <span className="text-xs text-neutral-600 font-mono">{agent.model}</span>
                  </div>
                  <Badge variant="default">{agent.role}</Badge>
                </div>

                <div className="border-t border-neutral-800/50 pt-4 flex flex-col gap-2.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Temperature</span>
                    <span className="text-neutral-300 font-mono">{agent.temp}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Max Tokens</span>
                    <span className="text-neutral-300 font-mono">{agent.maxTokens}</span>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-neutral-800/50">
                  <Button variant="ghost" size="sm" className="w-full justify-center gap-1.5 text-neutral-400">
                    <Sliders className="h-3.5 w-3.5" /> Adjust Parameters
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
