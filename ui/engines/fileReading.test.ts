import { describe, expect, test, vi, beforeEach, afterEach } from "vitest";

import type { ChatEngine } from "../core/chatEngine";
import type { ConnectivityState } from "../core/connectivity";
import { CloudEngine } from "./cloudEngine";
import { HybridEngine } from "./hybridEngine";
import { LocalEngine } from "./localEngine";

const goodConnectivity: ConnectivityState = {
  online: true,
  realInternet: true,
  type: "wifi",
  effectiveType: "4g",
  downlink: 50,
  rtt: 40,
  isWifi: true,
  isCellular: false,
  isSlow: false,
  cloudHealthy: true,
};

async function collect(iterable: AsyncIterable<string>): Promise<string> {
  let text = "";
  for await (const c of iterable) text += c;
  return text;
}

class StubEngine implements ChatEngine {
  constructor(
    public id: "cloud" | "local" | "hybrid",
    private readonly text: string,
    private readonly delay = 0,
    private readonly shouldFail = false,
  ) {}

  async generate(
    messages?: Array<{ role: "user" | "assistant" | "system"; content: string }>,
    options?: { file?: { name: string; type: string; content: string }; connectivity?: ConnectivityState },
  ): Promise<AsyncIterable<string>> {
    void messages;
    void options;
    if (this.shouldFail) throw new Error("stub-failure");
    const text = this.text;
    const delay = this.delay;
    return {
      [Symbol.asyncIterator]: async function* () {
        if (delay > 0) await new Promise((r) => setTimeout(r, delay));
        yield text;
      },
    };
  }
}

describe("file reading tests", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("file reading tests (local)", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response('{"message":{"content":"local-response"},"done":true}\n', {
        status: 200,
        headers: { "content-type": "application/x-ndjson" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const engine = new LocalEngine({ model: "phi3" });
    const iterable = await engine.generate(
      [{ role: "user", content: "Summarize." }],
      { file: { name: "a.txt", type: "text/plain", content: "File context" } },
    );

    const out = await collect(iterable);
    expect(out).toContain("local-response");

    const body = JSON.parse(String(fetchMock.mock.calls[0][1]?.body)) as { messages: Array<{ content: string }> };
    expect(body.messages.some((m) => m.content.includes("File context"))).toBe(true);
  });

  test("file reading tests (cloud)", async () => {
    process.env.CLOUD_API_KEY = "test-key";
    const fetchMock = vi.fn().mockResolvedValue(
      new Response('data: {"choices":[{"delta":{"content":"cloud-response"}}]}\n\ndata: [DONE]\n\n', {
        status: 200,
        headers: { "content-type": "text/event-stream" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const engine = new CloudEngine({ model: "gpt-4o-mini" });
    const iterable = await engine.generate(
      [{ role: "user", content: "Analyze" }],
      { file: { name: "b.txt", type: "text/plain", content: "Cloud file context" }, connectivity: goodConnectivity },
    );

    const out = await collect(iterable);
    expect(out).toContain("cloud-response");

    const body = JSON.parse(String(fetchMock.mock.calls[0][1]?.body)) as { messages: Array<{ content: string }> };
    expect(body.messages.some((m) => m.content.includes("Cloud file context"))).toBe(true);
  });

  test("file reading tests (hybrid)", async () => {
    const engine = new HybridEngine({
      localFactory: () => new StubEngine("local", "local-answer", 5),
      cloudFactory: () => new StubEngine("cloud", "cloud-answer", 10),
    });

    const iterable = await engine.generate([{ role: "user", content: "use file" }], {
      file: { name: "c.txt", type: "text/plain", content: "Hybrid context" },
      connectivity: goodConnectivity,
    });

    const out = await collect(iterable);
    expect(out).toContain("Refined by cloud:");
    expect(out).toContain("local-answer");
    expect(out).toContain("cloud-answer");
  });

  test("hybrid falls back to local when cloud is unavailable", async () => {
    const engine = new HybridEngine({
      localFactory: () => new StubEngine("local", "local-only", 0),
      cloudFactory: () => new StubEngine("cloud", "cloud-missing", 0, true),
    });

    const iterable = await engine.generate([{ role: "user", content: "fallback" }], {
      connectivity: { ...goodConnectivity, cloudHealthy: false },
    });

    const out = await collect(iterable);
    expect(out).toContain("local-only");
  });
});
