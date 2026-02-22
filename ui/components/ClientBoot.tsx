"use client";

import { useEffect } from "react";

import { installSyncOnConnectivity } from "../sync/offlineSync";

export function ClientBoot(): null {
  useEffect(() => {
    installSyncOnConnectivity();
  }, []);

  return null;
}
