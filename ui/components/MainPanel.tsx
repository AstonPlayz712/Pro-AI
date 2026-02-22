"use client";

/** Main panel that swaps content based on the current mode. */

import React from "react";

import { useModeManager } from "../hooks/useModeManager";
import { SmartModeView } from "../modes/SmartModeView";
import { DebugModeView } from "../modes/DebugModeView";
import { AutomationModeView } from "../modes/AutomationModeView";
import { InsightModeView } from "../modes/InsightModeView";

export function MainPanel(): React.JSX.Element {
  const { mode } = useModeManager();

  return (
    <main className="vsc-main" aria-label="Main panel">
      {mode === "smart" && <SmartModeView />}
      {mode === "debug" && <DebugModeView />}
      {mode === "automation" && <AutomationModeView />}
      {mode === "insight" && <InsightModeView />}
    </main>
  );
}
