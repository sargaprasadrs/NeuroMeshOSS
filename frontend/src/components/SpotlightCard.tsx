"use client";

import React, { useRef, useState } from "react";
import clsx from "clsx";

interface SpotlightCardProps {
  children: React.ReactNode;
  className?: string;
  glowColor?: string;
}

export const SpotlightCard: React.FC<SpotlightCardProps> = ({ 
  children, 
  className,
  glowColor = "rgba(16, 185, 129, 0.08)"
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [coords, setCoords] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setCoords({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      className={clsx(
        "relative overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 transition-all duration-300 hover:border-zinc-700/80 group focus-within:ring-1 focus-within:ring-emerald-500/50",
        className
      )}
      style={{
        "--mouse-x": `${coords.x}px`,
        "--mouse-y": `${coords.y}px`,
      } as React.CSSProperties}
    >
      {/* Spotlight fill glow (subtle, 60fps) */}
      <div
        className="absolute inset-0 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        style={{
          background: `radial-gradient(150px circle at var(--mouse-x) var(--mouse-y), ${glowColor}, transparent 80%)`,
        }}
      />
      
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};
