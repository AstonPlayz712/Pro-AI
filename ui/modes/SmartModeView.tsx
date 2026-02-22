"use client";

/** Smart mode view placeholder (primary AI interaction surface). */

import React from "react";

import { ChatPanel } from "../components/ChatPanel";

export function SmartModeView(): React.JSX.Element {
  return (
    <section className="vsc-mode" aria-label="Smart mode">
      <div className="vsc-panel-title">Smart</div>
      <div className="vsc-panel-body">
        <ChatPanel />
      </div>
    </section>
  );
}
