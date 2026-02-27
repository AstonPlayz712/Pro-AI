export type ChatRole = "user" | "assistant" | "system";

export type ChatMessage = {
  role: ChatRole;
  content: string;
  id?: string;
  createdAt?: string;
};

export type ChatFile = {
  name: string;
  type: string;
  content: string;
};
