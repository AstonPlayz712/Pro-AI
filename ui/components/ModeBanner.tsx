"use client";

import React from "react";

import { useConnectivity } from "../hooks/useConnectivity";
import { ensureDefaultSettings } from "../storage/db";
import { selectEngine } from "../core/engineSelector";
import { useAiModeManager } from "../hooks/useAiModeManager";

export function ModeBanner(): React.JSX.Element {
  const { state } = useConnectivity();
  const { currentMode } = useAiModeManager();
  const [detail, setDetail] = React.useState<string>("");
  const [headline, setHeadline] = React.useState<string>("Checking connectivity…");

  React.useEffect(() => {
    let cancelled = false;
    void (async () => {
      if (!state) return;
      const settings = await ensureDefaultSettings();
      const sel = await selectEngine(settings.engineMode, { connectivity: state });

      const typeText =
        state.type === "wifi"
          ? "Connected via Wi‑Fi"
          : state.type === "cellular"
            ? "Connected via Mobile Data"
            : state.type === "ethernet"
              ? "Connected via Ethernet"
              : "";

      const head =
        sel.engineId === "cloud"
          ? "Online · Cloud model · Full capabilities"
          : state.online
            ? "Local model · Reduced capabilities"
            : "Offline · Local model · Reduced capabilities";

      if (!cancelled) {
        setHeadline(`${head} · AI mode: ${currentMode}`);
        setDetail([typeText, sel.decision.reason].filter(Boolean).join(" · "));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [currentMode, state]);

  return (
    <div className="vsc-banner" role="status" aria-label="Connectivity banner">
      <div className="vsc-banner__headline">{headline}</div>
      {detail && <div className="vsc-banner__detail">{detail}</div>}
    </div>
  );
}
