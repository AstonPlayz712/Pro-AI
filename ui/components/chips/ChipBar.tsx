"use client";

import React from "react";
import { useDAIState } from "../../hooks/useDAIState";
import InlineChip from "./InlineChip";

/**
 * ChipBar — horizontal scrolling row of all active DAI chips from the
 * DAI state context. Each chip can be pinned (mode-accent) or unpinned
 * (default). Expired chips display in danger style.
 */
export default function ChipBar() {
  const { state, removeChip } = useDAIState();
  const { chips, health } = state;

  if (chips.length === 0) return null;

  const expiredSet = new Set(health.expiredChips);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-2)",
        padding: "var(--space-2) var(--space-4)",
        overflowX: "auto",
        borderBottom: "1px solid var(--color-border-muted)",
        background: "var(--color-surface-1)",
        flexShrink: 0,
      }}
    >
      <span
        style={{
          fontSize: "var(--text-xs)",
          color: "var(--color-text-dim)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          flexShrink: 0,
        }}
      >
        Chips
      </span>

      {chips.map((chip) => {
        const expired = expiredSet.has(chip.chipId);
        return (
          <InlineChip
            key={chip.chipId}
            label={chip.chipId}
            variant={
              expired
                ? "danger"
                : chip.pinned
                ? "mode"
                : undefined
            }
            confidence={chip.confidence}
            onRemove={() => removeChip(chip.chipId)}
            title={`Source: ${chip.source} | TTL: ${chip.ttl}s${expired ? " | EXPIRED" : ""}`}
          />
        );
      })}
    </div>
  );
}
