import type { ChatEngine } from "../core/chatEngine";
import type { ChatFile, ChatMessage } from "../core/chatTypes";
import type { AiMode } from "../core/aiModeManager";
import { getConnectivityState } from "../core/connectivity";

async function* streamPlainText(resp: Response): AsyncIterable<string> {
  if (!resp.body) return;
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    yield decoder.decode(value, { stream: true });
  }
}

export type BackendEngineOptions = {
  mode: AiMode;
  cloudModel?: string;
  localModel?: string;
  projectId?: string;
};

export class BackendChatEngine implements ChatEngine {
  public id: "cloud" | "local" | "hybrid" = "local";

  constructor(private readonly options: BackendEngineOptions) {}

  async generate(messages: ChatMessage[], options?: { file?: ChatFile }): Promise<AsyncIterable<string>> {
    const connectivity = await getConnectivityState();
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        messages,
        mode: this.options.mode,
        cloudModel: this.options.cloudModel,
        localModel: this.options.localModel,
        projectId: this.options.projectId,
        file: options?.file,
        connectivity,
      }),
    });

    const engineId = resp.headers.get("x-engine-id");
    if (engineId === "cloud" || engineId === "local" || engineId === "hybrid") {
      this.id = engineId;
    }

    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      throw new Error(`Backend chat route error (${resp.status}): ${text}`);
    }

    return streamPlainText(resp);
  }
}
