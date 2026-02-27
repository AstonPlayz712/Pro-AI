"use client";

import React, { useEffect, useRef, useState } from "react";

import type { AiMode } from "../core/aiModeManager";
import type { ChatFile, ChatMessage } from "../core/chatTypes";
import { classifyConnectivity } from "../core/connectivityPolicy";
import { isLargeTask, resolveAutomaticMode } from "../core/modeSwitching";
import { BackendChatEngine } from "../engines/backendEngine";
import {
  addMessage,
  createConversation,
  ensureDefaultSettings,
  listMessages,
  type StoredMessage,
} from "../storage/db";
import { useConnectivity } from "../hooks/useConnectivity";
import { recordTelemetryEvent } from "../telemetry/telemetry";
import { useProjectManager } from "../hooks/useProjectManager";
import { MessageInput } from "./MessageInput";
import { useAiModeManager } from "../hooks/useAiModeManager";

function toChatMessages(messages: StoredMessage[]): ChatMessage[] {
  return messages.map((m) => ({ role: m.role, content: m.content, id: m.id, createdAt: new Date(m.createdAt).toISOString() }));
}

export function ChatPanel(): React.JSX.Element {
  const { state: conn } = useConnectivity();
  const { project } = useProjectManager();
  const { defaultMode, currentMode, setDefaultMode, temporarilyUse, resetToDefault } = useAiModeManager();
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<StoredMessage[]>([]);
  const [engineId, setEngineId] = useState<"cloud" | "local" | "hybrid" | "-">("-");
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

  const quality = classifyConnectivity(conn);
  const canUseCloud = quality === "good";

  const send = async (text: string, file?: ChatFile) => {
    if (!conversationId) return;
    const normalizedText = text.trim() || (file ? "Please analyze the attached file." : "");
    if (!normalizedText) return;

    setBusy(true);

    const userDisplay = file ? `${normalizedText}\n\n[Attached file: ${file.name}]` : normalizedText;
    await addMessage(conversationId, "user", userDisplay);
    const existing = await listMessages(conversationId);
    setMessages(existing);

    const settings = await ensureDefaultSettings();
    const largeTask = isLargeTask(toChatMessages(existing), file);
    const decision = resolveAutomaticMode(defaultMode, quality, largeTask);
    if (decision.temporary) {
      temporarilyUse(decision.mode);
    }

    const engine = new BackendChatEngine({
      mode: decision.mode,
      cloudModel: settings.cloudModel,
      localModel: settings.localModel,
      projectId: project.id,
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
      const iterable = await engine.generate(toChatMessages(existing), { file });
      setEngineId(engine.id);
      recordTelemetryEvent({
        type: "engine_selected",
        ts: Date.now(),
        data: {
          engineId: engine.id,
          mode: decision.mode,
          defaultMode,
          temporary: decision.temporary,
          projectId: project.id,
          quality,
        },
      });

      // Batch UI updates to ~20fps.
      let lastFlush = 0;
      const flushEveryMs = 50;
      const flush = () => {
        setMessages((prev) => prev.map((m) => (m.id === assistantTempId ? { ...m, content: assistantBuffer } : m)));
      };

      for await (const chunk of iterable) {
        assistantBuffer += chunk;
        const now = performance.now();
        if (now - lastFlush >= flushEveryMs) {
          lastFlush = now;
          flush();
        }
      }

      flush();

      // Persist final assistant message.
      await addMessage(conversationId, "assistant", assistantBuffer.trim());
      setMessages(await listMessages(conversationId));
    } finally {
      setBusy(false);
      setWarmingUp(false);
      resetToDefault();
    }
  };

  return (
    <div className="vsc-chat">
      <div className="vsc-chat__top">
        <div className="vsc-chat__engine">
          <span className="vsc-muted">Default mode:</span>
          <select className="vsc-select" value={defaultMode} onChange={(e) => setDefaultMode(e.target.value as AiMode)}>
            <option value="local">Local</option>
            <option value="cloud">Cloud</option>
            <option value="hybrid">Hybrid</option>
          </select>
          <span className="vsc-muted">Current mode:</span> <span className="vsc-badge">{currentMode}</span>
          <span className="vsc-muted">Project:</span> <span className="vsc-badge">{project.name}</span>
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

      <MessageInput busy={busy} onSend={send} />
    </div>
  );
}
