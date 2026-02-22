"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { getConnectivityState } from "../core/connectivity";
import { recordTelemetryEvent } from "../telemetry/telemetry";

export function useConnectivity() {
  const [state, setState] = useState<Awaited<ReturnType<typeof getConnectivityState>> | null>(null);

  const refresh = useCallback(async () => {
    const next = await getConnectivityState();
    setState(next);
    recordTelemetryEvent({ type: "connectivity", ts: Date.now(), data: next as unknown as Record<string, unknown> });
  }, []);

  useEffect(() => {
    const t = window.setTimeout(() => {
      void refresh();
    }, 0);

    const onOnline = () => void refresh();
    const onOffline = () => void refresh();

    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);

    const anyNav = navigator as unknown as { connection?: { addEventListener?: (n: string, cb: () => void) => void; removeEventListener?: (n: string, cb: () => void) => void } };
    const conn = anyNav.connection;
    const onConn = () => void refresh();

    conn?.addEventListener?.("change", onConn);

    return () => {
      window.clearTimeout(t);
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
      conn?.removeEventListener?.("change", onConn);
    };
  }, [refresh]);

  return useMemo(() => ({ state, refresh }), [state, refresh]);
}
