"use client";

import React, { useState, useEffect } from "react";

const NETWORK_CONCEPTS: Record<string, string> = {
  "Stigmergy Relay": "Decentralized node-to-node memory signaling and environmental routing logs.",
  "Self-Organization Core": "Dynamic flow execution and path resolving without gateway controllers.",
  "Feedback Balancer": "Real-time query distribution across local active worker networks.",
  "Decentralized State": "Isolated micro-agent executions preventing central failure blocks.",
  "Emergent Compiler": "High-level visual graph compiled from individual node rule sets.",
  "Consensus Gateway": "Sub-millisecond validation layers routing signals between adjacent hosts.",
  "Cognitive Swarm": "Collaborative neural execution states resolving complex tasks in parallel.",
};

const CONCEPT_KEYS = Object.keys(NETWORK_CONCEPTS);

export default function SwarmIntelligence() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [mounted, setMounted] = useState(false);
  const [activeSignals, setActiveSignals] = useState<boolean[]>([]);

  useEffect(() => {
    setMounted(true);
    setActiveSignals(Array.from({ length: 15 }, () => Math.random() > 0.5));

    // Periodic subtle activation shifts
    const interval = setInterval(() => {
      setActiveSignals((prev) =>
        prev.map((val) => (Math.random() > 0.8 ? !val : val))
      );
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const spacingX = 42;
  const spacingY = 40;
  const rows = 3;
  const cols = 5;
  const cells: { id: number; r: number; c: number; cx: number; cy: number; label: string }[] = [];

  let idx = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      // Stagger layout for an organic mesh look
      const cx = c * spacingX + 22 + (r % 2 === 1 ? spacingX / 2 : 0);
      const cy = r * spacingY + 22;
      cells.push({
        id: idx,
        r,
        c,
        cx,
        cy,
        label: CONCEPT_KEYS[idx % CONCEPT_KEYS.length],
      });
      idx++;
    }
  }

  const getDistance = (idxA: number, idxB: number) => {
    const cellA = cells[idxA];
    const cellB = cells[idxB];
    if (!cellA || !cellB) return 0;
    const dx = cellA.cx - cellB.cx;
    const dy = cellA.cy - cellB.cy;
    return Math.sqrt(dx * dx + dy * dy) / spacingX;
  };

  const activeLabel = hoveredIndex !== null ? cells[hoveredIndex]?.label : null;
  const activeDesc = activeLabel ? NETWORK_CONCEPTS[activeLabel] : null;

  if (!mounted) return null;

  return (
    <div className="flex flex-col items-center gap-5 w-full select-none">
      <svg
        viewBox="0 0 210 124"
        className="w-full h-auto max-h-[140px]"
        style={{ overflow: "visible" }}
      >
        {/* Draw connection paths */}
        <g stroke="rgba(244, 244, 245, 0.04)" strokeWidth="1">
          {cells.map((cellA) =>
            cells.map((cellB) => {
              if (cellA.id < cellB.id) {
                const dist = getDistance(cellA.id, cellB.id);
                // Draw lines between near neighbors
                if (dist > 0.8 && dist < 1.3) {
                  const isHighlighted =
                    hoveredIndex !== null &&
                    (hoveredIndex === cellA.id || hoveredIndex === cellB.id);
                  return (
                    <line
                      key={`${cellA.id}-${cellB.id}`}
                      x1={cellA.cx}
                      y1={cellA.cy}
                      x2={cellB.cx}
                      y2={cellB.cy}
                      stroke={
                        isHighlighted
                          ? "rgba(16, 185, 129, 0.3)" // Subtle emerald connection glow
                          : "rgba(244, 244, 245, 0.05)"
                      }
                      strokeWidth={isHighlighted ? 1.2 : 0.8}
                      className="transition-all duration-300"
                    />
                  );
                }
              }
              return null;
            })
          )}
        </g>

        {/* Draw nodes */}
        {cells.map((cell) => {
          const isHovered = hoveredIndex === cell.id;
          const isSignalActive = activeSignals[cell.id] ?? false;

          let radius = 4;
          let nodeStroke = "border-zinc-800";
          let nodeFill = "rgba(39, 39, 42, 0.4)"; // zinc-800/40
          let nodeOpacity = 0.6;

          if (isHovered) {
            radius = 6;
            nodeStroke = "#10b981"; // Emerald accent
            nodeFill = "rgba(16, 185, 129, 0.15)";
            nodeOpacity = 1.0;
          } else if (isSignalActive) {
            nodeFill = "rgba(244, 244, 245, 0.3)";
            nodeOpacity = 0.8;
          }

          return (
            <g
              key={cell.id}
              onMouseEnter={() => setHoveredIndex(cell.id)}
              onMouseLeave={() => setHoveredIndex(null)}
              className="cursor-pointer"
            >
              {/* Outer hover ring */}
              {isHovered && (
                <circle
                  cx={cell.cx}
                  cy={cell.cy}
                  r={10}
                  fill="none"
                  stroke="rgba(16, 185, 129, 0.15)"
                  strokeWidth="1.5"
                  className="animate-ping"
                />
              )}
              {/* Core Node */}
              <circle
                cx={cell.cx}
                cy={cell.cy}
                r={radius}
                fill={nodeFill}
                stroke={isHovered ? nodeStroke : "rgba(113, 113, 122, 0.2)"}
                strokeWidth={isHovered ? 1.5 : 1}
                opacity={nodeOpacity}
                style={{
                  transition: "all 200ms cubic-bezier(0.4, 0, 0.2, 1)",
                }}
              />
            </g>
          );
        })}
      </svg>

      {/* Dynamic Status Text (Linear Style) */}
      <div className="h-12 w-full text-center flex items-center justify-center bg-zinc-950 border border-zinc-900 rounded-md px-4 py-2">
        {activeLabel && activeDesc ? (
          <div className="flex flex-col items-center gap-0.5">
            <span className="text-[10px] uppercase font-semibold text-emerald-500 tracking-wider">
              {activeLabel}
            </span>
            <span className="text-[10px] text-zinc-400 font-normal leading-tight max-w-[280px]">
              {activeDesc}
            </span>
          </div>
        ) : (
          <span className="text-[10px] text-zinc-500 font-medium">
            Hover network nodes to analyze telemetry relays
          </span>
        )}
      </div>
    </div>
  );
}
