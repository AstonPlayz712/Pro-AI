"use client";

import { addSyncQueueItem, getSettings, listSyncQueueItems, removeSyncQueueItem } from "../storage/db";
import { getConnectivityState } from "../core/connectivity";
import { recordTelemetryEvent } from "../telemetry/telemetry";

export async function enqueueSettingsSync(): Promise<void> {
  const settings = await getSettings();
  if (!settings) return;

  await addSyncQueueItem({
    id: `settings:${Date.now()}`,
    kind: "settings",
    payload: settings,
    createdAt: Date.now(),
  });
}

export async function syncPendingItems(): Promise<void> {
  const state = await getConnectivityState();
  const stable = state.realInternet && !state.isSlow;

  if (!stable) return;

  const items = await listSyncQueueItems(100);
  if (!items.length) return;

  // Placeholder sync endpoint.
  for (const item of items) {
    try {
      await fetch("/api/sync", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(item),
      });

      await removeSyncQueueItem(item.id);
      recordTelemetryEvent({ type: "sync", ts: Date.now(), data: { kind: item.kind } });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      recordTelemetryEvent({ type: "sync_error", ts: Date.now(), data: { error: message } });
      break;
    }
  }
}

export function installSyncOnConnectivity(): void {
  const run = () => void syncPendingItems();
  window.addEventListener("online", run);

  const anyNav = navigator as unknown as { connection?: { addEventListener?: (n: string, cb: () => void) => void } };
  anyNav.connection?.addEventListener?.("change", run);
}
