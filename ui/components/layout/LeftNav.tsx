"use client";

import React, { useState } from "react";
import { useMode } from "../../hooks/useMode";
import { useBlocks, type BlockType } from "../../hooks/useBlocks";
import { getModeTheme } from "../../lib/theme";

interface NavItem {
  id: string;
  label: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: "workspace", label: "Workspace", icon: "◫" },
  { id: "blocks",    label: "Blocks",    icon: "⊞" },
  { id: "chips",     label: "Chips",     icon: "◈" },
  { id: "memory",    label: "Memory",    icon: "⟳" },
  { id: "settings",  label: "Settings",  icon: "⚙" },
];

const BLOCK_TYPES: { type: BlockType; label: string; icon: string }[] = [
  { type: "plan",     label: "Plan",     icon: "▤" },
  { type: "code",     label: "Code",     icon: "</>" },
  { type: "analysis", label: "Analysis", icon: "∿" },
  { type: "diagram",  label: "Diagram",  icon: "⬡" },
  { type: "result",   label: "Result",   icon: "✓" },
  { type: "note",     label: "Note",     icon: "✎" },
];

/**
 * LeftNav
 *
 * Collapsible sidebar navigation. Shows primary workspace sections and a quick
 * "add block" palette. Collapses to icon-only mode at narrow widths.
 */
export default function LeftNav() {
  const [collapsed, setCollapsed] = useState(false);
  const [active, setActive] = useState("workspace");
  const { mode } = useMode();
  const { addBlock } = useBlocks();
  const modeTheme = getModeTheme(mode);

  const width = collapsed ? "var(--leftnav-collapsed)" : "var(--leftnav-width)";

  return (
    <aside
      style={{
        width,
        minWidth: width,
        maxWidth: width,
        height: "100%",
        background: "var(--color-surface-1)",
        borderRight: "1px solid var(--color-border)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        transition: "width var(--transition-slow), min-width var(--transition-slow)",
        flexShrink: 0,
      }}
    >
      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed((c) => !c)}
        style={{
          background: "transparent",
          border: "none",
          color: "var(--color-text-muted)",
          cursor: "pointer",
          padding: "var(--space-4)",
          textAlign: "right",
          fontSize: "var(--text-md)",
          alignSelf: "flex-end",
        }}
        aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
      >
        {collapsed ? "›" : "‹"}
      </button>

      {/* Primary nav */}
      <nav style={{ flex: 1, display: "flex", flexDirection: "column", gap: 2, padding: "0 var(--space-2)" }}>
        {NAV_ITEMS.map((item) => {
          const isActive = item.id === active;
          return (
            <button
              key={item.id}
              onClick={() => setActive(item.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-3)",
                padding: "var(--space-2) var(--space-3)",
                borderRadius: "var(--radius-md)",
                border: "none",
                cursor: "pointer",
                background: isActive ? modeTheme.accentDim : "transparent",
                color: isActive ? modeTheme.accent : "var(--color-text-muted)",
                fontWeight: isActive ? 600 : 400,
                fontSize: "var(--text-sm)",
                textAlign: "left",
                whiteSpace: "nowrap",
                overflow: "hidden",
                transition: "background var(--transition-base), color var(--transition-base)",
              }}
            >
              <span style={{ fontSize: "var(--text-md)", flexShrink: 0 }}>{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* Add block palette */}
      {!collapsed && (
        <div
          style={{
            padding: "var(--space-4) var(--space-3)",
            borderTop: "1px solid var(--color-border-muted)",
          }}
        >
          <p
            style={{
              fontSize: "var(--text-xs)",
              color: "var(--color-text-dim)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              marginBottom: "var(--space-2)",
            }}
          >
            Add block
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-1)" }}>
            {BLOCK_TYPES.map(({ type, label, icon }) => (
              <button
                key={type}
                onClick={() => addBlock(type)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-1)",
                  padding: "4px 6px",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--color-border-muted)",
                  background: "var(--color-surface-2)",
                  color: "var(--color-text-muted)",
                  fontSize: "var(--text-xs)",
                  cursor: "pointer",
                  transition: "background var(--transition-fast), color var(--transition-fast)",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = modeTheme.accentDim;
                  (e.currentTarget as HTMLButtonElement).style.color = modeTheme.accent;
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = "var(--color-surface-2)";
                  (e.currentTarget as HTMLButtonElement).style.color = "var(--color-text-muted)";
                }}
              >
                <span>{icon}</span>
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
}
