"use client";

/** VS Code–style sidebar that hosts mode buttons. */

import React from "react";

import { ModeButton } from "./ModeButton";
import { useModeManager } from "../hooks/useModeManager";

export function Sidebar(): React.JSX.Element {
  const { mode, setMode } = useModeManager();

  return (
    <aside className="vsc-sidebar" aria-label="Sidebar">
      <div className="vsc-sidebar__top" />
      <nav className="vsc-sidebar__modes" aria-label="Modes">
        <ModeButton label="Smart" isActive={mode === "smart"} onClick={() => setMode("smart")} />
        <ModeButton label="Debug" isActive={mode === "debug"} onClick={() => setMode("debug")} />
        <ModeButton
          label="Automation"
          isActive={mode === "automation"}
          onClick={() => setMode("automation")}
        />
        <ModeButton label="Insight" isActive={mode === "insight"} onClick={() => setMode("insight")} />
      </nav>
      <div className="vsc-sidebar__bottom" />
    </aside>
  );
}
