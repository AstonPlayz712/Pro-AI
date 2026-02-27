"use client";

import React, { useRef, useState } from "react";

import type { ChatFile } from "../core/chatTypes";

type MessageInputProps = {
  busy: boolean;
  onSend: (text: string, file?: ChatFile) => Promise<void>;
};

export function MessageInput({ busy, onSend }: MessageInputProps): React.JSX.Element {
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [input, setInput] = useState("");
  const [file, setFile] = useState<ChatFile | undefined>(undefined);
  const [uploading, setUploading] = useState(false);

  const canSend = !busy && !uploading && (input.trim().length > 0 || Boolean(file));

  const upload = async (selected: File) => {
    setUploading(true);
    try {
      const form = new FormData();
      form.set("file", selected);
      const resp = await fetch("/api/read-file", { method: "POST", body: form });
      const json = (await resp.json()) as { ok?: boolean; error?: string; file?: ChatFile };
      if (!resp.ok || !json.ok || !json.file) {
        throw new Error(json.error ?? "Failed to read file.");
      }
      setFile(json.file);
    } finally {
      setUploading(false);
    }
  };

  const send = async () => {
    if (!canSend) return;
    const text = input.trim();
    setInput("");
    const selectedFile = file;
    setFile(undefined);
    await onSend(text, selectedFile);
  };

  return (
    <div className="vsc-message-input">
      <input
        ref={fileRef}
        type="file"
        style={{ display: "none" }}
        onChange={(e) => {
          const selected = e.target.files?.[0];
          if (selected) {
            void upload(selected);
          }
          e.currentTarget.value = "";
        }}
      />

      {file && (
        <div className="vsc-badge" style={{ justifyContent: "space-between" }}>
          <span>{file.name}</span>
          <button type="button" className="vsc-command__btn" onClick={() => setFile(undefined)}>
            Remove
          </button>
        </div>
      )}

      <div className="vsc-chat__composer">
        <input
          className="vsc-chat__input"
          value={input}
          disabled={busy || uploading}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
        />
        <div className="vsc-command__actions">
          <button
            type="button"
            className="vsc-command__btn"
            disabled={busy || uploading}
            onClick={() => fileRef.current?.click()}
          >
            {uploading ? "Reading file…" : "Attach file"}
          </button>
          <button className="vsc-chat__send" type="button" disabled={!canSend} onClick={() => void send()}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
