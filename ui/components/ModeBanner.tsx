"use client";

import React from "react";

import { useConnectivity } from "../hooks/useConnectivity";

export function ModeBanner(): React.JSX.Element {
  const { state } = useConnectivity();

  const online = state?.online ?? false;
  const realInternet = state?.realInternet ?? false;
  const slow = state?.isSlow ?? false;
  const type = state?.type ?? "unknown";

  let headline = "Checking connectivity…";
  if (!online) headline = "Offline · Local model · Reduced capabilities";
  else if (online && !realInternet) headline = "Online (unstable) · Local model · Reduced capabilities";
  else if (slow) headline = "Slow connection detected — using local model";
  else headline = "Online · Cloud model · Full capabilities";

  const detail = type === "wifi" ? "Connected via Wi‑Fi" : type === "cellular" ? "Connected via Mobile Data" : "";

  return (
    <div className="vsc-banner" role="status" aria-label="Connectivity banner">
      <div className="vsc-banner__headline">{headline}</div>
      {detail && <div className="vsc-banner__detail">{detail}</div>}
    </div>
  );
}
