"use client";

/** Secondary panel placeholder for logs, debugging output, and process monitoring. */

import React from "react";

import { useProjectManager } from "../hooks/useProjectManager";

export function SecondaryPanel(): React.JSX.Element {
  const { project } = useProjectManager();

  return (
    <section className="vsc-secondary" aria-label="Secondary panel">
      <div className="vsc-panel-title">Secondary Panel</div>
      <div className="vsc-panel-body">
        <div className="vsc-muted">Logs, debug output, and process monitoring will appear here.</div>
        <hr className="vsc-hr" />
        <div className="vsc-kv__row">
          <div className="vsc-kv__k">Project</div>
          <div className="vsc-kv__v">{project.name}</div>
        </div>
        <div className="vsc-kv__row">
          <div className="vsc-kv__k">Capabilities</div>
          <div className="vsc-kv__v">{project.capabilities.join(", ")}</div>
        </div>
      </div>
    </section>
  );
}
