import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QuantClaw Data — AI-Built Financial Intelligence Platform",
  description: "200+ financial data modules built autonomously by AI agents. Equities, crypto, macro, fixed income, commodities, and alternative data. Zero API keys. MCP-ready. Free and open.",
  keywords: ["quantclaw", "financial data", "MCP", "AI agents", "market data", "quant trading", "SEC EDGAR", "options", "crypto", "macro economics", "alternative data"],
  openGraph: {
    title: "QuantClaw Data — AI Agents That Build Their Own Financial Arsenal",
    description: "200+ self-built financial modules. 43 data sources. 113K+ lines of autonomous code. Zero API keys. MCP-ready.",
    url: "https://quantclaw.org",
    siteName: "QuantClaw",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "QuantClaw Data — AI-Built Financial Intelligence",
    description: "200+ financial data modules built by AI agents. Free. Open. MCP-ready.",
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
      <body className="bg-[#000021] text-white min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
