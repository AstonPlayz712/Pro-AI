"use client";

import React from "react";
import { useMode } from "../../hooks/useMode";
import { getModeTheme } from "../../lib/theme";

export type ChipVariant = "default" | "success" | "warn" | "danger" | "info" | "mode";

interface InlineChipProps {
  label: string;
  variant?: ChipVariant;
  /** Confidence value 0–1 — automatically selects warn/danger variants */
  confidence?: number;
  onRemove?: () => void;
  onClick?: () => void;
  title?: string;
}

const VARIANT_STYLES: Record<
  ChipVariant,
  { bg: string; color: string; border: string }
> = {
  default: {
    bg:     "var(--color-surface-3)",
    color:  "var(--color-text-muted)",
    border: "var(--color-border)",
  },
  success: {
    bg:     "rgba(62,207,142,0.12)",
    color:  "var(--color-success)",
    border: "rgba(62,207,142,0.25)",
  },
  warn: {
    bg:     "rgba(224,162,58,0.12)",
    color:  "var(--color-warn)",
    border: "rgba(224,162,58,0.25)",
  },
  danger: {
    bg:     "rgba(232,90,79,0.12)",
    color:  "var(--color-danger)",
    border: "rgba(232,90,79,0.25)",
  },
  info: {
    bg:     "rgba(79,140,255,0.12)",
    color:  "var(--color-info)",
    border: "rgba(79,140,255,0.25)",
  },
  mode: {
    bg:     "var(--color-accent-dim)",
    color:  "var(--color-accent)",
    border: "rgba(255,255,255,0.08)",
  },
};

function confidenceVariant(confidence: number): ChipVariant {
  if (confidence >= 0.8) return "success";
  if (confidence >= 0.5) return "warn";
  return "danger";
}

/**
 * InlineChip — a small labelled pill used inline within blocks or text.
 */
export default function InlineChip({
  label,
  variant,
  confidence,
  onRemove,
  onClick,
  title,
}: InlineChipProps) {
  const resolvedVariant =
    variant ?? (confidence !== undefined ? confidenceVariant(confidence) : "default");
  const styles = VARIANT_STYLES[resolvedVariant];

  return (
    <span
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={
        onClick
          ? (e) => { if (e.key === "Enter" || e.key === " ") onClick(); }
          : undefined
      }
      title={title}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        height: "var(--chip-height)",
        padding: "0 8px",
        borderRadius: "var(--chip-radius)",
        fontSize: "var(--chip-font-size)",
        fontWeight: 500,
        background: styles.bg,
        color: styles.color,
        border: `1px solid ${styles.border}`,
        cursor: onClick ? "pointer" : "default",
        userSelect: "none",
        lineHeight: 1,
        whiteSpace: "nowrap",
      }}
    >
      {label}
      {confidence !== undefined && (
        <span style={{ opacity: 0.75 }}>{Math.round(confidence * 100)}%</span>
      )}
      {onRemove && (
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(); }}
          style={{
            background: "transparent",
            border: "none",
            cursor: "pointer",
            color: "inherit",
            padding: "0 0 0 2px",
            lineHeight: 1,
            fontSize: 10,
            opacity: 0.7,
          }}
          aria-label={`Remove ${label} chip`}
        >
          ✕
        </button>
      )}
    </span>
  );
}
