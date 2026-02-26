"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { listSyncQueueItems } from "../storage/db";

export function useSyncStatus() {
  const [pendingCount, setPendingCount] = useState(0);

  const refresh = useCallback(async () => {
    const items = await listSyncQueueItems(500);
    setPendingCount(items.length);
  }, []);

  useEffect(() => {
    const t0 = window.setTimeout(() => void refresh(), 0);
    const t = window.setInterval(() => void refresh(), 2000);
    return () => {
      window.clearTimeout(t0);
      window.clearInterval(t);
    };
  }, [refresh]);

  return useMemo(() => ({ pendingCount, refresh }), [pendingCount, refresh]);
}
