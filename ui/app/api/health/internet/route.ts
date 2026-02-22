import { NextResponse } from "next/server";

export const runtime = "nodejs";

async function headWithTimeout(url: string, timeoutMs: number): Promise<boolean> {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const resp = await fetch(url, { method: "HEAD", signal: controller.signal });
    return resp.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(t);
  }
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const timeout = Number(searchParams.get("timeout") ?? "1500");

  // Use a small, fast endpoint.
  const ok = await headWithTimeout("https://www.google.com/generate_204", timeout);
  return NextResponse.json({ ok });
}
