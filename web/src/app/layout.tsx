import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "x402 Micropay Demo",
  description: "Casper x402 Integration for AI Agent Micropayments",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
