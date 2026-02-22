"use client";

import React, { useEffect, useRef, useState } from "react";

import type { ChatMessage } from "../core/chatTypes";
import { BackendChatEngine } from "../engines/backendEngine";
import {
  addMessage,
  createConversation,
  ensureDefaultSettings,
  listMessages,
  type StoredMessage,
} from "../storage/db";
import { useConnectivity } from "../hooks/useConnectivity";

function toChatMessages(messages: StoredMessage[]): ChatMessage[] {
  return messages.map((m) => ({ role: m.role, content: m.content, id: m.id, createdAt: new Date(m.createdAt).toISOString() }));
}

export function ChatPanel(): React.JSX.Element {
  const { state: conn } = useConnectivity();
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<StoredMessage[]>([]);
  const [input, setInput] = useState("");
  const [engineId, setEngineId] = useState<"cloud" | "local" | "-">("-");
  const [busy, setBusy] = useState(false);
  const [warmingUp, setWarmingUp] = useState(false);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, busy]);

  useEffect(() => {
    void (async () => {
      const conv = await createConversation("New chat");
      setConversationId(conv.id);
      setMessages(await listMessages(conv.id));
    })();
  }, []);

  const canUseCloud = Boolean(conn?.realInternet && !conn?.isSlow && conn?.cloudHealthy);

  const send = async () => {
    if (!conversationId) return;
    const text = input.trim();
    if (!text) return;

    setInput("");
    setBusy(true);

    await addMessage(conversationId, "user", text);
    const existing = await listMessages(conversationId);
    setMessages(existing);

    const settings = await ensureDefaultSettings();

    // If user chose auto, we still pass auto; the BackendChatEngine will attach connectivity snapshot.
    const engine = new BackendChatEngine({
      mode: settings.engineMode,
      cloudModel: settings.cloudModel,
      localModel: settings.localModel,
    });

    // Local warming indicator (placeholder UX).
    setWarmingUp(!canUseCloud);

    let assistantBuffer = "";
    const assistantTempId = `temp:${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: assistantTempId,
        conversationId,
        role: "assistant",
        content: "",
        createdAt: Date.now(),
      },
    ]);

    try {
      const iterable = await engine.generate(toChatMessages(existing));
      setEngineId(engine.id);

      for await (const chunk of iterable) {
        assistantBuffer += chunk;
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantTempId ? { ...m, content: assistantBuffer } : m))
        );
      }

      // Persist final assistant message.
      await addMessage(conversationId, "assistant", assistantBuffer.trim());
      setMessages(await listMessages(conversationId));
    } finally {
      setBusy(false);
      setWarmingUp(false);
    }
  };

  return (
    <div className="vsc-chat">
      <div className="vsc-chat__top">
        <div className="vsc-chat__engine">
          <span className="vsc-muted">Engine:</span> <span className={`vsc-engine-badge ${engineId}`}>{engineId}</span>
          {warmingUp && <span className="vsc-badge">Local engine warming up</span>}
          {!canUseCloud && <span className="vsc-badge">Cloud temporarily disabled</span>}
        </div>
      </div>

      <div className="vsc-chat__log">
        {messages.map((m) => (
          <div key={m.id} className={`vsc-chat__msg ${m.role}`}>
            <div className="vsc-chat__role">{m.role}</div>
            <div className="vsc-chat__content">{m.content}</div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form
        className="vsc-chat__composer"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <input
          className="vsc-chat__input"
          value={input}
          disabled={busy}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
        />
        <button className="vsc-chat__send" type="submit" disabled={busy}>
          Send
        </button>
      </form>
    </div>
  );
}
