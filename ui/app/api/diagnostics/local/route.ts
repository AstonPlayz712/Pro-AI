import { NextResponse } from "next/server";

import { LocalEngine } from "../../../../engines/localEngine";

export const runtime = "nodejs";

export async function GET() {
  const engine = new LocalEngine();
  const start = performance.now();

  try {
    const iterable = await engine.generate([{ role: "system", content: "Say 'ok' in 1-3 words." }]);
    let chars = 0;
    let chunks = 0;
    for await (const c of iterable) {
      chars += c.length;
      chunks += 1;
      if (chars > 64) break;
    }

    const elapsedMs = performance.now() - start;
    const cps = elapsedMs > 0 ? (chars / (elapsedMs / 1000)) : 0;

    return NextResponse.json({ ok: true, elapsedMs, chunks, chars, cps });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: message });
  }
}
