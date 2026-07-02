"use client";

import { useState, useEffect } from "react";

const SWARM_CONCEPTS: Record<string, string> = {
  Stigmergy: "Indirect coordination through environmental cues, like pheromone paths left by foraging bees.",
  "Self-Organization": "Global order emerging from local interactions among individuals, without any central lead.",
  "Feedback Loops": "Positive loops amplify useful behaviors, while negative loops stabilize the colony structure.",
  Decentralization: "System operations distributed across the swarm, preventing single points of failure.",
  Emergence: "Complex, intelligent behavior arising from simple agents following basic local rules.",
  "Local Rules": "Individuals react only to their immediate neighbors and environment, requiring no global map.",
  "Swarm Intel": "Collective behavior of self-organized systems, outperforming any single individual.",
};

const CONCEPT_KEYS = Object.keys(SWARM_CONCEPTS);

export default function SwarmIntelligence() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const radius = 22; // Hex radius (scaled down to fit as dashboard card)
  const hexWidth = radius * 1.5;
  const hexHeight = radius * Math.sqrt(3);

  const rows = 3;
  const cols = 5;
  const cells: { id: number; r: number; c: number; cx: number; cy: number; label: string }[] = [];

  let idx = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const cx = c * hexWidth + 30;
      const cy = r * hexHeight + (c % 2 === 0 ? 0 : hexHeight / 2) + 25;
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
    return Math.sqrt(dx * dx + dy * dy) / (radius * 1.73);
  };

  const activeLabel = hoveredIndex !== null ? cells[hoveredIndex]?.label : null;
  const activeDesc = activeLabel ? SWARM_CONCEPTS[activeLabel] : null;

  if (!mounted) return null;

  return (
    <div className="flex flex-col items-center gap-4 w-full max-w-[340px] select-none">
      <svg
        viewBox="0 0 160 120"
        className="w-full h-auto max-h-[110px]"
        style={{ overflow: "visible" }}
      >
        {cells.map((cell) => {
          const distance = hoveredIndex !== null ? getDistance(hoveredIndex, cell.id) : 0;
          const isHovered = hoveredIndex === cell.id;
          const isNear = hoveredIndex !== null && distance < 2.5;

          const delay = hoveredIndex !== null ? distance * 70 : 0;

          let opacity = 0.5;
          let strokeColor = "rgba(63, 63, 70, 0.3)";
          let fillColor = "rgba(24, 24, 27, 0.1)";

          if (hoveredIndex !== null) {
            if (isHovered) {
              opacity = 1.0;
              strokeColor = "rgba(16, 185, 129, 0.95)"; // Emerald
              fillColor = "rgba(16, 185, 129, 0.15)";
            } else if (isNear) {
              const strength = 1 - distance / 2.5;
              opacity = 0.2 + strength * 0.6;
              strokeColor = `rgba(16, 185, 129, ${0.3 + strength * 0.5})`;
              fillColor = `rgba(16, 185, 129, ${strength * 0.08})`;
            } else {
              opacity = 0.08;
            }
          }

          const cx = cell.cx;
          const cy = cell.cy;
          const w = radius * Math.sqrt(3);
          const pathD = `
            M ${cx} ${cy - radius}
            L ${cx + w / 2} ${cy - radius / 2}
            L ${cx + w / 2} ${cy + radius / 2}
            L ${cx} ${cy + radius}
            L ${cx - w / 2} ${cy + radius / 2}
            L ${cx - w / 2} ${cy - radius / 2}
            Z
          `;

          return (
            <g
              key={cell.id}
              onMouseEnter={() => setHoveredIndex(cell.id)}
              onMouseLeave={() => setHoveredIndex(null)}
              className="cursor-pointer"
            >
              <path
                d={pathD}
                fill={fillColor}
                stroke={strokeColor}
                strokeWidth={isHovered ? 1.5 : 1}
                style={{
                  opacity,
                  transition: "all 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
                  transitionDelay: hoveredIndex !== null ? `${delay}ms` : "0ms",
                }}
              />
            </g>
          );
        })}
      </svg>

      <div className="h-10 text-center flex items-center justify-center">
        {activeLabel && activeDesc ? (
          <div>
            <h6 className="text-emerald-500 text-[10px] uppercase font-bold tracking-wider mb-0.5">{activeLabel}</h6>
            <p className="text-[10px] text-zinc-400 max-w-[280px] leading-snug">{activeDesc}</p>
          </div>
        ) : (
          <p className="text-[10px] text-zinc-500 italic">Hover hex cells to trigger communication waves</p>
        )}
      </div>
    </div>
  );
}
