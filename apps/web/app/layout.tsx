import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TradeMirror",
  description: "RAG chatbot for trading intelligence"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
