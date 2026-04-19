"use client";

import React, { useState } from "react";
import { useBlocks, type Block, type BlockType } from "../../hooks/useBlocks";
import { useMode } from "../../hooks/useMode";
import { getModeTheme } from "../../lib/theme";
import { glassStyle } from "../../lib/glassmorphism";

// ── Type → display metadata ───────────────────────────────────────────────────

const BLOCK_META: Record<BlockType, { label: string; icon: string }> = {
  plan:     { label: "Plan",     icon: "▤" },
  code:     { label: "Code",     icon: "</>" },
  analysis: { label: "Analysis", icon: "∿" },
  diagram:  { label: "Diagram",  icon: "⬡" },
  result:   { label: "Result",   icon: "✓" },
  note:     { label: "Note",     icon: "✎" },
};

const STATUS_COLORS: Record<Block["status"], string> = {
  idle:    "var(--color-text-dim)",
  running: "var(--color-info)",
  done:    "var(--color-success)",
  error:   "var(--color-danger)",
};

// ── Props ─────────────────────────────────────────────────────────────────────

export interface BlockProps {
  block: Block;
  children?: React.ReactNode;
  /** Slot rendered between the header and the body content */
  actions?: React.ReactNode;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Block
 *
 * Base container shared by all block types. Provides:
 * - Header with type badge, title, status indicator, and version picker
 * - Collapsible body
 * - Footer with metadata (model, confidence, timestamps)
 * - Remove action
 */
export default function Block({ block, children, actions }: BlockProps) {
  const { removeBlock, checkoutVersion } = useBlocks();
  const { mode } = useMode();
  const modeTheme = getModeTheme(mode);
  const [collapsed, setCollapsed] = useState(false);
  const meta = BLOCK_META[block.type];

  return (
    <article
      style={{
        ...glassStyle({ blur: 8, opacity: 0.6 }),
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        border: `1px solid var(--color-border)`,
      }}
    >
      {/* Header */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-3)",
          padding: "var(--space-3) var(--space-4)",
          borderBottom: collapsed ? "none" : "1px solid var(--color-border-muted)",
          background: "var(--color-surface-2)",
        }}
      >
        {/* Type badge */}
        <span
          style={{
            fontSize: "var(--text-xs)",
            padding: "2px 8px",
            borderRadius: "var(--radius-pill)",
            background: modeTheme.accentDim,
            color: modeTheme.accent,
            border: `1px solid ${modeTheme.accent}33`,
            fontWeight: 600,
            flexShrink: 0,
          }}
        >
          {meta.icon} {meta.label}
        </span>

        {/* Title */}
        <span
          style={{
            flex: 1,
            fontSize: "var(--text-sm)",
            fontWeight: 500,
            color: "var(--color-text)",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {block.title}
        </span>

        {/* Status dot */}
        <span
          title={`Status: ${block.status}`}
          style={{
            width: 7,
            height: 7,
            borderRadius: "50%",
            background: STATUS_COLORS[block.status],
            flexShrink: 0,
          }}
        />

        {/* Version picker */}
        {block.versions.length > 1 && (
          <select
            value={block.versions[block.versions.length - 1].version}
            onChange={(e) => checkoutVersion(block.id, Number(e.target.value))}
            style={{
              background: "var(--color-surface-3)",
              border: "1px solid var(--color-border)",
              color: "var(--color-text-muted)",
              fontSize: "var(--text-xs)",
              padding: "2px 6px",
              borderRadius: "var(--radius-sm)",
              cursor: "pointer",
            }}
            aria-label="Block version"
          >
            {block.versions.map((v) => (
              <option key={v.version} value={v.version}>
                v{v.version}
              </option>
            ))}
          </select>
        )}

        {/* Extra actions slot */}
        {actions}

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed((c) => !c)}
          style={iconBtnStyle}
          aria-label={collapsed ? "Expand block" : "Collapse block"}
        >
          {collapsed ? "▼" : "▲"}
        </button>

        {/* Remove */}
        <button
          onClick={() => removeBlock(block.id)}
          style={{ ...iconBtnStyle, color: "var(--color-danger)" }}
          aria-label="Remove block"
        >
          ✕
        </button>
      </header>

      {/* Body */}
      {!collapsed && (
        <div style={{ padding: "var(--space-4)" }}>{children}</div>
      )}

      {/* Footer */}
      {!collapsed && (
        <footer
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-4)",
            padding: "var(--space-2) var(--space-4)",
            borderTop: "1px solid var(--color-border-muted)",
            background: "var(--color-surface-1)",
          }}
        >
          {block.model && (
            <MetaItem label="model" value={block.model} />
          )}
          {block.confidence !== undefined && (
            <MetaItem
              label="confidence"
              value={`${Math.round(block.confidence * 100)}%`}
              valueColor={
                block.confidence >= 0.8
                  ? "var(--color-success)"
                  : block.confidence >= 0.5
                  ? "var(--color-warn)"
                  : "var(--color-danger)"
              }
            />
          )}
          <MetaItem label="v" value={String(block.versions.length)} />
          <MetaItem
            label="updated"
            value={new Date(block.updatedAt).toLocaleTimeString()}
          />
        </footer>
      )}
    </article>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function MetaItem({
  label,
  value,
  valueColor,
}: {
  label: string;
  value: string;
  valueColor?: string;
}) {
  return (
    <span style={{ display: "flex", gap: "var(--space-1)", fontSize: "var(--text-xs)" }}>
      <span style={{ color: "var(--color-text-dim)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
        {label}
      </span>
      <span style={{ color: valueColor ?? "var(--color-text-muted)" }}>{value}</span>
    </span>
  );
}

const iconBtnStyle: React.CSSProperties = {
  background: "transparent",
  border: "none",
  cursor: "pointer",
  color: "var(--color-text-muted)",
  fontSize: "var(--text-xs)",
  padding: "2px 4px",
  borderRadius: "var(--radius-sm)",
  lineHeight: 1,
};
