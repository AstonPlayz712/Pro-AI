"use client";

import React from "react";

import { useConnectivity } from "../hooks/useConnectivity";

export function ConnectivityIndicator(): React.JSX.Element {
  const { state } = useConnectivity();

  const online = state?.online ?? false;
  const realInternet = state?.realInternet ?? false;
  const slow = state?.isSlow ?? false;

  let label = "…";
  if (!online) label = "Offline";
  else if (!realInternet) label = "Unstable";
  else if (slow) label = "Slow";
  else label = "Online";

  return (
    <div className="vsc-conn" aria-label="Connectivity indicator" title={label}>
      <span className={`vsc-conn__dot ${label.toLowerCase()}`} />
      <span className="vsc-conn__text">{label}</span>
    </div>
  );
}
