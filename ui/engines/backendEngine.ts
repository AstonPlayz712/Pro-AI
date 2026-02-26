import type { ChatEngine } from "../core/chatEngine";
import type { ChatMessage } from "../core/chatTypes";
import type { EngineMode } from "../core/engineSelector";
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
  mode: EngineMode;
  cloudModel?: string;
  localModel?: string;
  projectId?: string;
};

export class BackendChatEngine implements ChatEngine {
  public id: "cloud" | "local" = "local";

  constructor(private readonly options: BackendEngineOptions) {}

  async generate(messages: ChatMessage[]): Promise<AsyncIterable<string>> {
    const connectivity = this.options.mode === "auto" ? await getConnectivityState() : undefined;
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        messages,
        mode: this.options.mode,
        cloudModel: this.options.cloudModel,
        localModel: this.options.localModel,
        projectId: this.options.projectId,
        connectivity,
      }),
    });

    const engineId = resp.headers.get("x-engine-id");
    if (engineId === "cloud" || engineId === "local") {
      this.id = engineId;
    }

    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      throw new Error(`Backend chat route error (${resp.status}): ${text}`);
    }

    return streamPlainText(resp);
  }
}
