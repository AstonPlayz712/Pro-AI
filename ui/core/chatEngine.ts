import type { ChatMessage } from "./chatTypes";

export interface ChatEngine {
  id: "cloud" | "local";
  generate(messages: ChatMessage[]): Promise<AsyncIterable<string>>;
}
