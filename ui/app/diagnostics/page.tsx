"use client";

import React, { useEffect, useState } from "react";

type LocalDiag = { ok: boolean; elapsedMs?: number; chunks?: number; chars?: number; cps?: number; error?: string };

export default function DiagnosticsPage(): React.JSX.Element {
  const [result, setResult] = useState<LocalDiag | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const resp = await fetch("/api/diagnostics/local", { cache: "no-store" });
      const json = (await resp.json()) as LocalDiag;
      setResult(json);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void run();
  }, []);

  return (
    <div style={{ padding: 12 }}>
      <h2 style={{ margin: "0 0 10px 0" }}>Local Engine Diagnostics</h2>
      <button className="vsc-command__btn" onClick={() => void run()} disabled={loading}>
        {loading ? "Running…" : "Run local test"}
      </button>

      <pre style={{ marginTop: 12, background: "var(--vsc-surface)", padding: 12, borderRadius: 8, border: "1px solid var(--vsc-border)" }}>
        {JSON.stringify(result, null, 2)}
      </pre>
    </div>
  );
}
