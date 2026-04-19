"use client";

import React from "react";
import type { DAIChipRef } from "../../hooks/useDAIState";
import { useDAIState } from "../../hooks/useDAIState";
import { useMode } from "../../hooks/useMode";
import { getModeTheme } from "../../lib/theme";

interface DAIChipProps {
  chip: DAIChipRef;
}

/**
 * DAIChip
 *
 * Renders a single chip from the DAI chip registry. Chips are reference-only:
 * no payload is displayed. Shows chip ID, source, confidence, TTL, and pin
 * state. Pinned chips use the mode accent; expired chips are styled as danger.
 */
/** Semi-transparent border: 20% opacity as hex suffix */
const BORDER_ALPHA = "33";

export default function DAIChip({ chip }: DAIChipProps) {
  const { state, removeChip } = useDAIState();
  const { mode } = useMode();
  const modeTheme = getModeTheme(mode);

  const expired = state.health.expiredChips.includes(chip.chipId);

  const accentColor = expired
    ? "var(--color-danger)"
    : chip.pinned
    ? modeTheme.accent
    : "var(--color-text-muted)";

  const bgColor = expired
    ? "rgba(232,90,79,0.1)"
    : chip.pinned
    ? modeTheme.accentDim
    : "var(--color-surface-3)";

  return (
    <div
      title={`Source: ${chip.source} | TTL: ${chip.ttl}s | Confidence: ${Math.round(chip.confidence * 100)}%${expired ? " | EXPIRED" : ""}${chip.pinned ? " | PINNED" : ""}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "2px 8px",
        borderRadius: "var(--radius-pill)",
        fontSize: "var(--text-xs)",
        fontWeight: 500,
        background: bgColor,
        color: accentColor,
        border: `1px solid ${accentColor}${BORDER_ALPHA}`,
        userSelect: "none",
        maxWidth: 160,
      }}
    >
      {/* Pin indicator */}
      {chip.pinned && <span style={{ fontSize: 9 }}>◈</span>}

      {/* Chip ID (truncated) */}
      <span
        style={{
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          maxWidth: 90,
        }}
      >
        {chip.chipId}
      </span>

      {/* Confidence */}
      <span style={{ opacity: 0.75 }}>{Math.round(chip.confidence * 100)}%</span>

      {/* Remove */}
      <button
        onClick={() => removeChip(chip.chipId)}
        style={{
          background: "transparent",
          border: "none",
          cursor: "pointer",
          color: "inherit",
          padding: 0,
          lineHeight: 1,
          fontSize: 9,
          opacity: 0.6,
        }}
        aria-label={`Remove chip ${chip.chipId}`}
      >
        ✕
      </button>
    </div>
  );
}
