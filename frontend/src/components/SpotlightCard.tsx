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
  glowColor = "rgba(255, 255, 255, 0.02)"
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
        "manga-panel relative overflow-hidden p-5 transition-all duration-200 group focus-within:ring-1 focus-within:ring-cinnabar/20",
        className
      )}
      style={{
        "--mouse-x": `${coords.x}px`,
        "--mouse-y": `${coords.y}px`,
      } as React.CSSProperties}
    >
      {/* Dynamic spotlight hover glow */}
      <div
        className="absolute inset-0 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{
          background: `radial-gradient(200px circle at var(--mouse-x) var(--mouse-y), rgba(179, 58, 58, 0.04), transparent 80%)`,
        }}
      />
      
      <div className="relative z-10 h-full w-full">
        {children}
      </div>
    </div>
  );
};
