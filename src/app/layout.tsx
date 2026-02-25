import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QuantClaw Data — Financial Intelligence Platform",
  description: "39+ financial data modules with MCP integration. Real-time prices, options, technicals, crypto, macro, and more.",
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
