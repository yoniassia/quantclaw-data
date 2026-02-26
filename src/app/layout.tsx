import type { Metadata } from "next";
import "./globals.css";
import "./terminal-theme.css";

export const metadata: Metadata = {
  title: "QuantClaw Data Terminal — Bloomberg-Style Financial Intelligence",
  description: "402+ financial data modules built autonomously by AI agents. Bloomberg-style terminal interface with real-time market data, options flow, macro indicators, and alternative data. Zero API keys. MCP-ready. Free and open.",
  keywords: ["quantclaw", "bloomberg terminal", "financial data", "MCP", "AI agents", "market data", "quant trading", "SEC EDGAR", "options", "crypto", "macro economics", "alternative data"],
  openGraph: {
    title: "QuantClaw Data Terminal — Bloomberg-Style Financial Intelligence",
    description: "402+ self-built financial modules. 194 data sources. Bloomberg-style terminal UI. Zero API keys. MCP-ready.",
    url: "https://quantclaw.org",
    siteName: "QuantClaw",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "QuantClaw Data Terminal — AI-Built Financial Intelligence",
    description: "402+ financial data modules in a Bloomberg-style terminal. Free. Open. MCP-ready.",
    creator: "@YoniAssia",
  },
  robots: {
    index: true,
    follow: true,
  },
  other: {
    "ai-plugin": "/.well-known/ai-plugin.json",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="terminal-body">
        {children}
      </body>
    </html>
  );
}
