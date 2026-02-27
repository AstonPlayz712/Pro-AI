import type { ChatEngine } from "../core/chatEngine";
import type { ChatMessage } from "../core/chatTypes";
import { withOptionalFile } from "../core/filePrompt";

type OllamaChatChunk = {
  message?: { role?: string; content?: string };
  done?: boolean;
};

function toOllamaMessages(messages: ChatMessage[]) {
  return messages.map((m) => ({ role: m.role, content: m.content }));
}

async function* streamNDJSON(resp: Response): AsyncIterable<string> {
  if (!resp.body) return;
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let idx: number;
    while ((idx = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 1);
      if (!line) continue;

      let parsed: OllamaChatChunk | null = null;
      try {
        parsed = JSON.parse(line) as OllamaChatChunk;
      } catch {
        parsed = null;
      }

      const token = parsed?.message?.content;
      if (token) yield token;
      if (parsed?.done) return;
    }
  }
}

export class LocalEngine implements ChatEngine {
  public readonly id = "local" as const;

  constructor(private readonly options?: { model?: string }) {}

  async generate(messages: ChatMessage[], options?: { file?: { name: string; type: string; content: string } }): Promise<AsyncIterable<string>> {
    const url = "http://localhost:11434/api/chat";
    const model = this.options?.model ?? process.env.LOCAL_MODEL ?? "phi3";
    const scopedMessages = withOptionalFile(messages, options?.file);

    const resp = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        model,
        stream: true,
        messages: toOllamaMessages(scopedMessages),
      }),
    });

    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      throw new Error(`Local engine error (${resp.status}): ${text}`);
    }

    return streamNDJSON(resp);
  }
}
