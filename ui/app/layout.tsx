import type { Metadata } from "next";

import "./globals.css";
import "../styles/theme.css";
import "../styles/layout.css";

import { ModeProvider } from "../context/ModeContext";
import { ProjectProvider } from "../context/ProjectContext";
import { AiModeProvider } from "../context/AiModeContext";

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
        <ModeProvider>
          <ProjectProvider>
            <AiModeProvider>{children}</AiModeProvider>
          </ProjectProvider>
        </ModeProvider>
      </body>
    </html>
  );
}
