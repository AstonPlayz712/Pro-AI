"use client";

import React from "react";
import { useBlocks } from "../../hooks/useBlocks";
import PlanBlock from "../blocks/PlanBlock";
import CodeBlock from "../blocks/CodeBlock";
import AnalysisBlock from "../blocks/AnalysisBlock";
import DiagramBlock from "../blocks/DiagramBlock";
import ResultBlock from "../blocks/ResultBlock";
import NoteBlock from "../blocks/NoteBlock";
import type { Block } from "../../hooks/useBlocks";

/**
 * MainWorkspace
 *
 * The scrollable canvas that renders the ordered block list. Empty state is
 * shown when no blocks exist.
 */
export default function MainWorkspace() {
  const { blocks } = useBlocks();

  return (
    <main
      style={{
        flex: 1,
        overflowY: "auto",
        padding: "var(--space-6)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-5)",
      }}
    >
      {blocks.length === 0 ? (
        <EmptyState />
      ) : (
        blocks.map((block) => <BlockRenderer key={block.id} block={block} />)
      )}
    </main>
  );
}

function BlockRenderer({ block }: { block: Block }) {
  switch (block.type) {
    case "plan":     return <PlanBlock block={block} />;
    case "code":     return <CodeBlock block={block} />;
    case "analysis": return <AnalysisBlock block={block} />;
    case "diagram":  return <DiagramBlock block={block} />;
    case "result":   return <ResultBlock block={block} />;
    case "note":     return <NoteBlock block={block} />;
    default:         return null;
  }
}

function EmptyState() {
  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "var(--space-4)",
        color: "var(--color-text-dim)",
        textAlign: "center",
        userSelect: "none",
      }}
    >
      <div style={{ fontSize: 48, opacity: 0.3 }}>◫</div>
      <p style={{ fontSize: "var(--text-base)", margin: 0 }}>
        Workspace is empty
      </p>
      <p style={{ fontSize: "var(--text-sm)", margin: 0 }}>
        Add a block from the sidebar or use the command surface below
      </p>
    </div>
  );
}
