import type { ChatEngine } from "../core/chatEngine";
import type { ConnectivityState } from "../core/connectivity";
import type { ChatFile, ChatMessage } from "../core/chatTypes";
import { classifyConnectivity } from "../core/connectivityPolicy";
import { CloudEngine } from "./cloudEngine";
import { LocalEngine } from "./localEngine";

type HybridOptions = {
  cloudModel?: string;
  localModel?: string;
  localFactory?: () => ChatEngine;
  cloudFactory?: () => ChatEngine;
};

async function collect(iterable: AsyncIterable<string>): Promise<string> {
  let text = "";
  for await (const chunk of iterable) text += chunk;
  return text;
}

async function* streamText(text: string): AsyncIterable<string> {
  const chunkSize = 200;
  for (let i = 0; i < text.length; i += chunkSize) {
    yield text.slice(i, i + chunkSize);
  }
}

async function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T | undefined> {
  return new Promise<T | undefined>((resolve) => {
    const timer = setTimeout(() => resolve(undefined), timeoutMs);
    void promise
      .then((v) => resolve(v))
      .catch(() => resolve(undefined))
      .finally(() => clearTimeout(timer));
  });
}

export class HybridEngine implements ChatEngine {
  public readonly id = "hybrid" as const;

  constructor(private readonly options?: HybridOptions) {}

  async generate(
    messages: ChatMessage[],
    params?: { file?: ChatFile; connectivity?: ConnectivityState },
  ): Promise<AsyncIterable<string>> {
    const local = this.options?.localFactory?.() ?? new LocalEngine({ model: this.options?.localModel });
    const cloud = this.options?.cloudFactory?.() ?? new CloudEngine({ model: this.options?.cloudModel });
    const quality = classifyConnectivity(params?.connectivity);

    const localPromise = collect(await local.generate(messages, { file: params?.file }));

    if (quality !== "good") {
      const localText = await localPromise;
      return streamText(localText);
    }

    const cloudPromise = collect(await cloud.generate(messages, { file: params?.file, connectivity: params?.connectivity }));

    const first = await Promise.race([
      localPromise.then((text) => ({ winner: "local" as const, text })),
      cloudPromise.then((text) => ({ winner: "cloud" as const, text })),
    ]);

    if (first.winner === "cloud") {
      return streamText(first.text);
    }

    const cloudText = await withTimeout(cloudPromise, 2200);
    if (!cloudText) {
      return streamText(first.text);
    }

    const refined = [
      first.text,
      "",
      "Refined by cloud:",
      cloudText,
    ].join("\n");

    return streamText(refined);
  }
}
