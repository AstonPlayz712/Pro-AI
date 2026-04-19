"use client";

import React from "react";
import Block from "./Block";
import type { Block as BlockData } from "../../hooks/useBlocks";
import { useBlocks } from "../../hooks/useBlocks";

interface Props {
  block: BlockData;
}

/**
 * NoteBlock — freeform editable markdown-like note surface.
 */
export default function NoteBlock({ block }: Props) {
  const { updateBlock } = useBlocks();

  return (
    <Block block={block}>
      <textarea
        defaultValue={block.content}
        placeholder="Write a note…"
        onBlur={(e) => updateBlock(block.id, { content: e.target.value })}
        rows={5}
        style={{
          width: "100%",
          background: "transparent",
          border: "none",
          color: "var(--color-text)",
          fontFamily: "var(--font-sans)",
          fontSize: "var(--text-sm)",
          lineHeight: "var(--leading-loose)",
          resize: "vertical",
          outline: "none",
          padding: 0,
        }}
        aria-label="Note content"
      />
    </Block>
  );
}
