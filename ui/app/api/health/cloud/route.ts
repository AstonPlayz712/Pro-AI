import { NextResponse } from "next/server";

import { CloudEngine } from "../../../../engines/cloudEngine";

export const runtime = "nodejs";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const timeoutMs = Number(searchParams.get("timeout") ?? "1500");

  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);

  try {
    // Minimal request: try to open a stream and read a small chunk.
    const engine = new CloudEngine();
    const iterable = await engine.generate([{ role: "system", content: "ping" }]);

    const iterator = iterable[Symbol.asyncIterator]();
    const first = await Promise.race([
      iterator.next(),
      new Promise<IteratorResult<string>>((_, rej) => setTimeout(() => rej(new Error("timeout")), timeoutMs)),
    ]);

    void first;
    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ ok: false });
  } finally {
    clearTimeout(t);
    controller.abort();
  }
}
