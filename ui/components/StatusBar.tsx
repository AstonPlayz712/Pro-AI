"use client";

/** Status bar showing current mode and system status. */

import React from "react";

import { useModeManager } from "../hooks/useModeManager";
import { ConnectivityIndicator } from "./ConnectivityIndicator";

export function StatusBar(): React.JSX.Element {
  const { mode } = useModeManager();

  return (
    <footer className="vsc-status" aria-label="Status bar">
      <div className="vsc-status__left">
        <span className="vsc-status__item">Mode: {mode}</span>
      </div>
      <div className="vsc-status__right">
        <span className="vsc-status__item">System: Placeholder</span>
        <ConnectivityIndicator />
      </div>
    </footer>
  );
}
