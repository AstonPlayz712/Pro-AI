"use client";

import React from "react";
import Block from "./Block";
import type { Block as BlockData } from "../../hooks/useBlocks";

interface Props {
  block: BlockData;
}

/**
 * DiagramBlock — renders diagram source (e.g. Mermaid / ASCII) inside a
 * scrollable pre-formatted container, with a placeholder prompting input.
 */
export default function DiagramBlock({ block }: Props) {
  return (
    <Block block={block}>
      {block.content ? (
        <div
          style={{
            background: "var(--color-surface-3)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-md)",
            padding: "var(--space-4)",
            overflowX: "auto",
          }}
        >
          <pre
            style={{
              margin: 0,
              fontFamily: "var(--font-mono)",
              fontSize: "var(--text-xs)",
              color: "var(--color-text-muted)",
              lineHeight: "var(--leading-normal)",
              whiteSpace: "pre",
            }}
          >
            {block.content}
          </pre>
        </div>
      ) : (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            minHeight: 120,
            border: "1.5px dashed var(--color-border)",
            borderRadius: "var(--radius-md)",
            color: "var(--color-text-dim)",
            fontSize: "var(--text-sm)",
            flexDirection: "column",
            gap: "var(--space-2)",
          }}
        >
          <span style={{ fontSize: 28, opacity: 0.4 }}>⬡</span>
          <span>Diagram output will render here</span>
        </div>
      )}
    </Block>
  );
}
