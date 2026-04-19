"use client";

import React from "react";
import Block from "./Block";
import type { Block as BlockData } from "../../hooks/useBlocks";
import { useBlocks } from "../../hooks/useBlocks";

interface Props {
  block: BlockData;
}

/**
 * PlanBlock — renders a structured plan as an editable ordered list.
 */
export default function PlanBlock({ block }: Props) {
  const { updateBlock } = useBlocks();

  const lines = block.content
    ? block.content.split("\n").filter(Boolean)
    : [];

  return (
    <Block block={block}>
      {lines.length > 0 ? (
        <ol
          style={{
            margin: 0,
            paddingLeft: "var(--space-5)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-2)",
          }}
        >
          {lines.map((line, i) => (
            <li
              key={i}
              style={{
                fontSize: "var(--text-sm)",
                color: "var(--color-text)",
                lineHeight: "var(--leading-normal)",
              }}
            >
              {line}
            </li>
          ))}
        </ol>
      ) : (
        <textarea
          placeholder="Describe the plan, one step per line…"
          defaultValue={block.content}
          onBlur={(e) =>
            updateBlock(block.id, { content: e.target.value })
          }
          rows={6}
          style={textareaStyle}
          aria-label="Plan content"
        />
      )}
    </Block>
  );
}

const textareaStyle: React.CSSProperties = {
  width: "100%",
  background: "var(--color-surface-3)",
  border: "1px solid var(--color-border)",
  color: "var(--color-text)",
  padding: "var(--space-3)",
  borderRadius: "var(--radius-md)",
  fontFamily: "var(--font-sans)",
  fontSize: "var(--text-sm)",
  lineHeight: "var(--leading-normal)",
  resize: "vertical",
  outline: "none",
};
