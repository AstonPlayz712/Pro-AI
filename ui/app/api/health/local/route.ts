import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function GET() {
  try {
    const resp = await fetch("http://localhost:11434/api/tags", { method: "GET" });
    return NextResponse.json({ ok: resp.ok });
  } catch {
    return NextResponse.json({ ok: false });
  }
}
