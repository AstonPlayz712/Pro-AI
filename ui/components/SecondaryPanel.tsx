"use client";

/** Secondary panel placeholder for logs, debugging output, and process monitoring. */

import React from "react";

export function SecondaryPanel(): React.JSX.Element {
  return (
    <section className="vsc-secondary" aria-label="Secondary panel">
      <div className="vsc-panel-title">Secondary Panel</div>
      <div className="vsc-panel-body">
        <div className="vsc-muted">Logs, debug output, and process monitoring will appear here.</div>
      </div>
    </section>
  );
}
