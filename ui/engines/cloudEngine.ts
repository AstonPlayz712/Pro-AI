import type { ChatEngine } from "../core/chatEngine";
import type { ChatMessage } from "../core/chatTypes";

type OpenAIChatCompletionChunk = {
  choices?: Array<{
    delta?: { content?: string };
    finish_reason?: string | null;
  }>;
};

function toOpenAIMessages(messages: ChatMessage[]) {
  return messages.map((m) => ({ role: m.role, content: m.content }));
}

async function* streamOpenAICompatibleSSE(resp: Response): AsyncIterable<string> {
  if (!resp.body) return;
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames separated by \n\n
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const frame of parts) {
      const lines = frame.split("\n");
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data:")) continue;
        const data = trimmed.slice("data:".length).trim();
        if (!data) continue;
        if (data === "[DONE]") return;

        let parsed: OpenAIChatCompletionChunk | null = null;
        try {
          parsed = JSON.parse(data) as OpenAIChatCompletionChunk;
        } catch {
          parsed = null;
        }
        const delta = parsed?.choices?.[0]?.delta?.content;
        if (delta) yield delta;
      }
    }
  }
}

export class CloudEngine implements ChatEngine {
  public readonly id = "cloud" as const;

  constructor(private readonly options?: { model?: string }) {}

  async generate(messages: ChatMessage[]): Promise<AsyncIterable<string>> {
    const baseUrl = process.env.CLOUD_BASE_URL ?? process.env.OPENAI_BASE_URL ?? "https://api.openai.com";
    const apiKey = process.env.CLOUD_API_KEY ?? process.env.OPENAI_API_KEY;
    const model =
      this.options?.model ?? process.env.CLOUD_MODEL ?? process.env.OPENAI_MODEL ?? "gpt-4o-mini";

    if (!apiKey) throw new Error("Missing CLOUD_API_KEY (or OPENAI_API_KEY) for cloud engine.");

    const url = `${baseUrl.replace(/\/$/, "")}/v1/chat/completions`;
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model,
        stream: true,
        messages: toOpenAIMessages(messages),
      }),
    });

    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      throw new Error(`Cloud engine error (${resp.status}): ${text}`);
    }

    return streamOpenAICompatibleSSE(resp);
  }
}
