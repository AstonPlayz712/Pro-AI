"use client";

import React from "react";
import WorkspaceShell from "../components/layout/WorkspaceShell";
import TopBar from "../components/layout/TopBar";
import LeftNav from "../components/layout/LeftNav";
import MainWorkspace from "../components/layout/MainWorkspace";
import DAIPanel from "../components/dai/DAIPanel";
import AutoCommandSurface from "../components/acs/AutoCommandSurface";
import ChipBar from "../components/chips/ChipBar";

/**
 * Auto Workspace — root page.
 *
 * Viewport layout:
 *   ┌──────────────────────────────────────────┐
 *   │                 TopBar                   │
 *   ├──────────┬───────────────────┬───────────┤
 *   │          │     ChipBar       │           │
 *   │ LeftNav  ├───────────────────┤ DAIPanel  │
 *   │          │  MainWorkspace    │           │
 *   │          ├───────────────────┤           │
 *   │          │       ACS         │           │
 *   └──────────┴───────────────────┴───────────┘
 */
export default function AutoPage() {
  return (
    <WorkspaceShell>
      {/* Top bar spans full width */}
      <TopBar />

      {/* Body row: nav + centre + DAI panel */}
      <div
        style={{
          display: "flex",
          flex: 1,
          overflow: "hidden",
        }}
      >
        <LeftNav />

        {/* Centre column */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <ChipBar />
          <MainWorkspace />
          <AutoCommandSurface />
        </div>

        <DAIPanel />
      </div>
    </WorkspaceShell>
  );
}

