"use client";

/** Debug mode view placeholder (inspecting model/tool execution). */

import React from "react";

export function DebugModeView(): React.JSX.Element {
  return (
    <section className="vsc-mode" aria-label="Debug mode">
      <div className="vsc-panel-title">Debug</div>
      <div className="vsc-panel-body">
        <div className="vsc-muted">Placeholder view for Debug mode.</div>
      </div>
    </section>
  );
}
