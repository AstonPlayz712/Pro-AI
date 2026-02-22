import type { Metadata } from "next";

import "./globals.css";
import "../styles/theme.css";
import "../styles/layout.css";

import { ModeProvider } from "../context/ModeContext";

export const metadata: Metadata = {
  title: "AI Workspace UI",
  description: "VS Code–style workspace UI scaffold for an AI system.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ModeProvider>{children}</ModeProvider>
      </body>
    </html>
  );
}
