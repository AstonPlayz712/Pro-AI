"use client";

import { createContext, useCallback, useContext, useState } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

export type BlockType =
  | "plan"
  | "code"
  | "analysis"
  | "diagram"
  | "result"
  | "note";

export type BlockStatus = "idle" | "running" | "done" | "error";

export interface BlockVersion {
  version: number;
  content: string;
  createdAt: string;
}

export interface Block {
  id: string;
  type: BlockType;
  title: string;
  content: string;
  status: BlockStatus;
  versions: BlockVersion[];
  createdAt: string;
  updatedAt: string;
  /** Optional model that produced the block */
  model?: string;
  /** Optional confidence score 0–1 */
  confidence?: number;
}

// ── Context ───────────────────────────────────────────────────────────────────

interface BlocksContextValue {
  blocks: Block[];
  addBlock: (type: BlockType, title?: string, content?: string) => Block;
  updateBlock: (id: string, patch: Partial<Pick<Block, "title" | "content" | "status" | "model" | "confidence">>) => void;
  removeBlock: (id: string) => void;
  reorderBlocks: (ids: string[]) => void;
  checkoutVersion: (id: string, version: number) => void;
}

export const BlocksContext = createContext<BlocksContextValue>(
  {} as BlocksContextValue,
);

/** Reads the block list and exposes mutation helpers. */
export function useBlocks(): BlocksContextValue {
  return useContext(BlocksContext);
}

// ── Helpers ───────────────────────────────────────────────────────────────────

let _seq = 0;
function newId(type: BlockType): string {
  return `${type}-${Date.now()}-${++_seq}`;
}

/** Full state hook — mount at workspace root. */
export function useBlocksValue(): BlocksContextValue {
  const [blocks, setBlocks] = useState<Block[]>([]);

  const addBlock = useCallback(
    (type: BlockType, title = "", content = ""): Block => {
      const now = new Date().toISOString();
      const block: Block = {
        id: newId(type),
        type,
        title: title || defaultTitle(type),
        content,
        status: "idle",
        versions: [{ version: 1, content, createdAt: now }],
        createdAt: now,
        updatedAt: now,
      };
      setBlocks((bs) => [...bs, block]);
      return block;
    },
    [],
  );

  const updateBlock = useCallback(
    (
      id: string,
      patch: Partial<Pick<Block, "title" | "content" | "status" | "model" | "confidence">>,
    ) => {
      setBlocks((bs) =>
        bs.map((b) => {
          if (b.id !== id) return b;
          const now = new Date().toISOString();
          const nextContent =
            patch.content !== undefined ? patch.content : b.content;
          const versionBumped =
            patch.content !== undefined && patch.content !== b.content;
          const versions = versionBumped
            ? [
                ...b.versions,
                {
                  version: b.versions.length + 1,
                  content: nextContent,
                  createdAt: now,
                },
              ]
            : b.versions;
          return { ...b, ...patch, versions, updatedAt: now };
        }),
      );
    },
    [],
  );

  const removeBlock = useCallback(
    (id: string) => setBlocks((bs) => bs.filter((b) => b.id !== id)),
    [],
  );

  const reorderBlocks = useCallback((ids: string[]) => {
    setBlocks((bs) => {
      const map = Object.fromEntries(bs.map((b) => [b.id, b]));
      const reordered = ids.map((id) => map[id]).filter((b): b is Block => {
        if (!b) console.warn(`[useBlocks] reorderBlocks: unknown id skipped`);
        return b !== undefined;
      });
      return reordered;
    });
  }, []);

  const checkoutVersion = useCallback((id: string, version: number) => {
    setBlocks((bs) =>
      bs.map((b) => {
        if (b.id !== id) return b;
        const v = b.versions.find((vv) => vv.version === version);
        if (!v) return b;
        return { ...b, content: v.content, updatedAt: new Date().toISOString() };
      }),
    );
  }, []);

  return { blocks, addBlock, updateBlock, removeBlock, reorderBlocks, checkoutVersion };
}

// ── Defaults ──────────────────────────────────────────────────────────────────

function defaultTitle(type: BlockType): string {
  const map: Record<BlockType, string> = {
    plan:     "Plan",
    code:     "Code",
    analysis: "Analysis",
    diagram:  "Diagram",
    result:   "Result",
    note:     "Note",
  };
  return map[type];
}
