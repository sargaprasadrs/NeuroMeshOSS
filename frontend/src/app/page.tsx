"use client";

import React, { useState, useCallback, useEffect, Fragment } from "react";
import Link from "next/link";
import { Play, Cpu, Layers, Activity, Plus, Zap, RefreshCw, ShieldAlert } from "lucide-react";
import { LogConsole } from "@/components/LogConsole";
import { THEMES } from "@/lib/themes";

/* ─── Wind Layer ────────────────────────────────────────────── */

interface WindLineDef { top: string; width: string; dur: string; delay: string; ease: string; }
interface PetalDef { top: string; left: string; dur: string; delay: string; color: string; rotate: string; }

function seededRand(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

function buildWindLines(): WindLineDef[] {
  const rand = seededRand(42);
  return Array.from({ length: 9 }, (_, i) => ({
    top: `${8 + i * 10}%`,
    width: `${rand() * 180 + 120}px`,
    dur: `${(rand() * 4 + 5).toFixed(1)}s`,
    delay: `${(rand() * 6).toFixed(1)}s`,
    ease: i % 3 === 0 ? "ease-in-out" : "linear",
  }));
}

function buildPetals(): PetalDef[] {
  const rand = seededRand(77);
  const colors = ["rgba(179,58,58,0.35)", "rgba(212,168,75,0.3)", "rgba(38,70,83,0.2)"];
  return Array.from({ length: 7 }, (_, i) => ({
    top: `${rand() * 80 + 5}%`,
    left: `${rand() * 10}%`,
    dur: `${(rand() * 8 + 9).toFixed(1)}s`,
    delay: `${(rand() * 12).toFixed(1)}s`,
    color: colors[i % colors.length],
    rotate: `${Math.round(rand() * 60 - 30)}deg`,
  }));
}

const WIND_LINES = buildWindLines();
const PETALS = buildPetals();

function WindLayer() {
  return (
    <div className="wind-layer" aria-hidden="true">
      {WIND_LINES.map((l, i) => (
        <div
          key={i}
          className="wind-line"
          style={{ top: l.top, width: l.width, "--dur": l.dur, "--delay": l.delay, "--ease": l.ease } as React.CSSProperties}
        />
      ))}
      {PETALS.map((p, i) => (
        <div
          key={i}
          className="wind-petal"
          style={{ top: p.top, left: p.left, background: p.color, transform: `rotate(${p.rotate})`, "--dur": p.dur, "--delay": p.delay } as React.CSSProperties}
        />
      ))}
    </div>
  );
}

/* ─── Theme Switcher ────────────────────────────────────────── */

interface Theme {
  id: string;
  name: string;
  swatches: [string, string, string];
  vars: Record<string, string>;
}

function ThemeSwitcher({ theme, onCycle }: { theme: Theme; onCycle: () => void }) {
  return (
    <button
      className="theme-switcher"
      onClick={onCycle}
      aria-label={`Theme: ${theme.name}. Click to cycle theme.`}
      title="Click to change colour theme"
    >
      <span className="theme-swatches" aria-hidden="true">
        {theme.swatches.map((c, i) => (
          <span key={i} className="theme-swatch" style={{ background: c }} />
        ))}
      </span>
      <span className="theme-switcher-info">
        <span className="theme-switcher-name">{theme.name}</span>
        <span className="theme-switcher-hex">{theme.swatches[1]}</span>
      </span>
      <span className="theme-cycle-icon" aria-hidden="true">↺</span>
    </button>
  );
}

/* ─── App / Dashboard ───────────────────────────────────────── */

export default function Dashboard() {
  const [logs, setLogs] = useState<string[]>([
    "Engine initialized. Awaiting workflow triggers.",
    "Running in local fallback mode (SQLite & In-Memory events).",
  ]);

  const [workflows, setWorkflows] = useState<any[]>([]);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [themeIdx, setThemeIdx] = useState(0);
  const currentTheme = THEMES[themeIdx];

  useEffect(() => {
    const saved = localStorage.getItem("portfolio-theme");
    if (saved) {
      const idx = THEMES.findIndex((t) => t.id === saved);
      if (idx !== -1) setThemeIdx(idx);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("portfolio-theme", currentTheme.id);
    Object.entries(currentTheme.vars).forEach(([k, v]) => {
      document.documentElement.style.setProperty(k, v);
    });
  }, [currentTheme]);

  const cycleTheme = () => {
    setThemeIdx((cur) => {
      let next = cur;
      while (next === cur) next = Math.floor(Math.random() * THEMES.length);
      return next;
    });
  };

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/workflows/")
      .then((res) => res.json())
      .then((data) => {
        if (data && data.items) {
          setWorkflows(data.items);
        }
      })
      .catch((err) => {
        console.error("Error fetching workflows:", err);
        // Fallback local mock if backend is down during initial load
        setWorkflows([
          { id: "11111111-1111-1111-1111-111111111111", name: "Market Analyzer Agent Flow" }
        ]);
      });
  }, []);

  const triggerRealRun = useCallback(async (workflowId: string, name: string) => {
    setIsExecuting(true);
    setLogs((prev) => [
      ...prev,
      `Manual run request initiated for ${name}`,
    ]);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/workflows/${workflowId}/run`, {
        method: "POST"
      });
      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }
      const data = await res.json();
      const runId = data.run_id;
      setLogs((prev) => [
        ...prev,
        `Created run execution context ID: ${runId}`,
        `Connecting to live trace stream...`,
      ]);

      // Connect to live WebSocket events
      const ws = new WebSocket(`ws://localhost:8000/ws/runs/${runId}`);
      ws.onmessage = (event) => {
        try {
          const payloadData = JSON.parse(event.data);
          const { event_type, payload } = payloadData;
          let logLine = `[${event_type}]`;
          if (event_type === "RUN_RUNNING") {
             logLine += ` Run status changed to RUNNING.`;
          } else if (event_type === "NODE_STARTED") {
             logLine += ` Executing Node: ${payload.node_id} (Type: ${payload.type})`;
          } else if (event_type === "NODE_COMPLETED") {
             logLine += ` Finished Node: ${payload.node_id} (Status: ${payload.status})`;
          } else if (event_type === "RUN_PAUSED") {
             logLine += ` Human approval requested at node. Execution paused.`;
          } else if (event_type === "RUN_COMPLETED") {
             logLine += ` Workflow run completed successfully.`;
             setIsExecuting(false);
          } else if (event_type === "RUN_FAILED") {
             logLine += ` Workflow run failed: ${payload.error || "Execution error"}`;
             setIsExecuting(false);
          } else {
             logLine += ` ${JSON.stringify(payload)}`;
          }
          setLogs((prev) => [...prev, logLine]);
        } catch (e) {
          setLogs((prev) => [...prev, `Received raw message: ${event.data}`]);
        }
      };
      ws.onerror = () => {
        setLogs((prev) => [...prev, `Error: Connection failed.`]);
        setIsExecuting(false);
      };
      ws.onclose = () => {
        setLogs((prev) => [...prev, `Trace connection closed.`]);
        setIsExecuting(false);
      };
    } catch (err: any) {
      setLogs((prev) => [
        ...prev,
        `Failed to trigger workflow: ${err.message}`,
      ]);
      setIsExecuting(false);
    }
  }, []);

  return (
    <div className="neo-edo-container min-h-screen flex flex-col font-sans transition-all duration-500 overflow-x-hidden">
      <div className="paper-texture" aria-hidden="true" />
      <WindLayer />

      <svg className="ink-splatter top-left" viewBox="0 0 100 100" aria-hidden="true">
        <circle cx="22" cy="22" r="16" fill="var(--cinnabar)" opacity="0.08" />
        <circle cx="38" cy="34" r="9" fill="var(--cinnabar)" opacity="0.06" />
        <circle cx="14" cy="42" r="5" fill="var(--cinnabar)" opacity="0.05" />
      </svg>
      <svg className="ink-splatter bottom-right" viewBox="0 0 100 100" aria-hidden="true">
        <circle cx="78" cy="78" r="13" fill="var(--indigo)" opacity="0.07" />
        <circle cx="62" cy="68" r="7" fill="var(--indigo)" opacity="0.05" />
      </svg>

      {/* Futuristic Command Header */}
      <nav className="top-nav">
        <div className="nav-left">
          <div className="nav-logo" aria-label="SR monogram">SR</div>
          <div className="nav-divider" />
          <span className="nav-title">NEUROMESH / HIVEMIND ENGINE</span>
        </div>
        
        {/* Navigation items adapted */}
        <div className="hidden md:flex items-center gap-2">
          <Link href="/workflows" className="nav-btn">Workflows</Link>
          <span className="nav-dot" aria-hidden="true" />
          <Link href="/agents" className="nav-btn">Agents</Link>
          <span className="nav-dot" aria-hidden="true" />
          <Link href="/plugins" className="nav-btn">Plugins</Link>
          <span className="nav-dot" aria-hidden="true" />
          <Link href="/secrets" className="nav-btn">Secrets</Link>
          <span className="nav-dot" aria-hidden="true" />
          <Link href="/metrics" className="nav-btn">Metrics</Link>
        </div>

        <div className="flex items-center gap-4">
          <ThemeSwitcher theme={currentTheme} onCycle={cycleTheme} />

          <div className="hidden sm:flex items-center gap-2 border border-emerald-950 bg-emerald-950/20 px-3 py-1 rounded-full shadow-[inset_0_0_4px_rgba(16,185,129,0.1)]">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-[10px] font-mono font-bold tracking-widest text-emerald-400 uppercase">
              Engine Online
            </span>
          </div>
        </div>
      </nav>

      {/* Main Dashboard Space */}
      <main className="main-content loaded relative z-10 flex-1 p-6 flex flex-col gap-6 max-w-7xl mx-auto w-full">
        
        {/* Core HUD Section */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[500px]">
          
          {/* Left panel: Workflows selection */}
          <aside className="lg:col-span-3 h-full">
            <div className="manga-panel h-full flex flex-col p-5">
              <div className="panel-header">
                <span className="panel-number">FLOW</span>
                <h2>Workflows</h2>
              </div>
              <p className="text-[10px] font-mono text-ink-muted mb-4">Select and execute automation workflows</p>
              
              <div className="flex flex-col gap-2.5 overflow-y-auto max-h-[360px]">
                {workflows.map((wf) => (
                  <div
                    key={wf.id}
                    className="p-3 bg-parchment hover:bg-parchment-dark border border-ink/15 hover:border-ink rounded transition duration-200 flex items-center justify-between group cursor-pointer"
                  >
                    <span className="text-xs font-semibold font-mono text-ink truncate pr-3" title={wf.name}>
                      {wf.name}
                    </span>
                    <button
                      onClick={() => triggerRealRun(wf.id, wf.name)}
                      aria-label={`Trigger manual run for workflow ${wf.name}`}
                      className="p-1.5 bg-parchment hover:bg-cinnabar/20 border border-ink/40 hover:border-cinnabar rounded text-ink/75 hover:text-cinnabar transition-all focus:outline-none flex items-center justify-center"
                    >
                      <Play className="h-3 w-3 fill-current" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </aside>

          {/* Center Holographic Core Visualizer Panel */}
          <section className="lg:col-span-6 h-full flex flex-col justify-between p-5 manga-panel">
            <div className="panel-header">
              <span className="panel-number">CORE</span>
              <h2>Quantum Hivemind Visualizer</h2>
              <span className={`px-2 py-0.5 text-[8px] font-mono font-bold tracking-widest uppercase rounded ${
                isExecuting ? "bg-cinnabar/20 text-cinnabar border border-cinnabar/40 animate-pulse" : "bg-parchment-dark text-ink-muted"
              }`}>
                {isExecuting ? "Executing" : "Core Idle"}
              </span>
            </div>

            {/* Glowing Center Core Frame container */}
            <div className="flex-1 flex flex-col items-center justify-center relative py-6">
              
              {/* Center Uiverse .svg-frame Component */}
              <div className="svg-frame cursor-pointer select-none">
                <svg style={{ "--i": 0, "--j": 0 } as React.CSSProperties}>
                  <g id="out1">
                    <path d="M72 172C72 116.772 116.772 72 172 72C227.228 72 272 116.772 272 172C272 227.228 227.228 272 172 272C116.772 272 72 227.228 72 172ZM197.322 172C197.322 158.015 185.985 146.678 172 146.678C158.015 146.678 146.678 158.015 146.678 172C146.678 185.985 158.015 197.322 172 197.322C185.985 197.322 197.322 185.985 197.322 172Z" />
                    <path mask="url(#path-1-inside-1_111_3212)" strokeMiterlimit={16} strokeWidth={2} stroke="var(--cinnabar)" d="M72 172C72 116.772 116.772 72 172 72C227.228 72 272 116.772 272 172C272 227.228 227.228 272 172 272C116.772 272 72 227.228 72 172ZM197.322 172C197.322 158.015 185.985 146.678 172 146.678C158.015 146.678 146.678 158.015 146.678 172C146.678 185.985 158.015 197.322 172 197.322C185.985 197.322 197.322 185.985 197.322 172Z" />
                  </g>
                </svg>

                <svg style={{ "--i": 1, "--j": 1 } as React.CSSProperties}>
                  <g id="out2">
                    <mask fill="white" id="path-2-inside-2_111_3212">
                      <path d="M102.892 127.966C93.3733 142.905 88.9517 160.527 90.2897 178.19L94.3752 177.88C93.1041 161.1 97.3046 144.36 106.347 130.168L102.892 127.966Z" />
                      <path d="M93.3401 194.968C98.3049 211.971 108.646 226.908 122.814 237.541L125.273 234.264C111.814 224.163 101.99 209.973 97.2731 193.819L93.3401 194.968Z" />
                      <path d="M152.707 92.3592C140.33 95.3575 128.822 101.199 119.097 109.421L121.742 112.55C130.981 104.739 141.914 99.1897 153.672 96.3413L152.707 92.3592Z" />
                      <path d="M253.294 161.699C255.099 175.937 253.132 190.4 247.59 203.639L243.811 202.057C249.075 189.48 250.944 175.74 249.23 162.214L253.294 161.699Z" />
                      <path d="M172 90.0557C184.677 90.0557 197.18 92.9967 208.528 98.6474C219.875 104.298 229.757 112.505 237.396 122.621L234.126 125.09C226.869 115.479 217.481 107.683 206.701 102.315C195.921 96.9469 184.043 94.1529 172 94.1529V90.0557Z" />
                      <path d="M244.195 133.235C246.991 138.442 249.216 143.937 250.83 149.623L246.888 150.742C245.355 145.34 243.242 140.12 240.586 135.174L244.195 133.235Z" />
                      <path d="M234.238 225.304C223.932 237.338 210.358 246.126 195.159 250.604C179.961 255.082 163.79 255.058 148.606 250.534L149.775 246.607C164.201 250.905 179.563 250.928 194.001 246.674C208.44 242.42 221.335 234.071 231.126 222.639L234.238 225.304Z" />
                    </mask>
                    <path mask="url(#path-2-inside-2_111_3212)" fill="var(--indigo)" d="M102.892 127.966L105.579 123.75L101.362 121.063L98.6752 125.28L102.892 127.966ZM90.2897 178.19L85.304 178.567L85.6817 183.553L90.6674 183.175L90.2897 178.19ZM94.3752 177.88L94.7529 182.866L99.7386 182.488L99.3609 177.503L94.3752 177.88ZM106.347 130.168L110.564 132.855L113.251 128.638L109.034 125.951ZM93.3401 194.968L91.9387 190.168L87.1391 191.569L88.5405 196.369ZM122.814 237.541L119.813 241.54L123.812 244.541L126.813 240.542ZM125.273 234.264L129.272 237.265L132.273 233.266L128.274 230.265ZM97.2731 193.819L102.073 192.418L100.671 187.618L95.8717 189.02ZM152.707 92.3592L157.567 91.182L156.389 86.3226L151.53 87.4998ZM119.097 109.421L115.869 105.603L112.05 108.831L115.278 112.649ZM121.742 112.55L117.924 115.778L121.152 119.596L124.97 116.368ZM153.672 96.3413L154.849 101.201L159.708 100.023L158.531 95.1641ZM253.294 161.699L258.255 161.07L257.626 156.11L252.666 156.738ZM247.59 203.639L245.66 208.251L250.272 210.182L252.203 205.569ZM243.811 202.057L239.198 200.126L237.268 204.739L241.88 206.669ZM249.23 162.214L248.601 157.253L243.641 157.882L244.269 162.842ZM172 90.0557V85.0557H167V90.0557H172ZM208.528 98.6474L206.299 103.123L206.299 103.123ZM237.396 122.621L240.409 126.611L244.399 123.598L241.386 119.608ZM234.126 125.09L230.136 128.103L233.149 132.093L237.139 129.08ZM206.701 102.315L204.473 106.791L204.473 106.791ZM172 94.1529H167V99.1529H172V94.1529ZM244.195 133.235L248.601 130.87L246.235 126.465L241.83 128.83ZM250.83 149.623L252.195 154.433L257.005 153.067L255.64 148.257ZM246.888 150.742L242.078 152.107L243.444 156.917L248.254 155.552ZM240.586 135.174L238.22 130.768L233.815 133.134L236.181 137.539ZM234.238 225.304L238.036 228.556L241.288 224.759L237.491 221.506ZM195.159 250.604L196.572 255.4L196.572 255.4ZM148.606 250.534L143.814 249.107L142.386 253.899L147.178 255.326ZM149.775 246.607L151.203 241.816L146.411 240.388L144.983 245.18ZM194.001 246.674L195.415 251.47L195.415 251.47ZM231.126 222.639L234.379 218.841L230.581 215.589L227.329 219.386ZM98.6752 125.28C88.5757 141.13 83.8844 159.826 85.304 178.567L95.2754 177.812C94.0191 161.227 98.1709 144.681 107.109 130.653ZM90.6674 183.175L94.7529 182.866L93.9976 172.895L89.912 173.204ZM99.3609 177.503C98.1715 161.8 102.102 146.135 110.564 132.855L102.131 127.481C92.5071 142.585 88.0368 160.4 89.3895 178.258ZM109.034 125.951L105.579 123.75L100.205 132.183L103.661 134.385ZM88.5405 196.369C93.8083 214.41 104.78 230.259 119.813 241.54L125.815 233.542C112.512 223.558 102.802 209.532 98.1397 193.566ZM227.874 226.436L230.986 229.101L237.491 221.506L234.379 218.841Z" />
                  </g>
                </svg>

                <svg style={{ "--i": 0, "--j": 2 } as React.CSSProperties}>
                  <g id="inner3">
                    <path d="M195.136 135.689C188.115 131.215 179.948 128.873 171.624 128.946C163.299 129.019 155.174 131.503 148.232 136.099L148.42 136.382C155.307 131.823 163.368 129.358 171.627 129.286C179.886 129.213 187.988 131.537 194.954 135.975L195.136 135.689Z" />
                    <path d="M195.136 208.311C188.115 212.784 179.948 215.127 171.624 215.054C163.299 214.981 155.174 212.496 148.232 207.901L148.42 207.618C155.307 212.177 163.368 214.642 171.627 214.714C179.886 214.786 187.988 212.463 194.954 208.025L195.136 208.311Z" />
                    <path mask="url(#path-5-inside-3_111_3212)" fill="var(--cinnabar)" d="M195.136 135.689L195.474 135.904L195.689 135.566L195.351 135.352ZM171.624 128.946L171.627 129.346L171.624 128.946ZM148.232 136.099L148.011 135.765L147.678 135.986L147.899 136.32ZM148.42 136.382L148.086 136.603L148.307 136.936L148.641 136.716ZM171.627 129.286L171.63 129.686L171.627 129.286ZM194.954 135.975L194.739 136.313L195.076 136.528L195.291 136.19ZM195.136 208.311L195.351 208.648L195.689 208.433L195.474 208.096ZM171.624 215.054L171.627 214.654L171.624 215.054ZM148.232 207.901L147.899 207.68L147.678 208.014L148.011 208.234ZM148.42 207.618L148.641 207.284L148.307 207.063L148.086 207.397ZM171.627 214.714L171.63 214.314L171.627 214.714ZM194.954 208.025L195.291 207.81L195.076 207.472L194.739 207.687ZM195.351 135.352C188.265 130.836 180.022 128.473 171.62 128.546L171.627 129.346C179.874 129.274 187.966 131.594 194.921 136.026ZM171.62 128.546C163.218 128.619 155.018 131.127 148.011 135.765L148.453 136.432ZM147.899 136.32L148.086 136.603L148.753 136.161L148.566 135.878ZM148.641 136.716C155.463 132.199 163.448 129.757 171.63 129.686L171.623 128.886ZM171.63 129.686C179.812 129.614 187.839 131.916 194.739 136.313L195.169 135.638ZM195.291 136.19L195.474 135.904L194.799 135.474L194.617 135.76ZM194.921 207.974C187.966 212.406 179.874 214.726 171.627 214.654L171.62 215.454ZM171.627 214.654C163.38 214.582 155.33 212.12 148.453 207.567L148.011 208.234ZM148.566 208.122L147.899 207.68L148.086 207.397L147.899 207.68ZM148.199 207.951C155.15 212.553 163.287 215.041 171.623 215.114L171.63 214.314ZM171.623 215.114C179.959 215.187 188.138 212.842 195.169 208.362L194.739 207.687ZM194.617 208.239L194.799 208.526L195.474 208.096L195.291 207.81Z" />
                  </g>
                  <path stroke="var(--cinnabar)" d="M240.944 172C240.944 187.951 235.414 203.408 225.295 215.738C215.176 228.068 201.095 236.508 185.45 239.62C169.806 242.732 153.567 240.323 139.5 232.804C125.433 225.285 114.408 213.12 108.304 198.384C102.2 183.648 101.394 167.25 106.024 151.987C110.654 136.723 120.434 123.537 133.696 114.675C146.959 105.813 162.884 101.824 178.758 103.388C194.632 104.951 209.472 111.97 220.751 123.249" id="out3" />
                </svg>

                <svg style={{ "--i": 1, "--j": 3 } as React.CSSProperties}>
                  <g id="inner1">
                    <path fill="var(--cinnabar)" d="M145.949 124.51L148.554 129.259C156.575 124.859 165.672 122.804 174.806 123.331C183.94 123.858 192.741 126.944 200.203 132.236C207.665 137.529 213.488 144.815 217.004 153.261C220.521 161.707 221.59 170.972 220.09 179.997L224.108 180.665L224.102 180.699L229.537 181.607C230.521 175.715 230.594 169.708 229.753 163.795L225.628 164.381C224.987 159.867 223.775 155.429 222.005 151.179C218.097 141.795 211.628 133.699 203.337 127.818C195.045 121.937 185.266 118.508 175.118 117.923C165.302 117.357 155.525 119.474 146.83 124.037C146.535 124.192 146.241 124.349 145.949 124.51ZM224.638 164.522C224.009 160.091 222.819 155.735 221.082 151.563C217.246 142.352 210.897 134.406 202.758 128.634C194.62 122.862 185.021 119.496 175.06 118.922C165.432 118.367 155.841 120.441 147.311 124.914L148.954 127.91C156.922 123.745 165.876 121.814 174.864 122.333C184.185 122.87 193.166 126.019 200.782 131.421C208.397 136.822 214.339 144.257 217.928 152.877C221.388 161.188 222.526 170.276 221.23 179.173L224.262 179.677C224.998 174.671 225.35 169.535 224.638 164.522Z" clipRule="evenodd" fillRule="evenodd" />
                    <path fill="var(--cinnabar)" d="M139.91 220.713C134.922 217.428 130.469 213.395 126.705 208.758L130.983 205.286L130.985 205.288L134.148 202.721C141.342 211.584 151.417 217.642 162.619 219.839C173.821 222.036 185.438 220.232 195.446 214.742L198.051 219.491C197.759 219.651 197.465 219.809 197.17 219.963C186.252 225.693 173.696 227.531 161.577 225.154C154.613 223.789 148.041 221.08 142.202 217.234L139.91 220.713ZM142.752 216.399C148.483 220.174 154.934 222.833 161.769 224.173C173.658 226.504 185.977 224.704 196.689 219.087L195.046 216.09C185.035 221.323 173.531 222.998 162.427 220.82C151.323 218.643 141.303 212.747 134.01 204.122L131.182 206.5C134.451 210.376 138.515 213.607 142.752 216.399Z" clipRule="evenodd" fillRule="evenodd" />
                  </g>
                </svg>

                <svg style={{ "--i": 2, "--j": 4 } as React.CSSProperties}>
                  <path fill="var(--cinnabar)" d="M180.956 186.056C183.849 184.212 186.103 181.521 187.41 178.349C188.717 175.177 189.013 171.679 188.258 168.332C187.503 164.986 185.734 161.954 183.192 159.65C180.649 157.346 177.458 155.883 174.054 155.46C170.649 155.038 167.197 155.676 164.169 157.288C161.14 158.9 158.683 161.407 157.133 164.468C155.582 167.528 155.014 170.992 155.505 174.388C155.997 177.783 157.524 180.944 159.879 183.439L161.129 182.259C159.018 180.021 157.648 177.186 157.207 174.141C156.766 171.096 157.276 167.989 158.667 165.245C160.057 162.5 162.261 160.252 164.977 158.806C167.693 157.36 170.788 156.788 173.842 157.167C176.895 157.546 179.757 158.858 182.037 160.924C184.317 162.99 185.904 165.709 186.581 168.711C187.258 171.712 186.992 174.849 185.82 177.694C184.648 180.539 182.627 182.952 180.032 184.606L180.956 186.056Z" id="center1" />
                  <path fill="var(--cinnabar)" d="M172 166.445C175.068 166.445 177.556 168.932 177.556 172C177.556 175.068 175.068 177.556 172 177.556C168.932 177.556 166.444 175.068 166.444 172C166.444 168.932 168.932 166.445 172 166.445ZM172 177.021C174.773 177.021 177.021 174.773 177.021 172C177.021 169.227 174.773 166.979 172 166.979C169.227 166.979 166.979 169.227 166.979 172C166.979 174.773 169.227 177.021 172 177.021Z" id="center" />
                </svg>
              </div>
            </div>

            {/* Micro details panel under core */}
            <div className="border-t border-ink/15 pt-3 flex justify-between items-center text-[10px] font-mono text-ink-muted">
              <span className="flex items-center gap-1">
                <RefreshCw className={`h-3 w-3 ${isExecuting ? "animate-spin text-cinnabar" : ""}`} />
                <span>SYNC RATE: 100%</span>
              </span>
              <span>SECTOR: 0x47B2</span>
              <span className="text-cinnabar font-bold">HOVER FOR 3D ANALYSIS</span>
            </div>
          </section>

          {/* Right trace log console */}
          <LogConsole logs={logs} />
        </div>

        {/* HUD Stats Footer */}
        <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="manga-panel p-4 flex items-center justify-between group">
            <div>
              <p className="text-[9px] text-ink-muted font-bold uppercase tracking-widest font-mono">Active Agents</p>
              <h3 className="text-2xl font-bold font-mono mt-1 text-ink tracking-tight">12</h3>
            </div>
            <Cpu className="h-5 w-5 text-ink-muted group-hover:text-cinnabar transition-colors" />
          </div>

          <div className="manga-panel p-4 flex items-center justify-between group">
            <div>
              <p className="text-[9px] text-ink-muted font-bold uppercase tracking-widest font-mono">Running Flows</p>
              <h3 className="text-2xl font-bold font-mono mt-1 text-ink tracking-tight">
                {isExecuting ? "4" : "3"}
              </h3>
            </div>
            <Activity className="h-5 w-5 text-ink-muted group-hover:text-cinnabar transition-colors" />
          </div>

          <div className="manga-panel p-4 flex items-center justify-between group">
            <div>
              <p className="text-[9px] text-ink-muted font-bold uppercase tracking-widest font-mono">Queue Latency</p>
              <h3 className="text-2xl font-bold font-mono mt-1 text-ink tracking-tight">2ms</h3>
            </div>
            <Zap className="h-5 w-5 text-ink-muted group-hover:text-cinnabar transition-colors" />
          </div>

          <div className="manga-panel p-4 flex items-center justify-between group">
            <div>
              <p className="text-[9px] text-ink-muted font-bold uppercase tracking-widest font-mono">Secrets Vault</p>
              <h3 className="text-2xl font-bold font-mono mt-1 text-ink tracking-tight">4</h3>
            </div>
            <ShieldAlert className="h-5 w-5 text-ink-muted group-hover:text-cinnabar transition-colors" />
          </div>
        </section>
      </main>
    </div>
  );
}
