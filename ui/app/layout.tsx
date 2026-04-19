import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Auto — Workspace",
  description: "Auto OS-level intelligence workspace powered by DAI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0, height: "100vh", overflow: "hidden" }}>
        {children}
      </body>
    </html>
  );
}

