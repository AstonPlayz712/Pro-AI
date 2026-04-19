"use client";

import React, { useRef, useState } from "react";
import { useMode } from "../../hooks/useMode";
import { useBlocks, type BlockType } from "../../hooks/useBlocks";
import { getModeTheme } from "../../lib/theme";
import { glassStyle } from "../../lib/glassmorphism";

/** Command prefixes that map to block types */
const BLOCK_PREFIXES: Record<string, BlockType> = {
  "/plan":     "plan",
  "/code":     "code",
  "/analyse":  "analysis",
  "/analyze":  "analysis",
  "/diagram":  "diagram",
  "/result":   "result",
  "/note":     "note",
};

/** Built-in slash commands shown in the hint list */
const COMMAND_HINTS = [
  { cmd: "/plan",    desc: "Create a plan block" },
  { cmd: "/code",    desc: "Create a code block" },
  { cmd: "/analyse", desc: "Create an analysis block" },
  { cmd: "/diagram", desc: "Create a diagram block" },
  { cmd: "/result",  desc: "Create a result block" },
  { cmd: "/note",    desc: "Create a note block" },
];

/**
 * AutoCommandSurface (ACS)
 *
 * Bottom-anchored command bar. Accepts natural language prompts and slash
 * commands. Slash commands immediately create a new block; plain text
 * messages are forwarded to the backend chat endpoint (stub).
 */
export default function AutoCommandSurface() {
  const { mode } = useMode();
  const { addBlock } = useBlocks();
  const modeTheme = getModeTheme(mode);
  const [value, setValue] = useState("");
  const [showHints, setShowHints] = useState(false);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredHints = value.startsWith("/")
    ? COMMAND_HINTS.filter((h) => h.cmd.startsWith(value.split(" ")[0]))
    : [];

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") {
      setShowHints(false);
      return;
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(value.trim());
    }
  }

  function submit(raw: string) {
    if (!raw) return;
    const parts = raw.split(" ");
    const prefix = parts[0].toLowerCase();
    const rest = parts.slice(1).join(" ");

    const blockType = BLOCK_PREFIXES[prefix];
    if (blockType) {
      addBlock(blockType, rest || undefined, "");
      setValue("");
      setShowHints(false);
      return;
    }

    // Plain-text prompt → stub for backend call
    setLoading(true);
    addBlock("result", raw, "");
    // TODO: call POST /api/chat with the prompt and stream the response
    // into the new result block's content via updateBlock.
    setTimeout(() => {
      setLoading(false);
    }, 500);
    setValue("");
    setShowHints(false);
  }

  return (
    <div
      style={{
        position: "relative",
        flexShrink: 0,
      }}
    >
      {/* Slash-command hints */}
      {showHints && filteredHints.length > 0 && (
        <div
          style={{
            ...glassStyle({ blur: 16, opacity: 0.95 }),
            position: "absolute",
            bottom: "calc(100% + 6px)",
            left: "var(--space-4)",
            right: "var(--space-4)",
            borderRadius: "var(--radius-lg)",
            overflow: "hidden",
            zIndex: "var(--z-overlay)",
          }}
        >
          {filteredHints.map(({ cmd, desc }) => (
            <button
              key={cmd}
              onMouseDown={(e) => {
                e.preventDefault();
                setValue(cmd + " ");
                inputRef.current?.focus();
              }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-4)",
                width: "100%",
                padding: "var(--space-3) var(--space-4)",
                background: "transparent",
                border: "none",
                borderBottom: "1px solid var(--color-border-muted)",
                color: "var(--color-text-muted)",
                fontSize: "var(--text-sm)",
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  color: modeTheme.accent,
                  fontWeight: 600,
                  minWidth: 90,
                }}
              >
                {cmd}
              </span>
              <span>{desc}</span>
            </button>
          ))}
        </div>
      )}

      {/* Input bar */}
      <div
        style={{
          ...glassStyle({ blur: 14, opacity: 0.9 }),
          display: "flex",
          alignItems: "center",
          gap: "var(--space-3)",
          padding: "var(--space-3) var(--space-4)",
          borderTop: "1px solid var(--color-border)",
          height: "var(--acs-height)",
        }}
      >
        {/* Mode icon */}
        <span
          style={{
            fontSize: "var(--text-md)",
            color: modeTheme.accent,
            flexShrink: 0,
            lineHeight: 1,
          }}
        >
          {modeTheme.icon}
        </span>

        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setShowHints(e.target.value.startsWith("/"));
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => { if (value.startsWith("/")) setShowHints(true); }}
          onBlur={() => setTimeout(() => setShowHints(false), 150)}
          placeholder={`Ask ${modeTheme.label} anything, or type / for commands…`}
          disabled={loading}
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "var(--color-text)",
            fontSize: "var(--text-sm)",
            fontFamily: "var(--font-sans)",
          }}
          aria-label="Command input"
        />

        {/* Send button */}
        <button
          onClick={() => submit(value.trim())}
          disabled={loading || !value.trim()}
          style={{
            background: value.trim() ? modeTheme.accent : "var(--color-surface-3)",
            border: "none",
            borderRadius: "var(--radius-md)",
            color: value.trim() ? "#fff" : "var(--color-text-dim)",
            cursor: value.trim() && !loading ? "pointer" : "not-allowed",
            padding: "5px 14px",
            fontSize: "var(--text-xs)",
            fontWeight: 600,
            transition: "background var(--transition-base), color var(--transition-base)",
            flexShrink: 0,
          }}
          aria-label="Send"
        >
          {loading ? "…" : "↵"}
        </button>
      </div>
    </div>
  );
}
