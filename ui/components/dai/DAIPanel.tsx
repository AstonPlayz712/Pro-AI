"use client";

import React from "react";
import { useDAIState } from "../../hooks/useDAIState";
import { useMode } from "../../hooks/useMode";
import { getModeTheme } from "../../lib/theme";
import { glassStyle } from "../../lib/glassmorphism";
import DAIChip from "./DAIChip";
import InlineChip from "../chips/InlineChip";

/**
 * DAIPanel
 *
 * Fixed right-side panel displaying live DAI state: active goal, subtasks,
 * chip registry, health status, and a timeline of recent events.
 */
export default function DAIPanel() {
  const { state } = useDAIState();
  const { mode } = useMode();
  const modeTheme = getModeTheme(mode);
  const { goal, subtasks, chips, health, timeline, tone } = state;

  const hasIssue =
    health.chipConflicts ||
    health.expiredChips.length > 0 ||
    health.lowConfidence;

  return (
    <aside
      style={{
        ...glassStyle({ blur: 12, opacity: 0.7 }),
        width: "var(--dai-panel-width)",
        minWidth: "var(--dai-panel-width)",
        height: "100%",
        borderLeft: "1px solid var(--color-border)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        flexShrink: 0,
      }}
    >
      {/* Panel header */}
      <div
        style={{
          padding: "var(--space-4)",
          borderBottom: "1px solid var(--color-border-muted)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <span
          style={{
            fontSize: "var(--text-sm)",
            fontWeight: 600,
            color: modeTheme.accent,
          }}
        >
          DAI
        </span>
        <InlineChip
          label={modeTheme.label}
          variant="mode"
          title="Active mode"
        />
      </div>

      {/* Scrollable content */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-1)",
        }}
      >
        {/* Health */}
        {hasIssue && (
          <Section title="Health">
            {health.chipConflicts && (
              <HealthRow icon="⚠" label="Chip conflicts detected" color="var(--color-warn)" />
            )}
            {health.lowConfidence && (
              <HealthRow icon="⚠" label="Low confidence state" color="var(--color-warn)" />
            )}
            {health.expiredChips.map((id) => (
              <HealthRow key={id} icon="✕" label={`Expired: ${id}`} color="var(--color-danger)" />
            ))}
          </Section>
        )}

        {/* Active goal */}
        {goal && (
          <Section title="Goal">
            <p style={bodyTextStyle}>{goal.description}</p>
            {goal.successCriteria && (
              <p style={{ ...bodyTextStyle, color: "var(--color-text-dim)", fontSize: "var(--text-xs)" }}>
                ✓ {goal.successCriteria}
              </p>
            )}
          </Section>
        )}

        {/* Subtasks */}
        {subtasks.length > 0 && (
          <Section title={`Subtasks (${subtasks.length})`}>
            {subtasks.map((t) => (
              <SubtaskRow key={t.id} status={t.status} description={t.description} confidence={t.confidence} />
            ))}
          </Section>
        )}

        {/* Chips */}
        {chips.length > 0 && (
          <Section title={`Chips (${chips.length})`}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-1)" }}>
              {chips.map((c) => (
                <DAIChip key={c.chipId} chip={c} />
              ))}
            </div>
          </Section>
        )}

        {/* Tone */}
        <Section title="Tone">
          <InlineChip label={tone} />
        </Section>

        {/* Timeline */}
        {timeline.length > 0 && (
          <Section title="Timeline">
            {[...timeline].reverse().slice(0, 8).map((ev, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  gap: "var(--space-2)",
                  fontSize: "var(--text-xs)",
                  color: "var(--color-text-muted)",
                  padding: "var(--space-1) 0",
                  borderBottom: "1px solid var(--color-border-muted)",
                }}
              >
                <span style={{ color: "var(--color-text-dim)", flexShrink: 0, fontFamily: "var(--font-mono)" }}>
                  {new Date(ev.timestamp).toLocaleTimeString()}
                </span>
                <span style={{ flex: 1 }}>{ev.details}</span>
              </div>
            ))}
          </Section>
        )}
      </div>
    </aside>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        padding: "var(--space-3) var(--space-4)",
        borderBottom: "1px solid var(--color-border-muted)",
      }}
    >
      <p
        style={{
          margin: "0 0 var(--space-2)",
          fontSize: "var(--text-xs)",
          color: "var(--color-text-dim)",
          textTransform: "uppercase",
          letterSpacing: "0.07em",
          fontWeight: 600,
        }}
      >
        {title}
      </p>
      {children}
    </div>
  );
}

function HealthRow({ icon, label, color }: { icon: string; label: string; color: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-2)",
        fontSize: "var(--text-xs)",
        color,
        padding: "var(--space-1) 0",
      }}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </div>
  );
}

function SubtaskRow({
  status,
  description,
  confidence,
}: {
  status: string;
  description: string;
  confidence: number;
}) {
  const statusIcon: Record<string, string> = {
    pending:     "○",
    in_progress: "◎",
    done:        "●",
    blocked:     "✕",
  };
  const statusColor: Record<string, string> = {
    pending:     "var(--color-text-dim)",
    in_progress: "var(--color-info)",
    done:        "var(--color-success)",
    blocked:     "var(--color-danger)",
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "var(--space-2)",
        fontSize: "var(--text-xs)",
        padding: "var(--space-1) 0",
        color: "var(--color-text-muted)",
      }}
    >
      <span style={{ color: statusColor[status] ?? "var(--color-text-dim)", flexShrink: 0 }}>
        {statusIcon[status] ?? "○"}
      </span>
      <span style={{ flex: 1, lineHeight: "var(--leading-normal)" }}>{description}</span>
      <span style={{ color: "var(--color-text-dim)", flexShrink: 0 }}>
        {Math.round(confidence * 100)}%
      </span>
    </div>
  );
}

const bodyTextStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "var(--text-xs)",
  color: "var(--color-text-muted)",
  lineHeight: "var(--leading-normal)",
};
