"use client";

import React from "react";
import Block from "./Block";
import type { Block as BlockData } from "../../hooks/useBlocks";

interface Props {
  block: BlockData;
}

/**
 * ResultBlock — final-output block. Shows the result content with a
 * prominent done/error state banner when the block is in a terminal status.
 */
export default function ResultBlock({ block }: Props) {
  return (
    <Block block={block}>
      {block.status === "running" && <RunningBanner />}
      {block.status === "error" && <ErrorBanner />}

      {block.content ? (
        <div
          style={{
            fontSize: "var(--text-sm)",
            color: "var(--color-text)",
            lineHeight: "var(--leading-loose)",
            whiteSpace: "pre-wrap",
            padding:
              block.status !== "idle" ? "var(--space-3) 0 0" : undefined,
          }}
        >
          {block.content}
        </div>
      ) : block.status === "idle" ? (
        <p
          style={{
            margin: 0,
            color: "var(--color-text-dim)",
            fontSize: "var(--text-sm)",
            fontStyle: "italic",
          }}
        >
          Result will appear here…
        </p>
      ) : null}
    </Block>
  );
}

function RunningBanner() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-2)",
        fontSize: "var(--text-xs)",
        color: "var(--color-info)",
        background: "rgba(79,140,255,0.08)",
        padding: "var(--space-2) var(--space-3)",
        borderRadius: "var(--radius-md)",
        marginBottom: "var(--space-3)",
      }}
    >
      <span style={{ animation: "spin 1s linear infinite" }}>↻</span>
      <span>Generating…</span>
    </div>
  );
}

function ErrorBanner() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-2)",
        fontSize: "var(--text-xs)",
        color: "var(--color-danger)",
        background: "rgba(232,90,79,0.08)",
        padding: "var(--space-2) var(--space-3)",
        borderRadius: "var(--radius-md)",
        marginBottom: "var(--space-3)",
      }}
    >
      <span>✕</span>
      <span>Generation failed</span>
    </div>
  );
}
