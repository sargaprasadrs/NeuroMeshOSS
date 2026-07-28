"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "ghost" | "destructive" | "outline";
  size?: "default" | "sm" | "lg" | "icon";
}

const variantStyles = {
  default: "bg-white text-neutral-900 hover:bg-neutral-100 border border-neutral-200",
  secondary: "bg-neutral-800 text-neutral-200 hover:bg-neutral-700 border border-neutral-700",
  ghost: "bg-transparent text-neutral-300 hover:text-white hover:bg-white/5",
  destructive: "bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20",
  outline: "bg-transparent text-neutral-300 hover:bg-white/5 border border-neutral-700",
};

const sizeStyles = {
  default: "h-10 px-4 py-2 text-sm",
  sm: "h-8 px-3 text-xs",
  lg: "h-12 px-6 text-base",
  icon: "h-10 w-10",
};

export function Button({
  variant = "default",
  size = "default",
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neutral-400 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-900",
        "disabled:pointer-events-none disabled:opacity-50",
        "active:scale-[0.98]",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
