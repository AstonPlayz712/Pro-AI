"use client";

import React from "react";
import Block from "./Block";
import type { Block as BlockData } from "../../hooks/useBlocks";

interface Props {
  block: BlockData;
}

/**
 * AnalysisBlock — renders structured analytical output with confidence
 * indicators and evidence sections.
 */
export default function AnalysisBlock({ block }: Props) {
  return (
    <Block block={block}>
      {block.content ? (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-4)",
          }}
        >
          {block.confidence !== undefined && (
            <ConfidenceBar confidence={block.confidence} />
          )}
          <div
            style={{
              fontSize: "var(--text-sm)",
              color: "var(--color-text)",
              lineHeight: "var(--leading-loose)",
              whiteSpace: "pre-wrap",
            }}
          >
            {block.content}
          </div>
        </div>
      ) : (
        <Placeholder text="Analysis output will appear here…" />
      )}
    </Block>
  );
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color =
    confidence >= 0.8
      ? "var(--color-success)"
      : confidence >= 0.5
      ? "var(--color-warn)"
      : "var(--color-danger)";

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: "var(--text-xs)",
          color: "var(--color-text-muted)",
          marginBottom: "var(--space-1)",
        }}
      >
        <span>Confidence</span>
        <span style={{ color }}>{pct}%</span>
      </div>
      <div
        style={{
          height: 4,
          borderRadius: "var(--radius-pill)",
          background: "var(--color-surface-3)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background: color,
            borderRadius: "var(--radius-pill)",
            transition: "width var(--transition-slow)",
          }}
        />
      </div>
    </div>
  );
}

function Placeholder({ text }: { text: string }) {
  return (
    <p
      style={{
        margin: 0,
        color: "var(--color-text-dim)",
        fontSize: "var(--text-sm)",
        fontStyle: "italic",
      }}
    >
      {text}
    </p>
  );
}
