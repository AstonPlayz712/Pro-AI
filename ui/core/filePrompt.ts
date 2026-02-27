import type { ChatFile, ChatMessage } from "./chatTypes";

export function withOptionalFile(messages: ChatMessage[], file?: ChatFile): ChatMessage[] {
  if (!file) return messages;
  const fileContext: ChatMessage = {
    role: "system",
    content: [
      `User attached file: ${file.name} (${file.type}).`,
      "Use the extracted file text below as additional context:",
      file.content,
    ].join("\n\n"),
  };
  return [...messages, fileContext];
}
