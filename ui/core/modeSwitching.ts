import type { ConnectivityQuality } from "./connectivityPolicy";
import type { AiMode } from "./aiModeManager";
import type { ChatMessage, ChatFile } from "./chatTypes";

const LARGE_TASK_CHARS = 4000;

export function estimateTaskSize(messages: ChatMessage[], file?: ChatFile): number {
  const msgChars = messages.reduce((sum, message) => sum + message.content.length, 0);
  const fileChars = file?.content.length ?? 0;
  return msgChars + fileChars;
}

export function isLargeTask(messages: ChatMessage[], file?: ChatFile): boolean {
  return estimateTaskSize(messages, file) >= LARGE_TASK_CHARS;
}

export function resolveAutomaticMode(
  defaultMode: AiMode,
  quality: ConnectivityQuality,
  largeTask: boolean,
): { mode: AiMode; temporary: boolean; reason: string } {
  if (defaultMode === "hybrid") {
    return { mode: "hybrid", temporary: false, reason: "Hybrid mode uses connectivity-aware engine blending." };
  }

  if (defaultMode === "local") {
    if (largeTask && quality === "good") {
      return { mode: "cloud", temporary: true, reason: "Large task temporarily escalated to cloud." };
    }
    return { mode: "local", temporary: false, reason: "Local mode preserved." };
  }

  if (quality === "offline") {
    return { mode: "local", temporary: true, reason: "Cloud mode temporarily switched to local while offline." };
  }

  return { mode: "cloud", temporary: false, reason: "Cloud mode preserved." };
}
