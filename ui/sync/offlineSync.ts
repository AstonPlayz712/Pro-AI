"use client";

import { addSyncQueueItem, getSettings, listSyncQueueItems, removeSyncQueueItem, type SyncQueueItem } from "../storage/db";
import { getConnectivityState } from "../core/connectivity";
import { recordTelemetryEvent } from "../telemetry/telemetry";

function getOrCreateDeviceId(): string {
  const key = "pro-ai:deviceId";
  const existing = localStorage.getItem(key);
  if (existing) return existing;
  const next = `dev:${Date.now()}:${Math.random().toString(16).slice(2)}`;
  localStorage.setItem(key, next);
  return next;
}

function backoffDelayMs(attempts: number) {
  const base = 1000;
  const max = 60_000;
  const pow = Math.min(10, Math.max(0, attempts));
  return Math.min(max, base * 2 ** pow);
}

export async function enqueueSettingsSync(): Promise<void> {
  const settings = await getSettings();
  if (!settings) return;

  const deviceId = getOrCreateDeviceId();
  await addSyncQueueItem({
    id: `settings:${Date.now()}`,
    kind: "settings",
    payload: settings,
    createdAt: Date.now(),
    updatedAt: settings.updatedAt ?? Date.now(),
    deviceId,
  });
}

export async function syncPendingItems(): Promise<void> {
  const state = await getConnectivityState({ ttlMs: 1500 });
  const stable = state.realInternet && !state.isSlow && state.cloudHealthy;

  if (!stable) return;

  const items = await listSyncQueueItems(200);
  if (!items.length) return;

  const now = Date.now();
  const due = items.filter((i) => (i.nextAttemptAt ?? 0) <= now);
  if (!due.length) return;

  // Batch by kind.
  const batches = new Map<string, SyncQueueItem[]>();
  for (const item of due) {
    const arr = batches.get(item.kind) ?? [];
    arr.push(item);
    batches.set(item.kind, arr);
  }

  for (const [kind, batch] of batches) {
    try {
      const resp = await fetch("/api/sync", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ kind, items: batch }),
      });
      if (!resp.ok) throw new Error(`sync_failed:${resp.status}`);

      const json = (await resp.json().catch(() => null)) as
        | {
            results?: Array<{ id: string | null; ok: boolean }>;
          }
        | null;
      const okIds = new Set(
        (json?.results ?? []).filter((r) => r.ok && r.id).map((r) => String(r.id)),
      );

      let okCount = 0;
      for (const item of batch) {
        if (okIds.size === 0 || okIds.has(item.id)) {
          await removeSyncQueueItem(item.id);
          okCount++;
        }
      }
      recordTelemetryEvent({ type: "sync", ts: Date.now(), data: { kind, okCount, sent: batch.length } });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      recordTelemetryEvent({ type: "sync_error", ts: Date.now(), data: { kind, error: message } });

      // Backoff: re-enqueue updated items with increased attempts/nextAttemptAt.
      for (const item of batch) {
        const attempts = (item.attempts ?? 0) + 1;
        await addSyncQueueItem({
          ...item,
          attempts,
          lastError: message,
          nextAttemptAt: Date.now() + backoffDelayMs(attempts),
        });
      }
      break;
    }
  }
}

export function installSyncOnConnectivity(): void {
  const run = () => void syncPendingItems();
  window.addEventListener("online", run);

  const anyNav = navigator as unknown as { connection?: { addEventListener?: (n: string, cb: () => void) => void } };
  anyNav.connection?.addEventListener?.("change", run);

  // Gentle periodic sync attempt.
  window.setInterval(run, 30_000);
}
