"use client";

import React from "react";
import Block from "./Block";
import type { Block as BlockData } from "../../hooks/useBlocks";
import { useBlocks } from "../../hooks/useBlocks";

interface Props {
  block: BlockData;
}

/**
 * CodeBlock — monospaced code viewer/editor with syntax-highlighted appearance.
 */
export default function CodeBlock({ block }: Props) {
  const { updateBlock } = useBlocks();

  return (
    <Block block={block}>
      <pre
        style={{
          margin: 0,
          padding: "var(--space-4)",
          background: "var(--color-surface-3)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-md)",
          overflow: "auto",
          maxHeight: 400,
        }}
      >
        <code
          role="textbox"
          aria-label="Code content"
          aria-multiline="true"
          contentEditable
          suppressContentEditableWarning
          onBlur={(e) =>
            updateBlock(block.id, {
              content: e.currentTarget.textContent ?? "",
            })
          }
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "var(--text-sm)",
            color: "var(--color-text)",
            lineHeight: "var(--leading-loose)",
            outline: "none",
            whiteSpace: "pre",
          }}
        >
          {block.content || "// paste or type code here…"}
        </code>
      </pre>
    </Block>
  );
}
