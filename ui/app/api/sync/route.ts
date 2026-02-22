import { NextResponse } from "next/server";

export const runtime = "nodejs";

type SyncKind = "settings" | "telemetry" | "chat" | string;

type SyncItem = {
  id: string;
  kind: SyncKind;
  payload: unknown;
  createdAt: number;
  updatedAt?: number;
  deviceId?: string;
};

type SyncRequest =
  | SyncItem
  | {
      kind: SyncKind;
      items: SyncItem[];
    };

function normalize(body: unknown): { kind: SyncKind; items: SyncItem[] } {
  if (!body || typeof body !== "object") return { kind: "unknown", items: [] };
  const anyBody = body as Record<string, unknown>;
  if (Array.isArray(anyBody.items)) {
    const kind = typeof anyBody.kind === "string" ? (anyBody.kind as SyncKind) : "unknown";
    return { kind, items: anyBody.items as SyncItem[] };
  }
  return { kind: (anyBody.kind as SyncKind) ?? "unknown", items: [anyBody as SyncItem] };
}

export async function POST(req: Request) {
  // Placeholder multi-device sync endpoint.
  // In a real implementation, this would authenticate and persist to a backend.
  const body = (await req.json().catch(() => null)) as SyncRequest | null;
  const { kind, items } = normalize(body);

  const results = items.map((item) => {
    const idOk = Boolean(item && typeof item.id === "string" && item.id.length);
    return {
      id: idOk ? item.id : null,
      ok: idOk,
      kind: (item?.kind ?? kind) as SyncKind,
      deviceId: item?.deviceId ?? null,
      applied: idOk,
    };
  });

  return NextResponse.json({ ok: true, kind, count: results.length, results });
}
