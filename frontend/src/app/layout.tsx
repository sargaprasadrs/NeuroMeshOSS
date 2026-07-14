"use client";

import React, { useState, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { THEMES } from "@/lib/themes";
import "@/app/globals.css"; // Global styles import

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Create query client instance per session instance
  const [queryClient] = useState(() => new QueryClient());

  useEffect(() => {
    const saved = localStorage.getItem("portfolio-theme");
    if (saved) {
      const theme = THEMES.find((t) => t.id === saved);
      if (theme) {
        Object.entries(theme.vars).forEach(([k, v]) => {
          document.documentElement.style.setProperty(k, v);
        });
      }
    } else {
      // Default washi theme properties
      Object.entries(THEMES[0].vars).forEach(([k, v]) => {
        document.documentElement.style.setProperty(k, v);
      });
    }
  }, []);

  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen">
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </body>
    </html>
  );
}
