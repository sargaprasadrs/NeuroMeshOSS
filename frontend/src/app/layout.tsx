import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "./providers";
import "@/app/globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "NeuroMeshOSS — AI Agent Orchestration Platform",
  description: "Build, schedule, trace, and execute autonomous multi-agent workflows.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} dark antialiased`}>
      <body className="font-sans bg-neutral-900 text-neutral-50 overflow-x-hidden min-h-screen">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
