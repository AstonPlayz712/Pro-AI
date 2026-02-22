"use client";

import { openDB, type DBSchema } from "idb";

export type Conversation = {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
};

export type StoredMessage = {
  id: string;
  conversationId: string;
  role: "user" | "assistant" | "system";
  content: string;
  createdAt: number;
};

export type SettingsState = {
  engineMode: "auto" | "force-cloud" | "force-local";
  cloudModel: string;
  localModel: string;
};

export type SyncQueueItem = {
  id: string;
  kind: "settings" | "metadata" | "conversation_titles";
  payload: unknown;
  createdAt: number;
};

export type TelemetryEvent = {
  id?: string;
  type:
    | "engine_selected"
    | "engine_error"
    | "connectivity"
    | "cloud_health"
    | "local_health"
    | "sync"
    | "sync_error";
  ts: number;
  data: Record<string, unknown>;
};

interface ProAIDB extends DBSchema {
  conversations: {
    key: string;
    value: Conversation;
    indexes: { "by-updated": number };
  };
  messages: {
    key: string;
    value: StoredMessage;
    indexes: { "by-conversation": string; "by-created": number };
  };
  settings: {
    key: string;
    value: SettingsState;
  };
  syncQueue: {
    key: string;
    value: SyncQueueItem;
    indexes: { "by-created": number };
  };
  telemetry: {
    key: string;
    value: TelemetryEvent & { id: string };
    indexes: { "by-ts": number };
  };
}

const DB_NAME = "pro-ai";
const DB_VERSION = 1;

function makeId(prefix: string) {
  return `${prefix}:${Date.now()}:${Math.random().toString(16).slice(2)}`;
}

async function getDb() {
  return openDB<ProAIDB>(DB_NAME, DB_VERSION, {
    upgrade(db) {
      const conv = db.createObjectStore("conversations", { keyPath: "id" });
      conv.createIndex("by-updated", "updatedAt");

      const msg = db.createObjectStore("messages", { keyPath: "id" });
      msg.createIndex("by-conversation", "conversationId");
      msg.createIndex("by-created", "createdAt");

      db.createObjectStore("settings");

      const q = db.createObjectStore("syncQueue", { keyPath: "id" });
      q.createIndex("by-created", "createdAt");

      const t = db.createObjectStore("telemetry", { keyPath: "id" });
      t.createIndex("by-ts", "ts");
    },
  });
}

export async function getSettings(): Promise<SettingsState | null> {
  const db = await getDb();
  return (await db.get("settings", "default")) ?? null;
}

export async function setSettings(state: SettingsState): Promise<void> {
  const db = await getDb();
  await db.put("settings", state, "default");
}

export async function ensureDefaultSettings(): Promise<SettingsState> {
  const existing = await getSettings();
  if (existing) return existing;
  const defaults: SettingsState = {
    engineMode: "auto",
    cloudModel: "gpt-4o-mini",
    localModel: "phi3",
  };
  await setSettings(defaults);
  return defaults;
}

export async function createConversation(title = "New chat"): Promise<Conversation> {
  const db = await getDb();
  const now = Date.now();
  const conv: Conversation = {
    id: makeId("conv"),
    title,
    createdAt: now,
    updatedAt: now,
  };
  await db.put("conversations", conv);
  return conv;
}

export async function listConversations(limit = 50): Promise<Conversation[]> {
  const db = await getDb();
  const idx = db.transaction("conversations").store.index("by-updated");
  const all = await idx.getAll();
  return all.sort((a, b) => b.updatedAt - a.updatedAt).slice(0, limit);
}

export async function updateConversationTitle(conversationId: string, title: string): Promise<void> {
  const db = await getDb();
  const existing = await db.get("conversations", conversationId);
  if (!existing) return;
  await db.put("conversations", { ...existing, title, updatedAt: Date.now() });
}

export async function addMessage(conversationId: string, role: StoredMessage["role"], content: string): Promise<StoredMessage> {
  const db = await getDb();
  const msg: StoredMessage = {
    id: makeId("msg"),
    conversationId,
    role,
    content,
    createdAt: Date.now(),
  };
  await db.put("messages", msg);

  const conv = await db.get("conversations", conversationId);
  if (conv) await db.put("conversations", { ...conv, updatedAt: Date.now() });
  return msg;
}

export async function listMessages(conversationId: string, limit = 200): Promise<StoredMessage[]> {
  const db = await getDb();
  const idx = db.transaction("messages").store.index("by-conversation");
  const all = await idx.getAll(conversationId);
  return all.sort((a, b) => a.createdAt - b.createdAt).slice(-limit);
}

export async function addSyncQueueItem(item: SyncQueueItem): Promise<void> {
  const db = await getDb();
  await db.put("syncQueue", item);
}

export async function listSyncQueueItems(limit = 50): Promise<SyncQueueItem[]> {
  const db = await getDb();
  const idx = db.transaction("syncQueue").store.index("by-created");
  const all = await idx.getAll();
  return all.sort((a, b) => a.createdAt - b.createdAt).slice(0, limit);
}

export async function removeSyncQueueItem(id: string): Promise<void> {
  const db = await getDb();
  await db.delete("syncQueue", id);
}

export async function addTelemetryEvent(event: TelemetryEvent): Promise<void> {
  const db = await getDb();
  const id = event.id ?? `${event.type}:${event.ts}:${Math.random().toString(16).slice(2)}`;
  await db.put("telemetry", { ...event, id });
}

export async function listTelemetry(limit = 200): Promise<Array<TelemetryEvent & { id: string }>> {
  const db = await getDb();
  const all = await db.getAll("telemetry");
  return all.sort((a, b) => a.ts - b.ts).slice(-limit);
}
