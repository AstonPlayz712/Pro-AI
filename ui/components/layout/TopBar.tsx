"use client";

import React from "react";
import { useMode } from "../../hooks/useMode";
import { useTone, type Tone } from "../../hooks/useTone";
import { useDAIState } from "../../hooks/useDAIState";
import { getModeTheme, MODE_THEMES, type Mode } from "../../lib/theme";
import { glassStyle } from "../../lib/glassmorphism";

const MODES: Mode[] = ["architect", "debugger", "analyst", "builder"];
const TONES: Tone[] = ["precise", "conversational", "minimalist", "technical"];

/**
 * TopBar
 *
 * Fixed header spanning the full viewport width. Displays the workspace title,
 * the active mode pill (with mode switcher), tone selector, and health
 * indicator from DAI state.
 */
/** Semi-transparent border: 20% opacity as hex suffix */
const BORDER_ALPHA = "33";

export default function TopBar() {
  const { mode, setMode } = useMode();
  const { tone, setTone } = useTone();
  const { state } = useDAIState();
  const modeTheme = getModeTheme(mode);

  const hasHealthIssue =
    state.health.chipConflicts ||
    state.health.expiredChips.length > 0 ||
    state.health.lowConfidence;

  return (
    <header
      style={{
        ...glassStyle({ blur: 16, opacity: 0.85 }),
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: "var(--topbar-height)",
        padding: "0 var(--space-6)",
        borderBottom: "1px solid var(--color-border)",
        position: "sticky",
        top: 0,
        zIndex: "var(--z-topbar)",
        flexShrink: 0,
      }}
    >
      {/* Left: wordmark */}
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
        <span
          style={{
            fontWeight: 700,
            fontSize: "var(--text-md)",
            letterSpacing: "0.04em",
            color: "var(--color-text)",
          }}
        >
          Auto
        </span>
        <span
          style={{
            fontSize: "var(--text-xs)",
            color: "var(--color-text-dim)",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          workspace
        </span>
      </div>

      {/* Centre: mode switcher */}
      <nav
        style={{
          display: "flex",
          gap: "var(--space-1)",
          background: "var(--color-surface-2)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-pill)",
          padding: "3px",
        }}
      >
        {MODES.map((m) => {
          const t = getModeTheme(m);
          const active = m === mode;
          return (
            <button
              key={m}
              onClick={() => setMode(m)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-1)",
                padding: "3px 12px",
                borderRadius: "var(--radius-pill)",
                border: "none",
                cursor: "pointer",
                fontSize: "var(--text-xs)",
                fontWeight: active ? 600 : 400,
                background: active ? t.accent : "transparent",
                color: active ? "#fff" : "var(--color-text-muted)",
                transition: "background var(--transition-base), color var(--transition-base)",
              }}
            >
              <span>{t.icon}</span>
              <span>{t.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Right: tone + health */}
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
        {/* Tone selector */}
        <select
          value={tone}
          onChange={(e) => setTone(e.target.value as Tone)}
          style={{
            background: "var(--color-surface-2)",
            border: "1px solid var(--color-border)",
            color: "var(--color-text-muted)",
            fontSize: "var(--text-xs)",
            padding: "4px 8px",
            borderRadius: "var(--radius-md)",
            cursor: "pointer",
          }}
          aria-label="Select tone"
        >
          {TONES.map((t) => (
            <option key={t} value={t}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </option>
          ))}
        </select>

        {/* Health indicator */}
        <div
          title={hasHealthIssue ? "DAI health issues detected" : "DAI healthy"}
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: hasHealthIssue
              ? "var(--color-danger)"
              : "var(--color-success)",
            boxShadow: hasHealthIssue
              ? "0 0 6px var(--color-danger)"
              : "0 0 6px var(--color-success)",
          }}
        />

        {/* Active mode badge */}
        <span
          style={{
            fontSize: "var(--text-xs)",
            padding: "3px 10px",
            borderRadius: "var(--radius-pill)",
            background: modeTheme.accentDim,
            color: modeTheme.accent,
            border: `1px solid ${modeTheme.accent}${BORDER_ALPHA}`,
            fontWeight: 500,
          }}
        >
          {modeTheme.icon} {modeTheme.label}
        </span>
      </div>
    </header>
  );
}
