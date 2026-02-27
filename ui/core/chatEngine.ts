import type { ChatFile, ChatMessage } from "./chatTypes";
import type { ConnectivityState } from "./connectivity";

export interface ChatEngine {
  id: "cloud" | "local" | "hybrid";
  generate(messages: ChatMessage[], options?: { file?: ChatFile; connectivity?: ConnectivityState }): Promise<AsyncIterable<string>>;
}
