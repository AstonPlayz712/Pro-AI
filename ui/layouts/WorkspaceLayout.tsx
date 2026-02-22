"use client";

/** Workspace layout assembling the VS Code–inspired shell. */

import React from "react";

import { Sidebar } from "../components/Sidebar";
import { MainPanel } from "../components/MainPanel";
import { SecondaryPanel } from "../components/SecondaryPanel";
import { StatusBar } from "../components/StatusBar";
import { CommandPalette, type CommandEvent } from "../components/CommandPalette";
import { ModeBanner } from "../components/ModeBanner";
import { ClientBoot } from "../components/ClientBoot";

export function WorkspaceLayout(): React.JSX.Element {
  const handleCommand = (event: CommandEvent) => {
    // Placeholder event sink; replace with command routing later.
    // Intentionally no real behavior beyond keeping a clean scaffold.
    void event;
  };

  return (
    <div className="vsc-root">
      <ClientBoot />
      <div className="vsc-workbench">
        <Sidebar />
        <div className="vsc-editor">
          <ModeBanner />
          <div className="vsc-panels">
            <MainPanel />
            <SecondaryPanel />
          </div>
          <StatusBar />
        </div>
      </div>

      <div className="vsc-command-dock">
        <CommandPalette onCommand={handleCommand} />
      </div>
    </div>
  );
}
