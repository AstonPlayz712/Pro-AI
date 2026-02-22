import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(req: Request) {
  // Placeholder multi-device sync endpoint.
  // In a real implementation, this would authenticate and persist to a backend.
  const body = await req.json().catch(() => null);
  return NextResponse.json({ ok: true, received: Boolean(body) });
}
