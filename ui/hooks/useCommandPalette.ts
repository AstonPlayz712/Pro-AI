"use client";

/** Command palette state hook (placeholder behavior only). */

import { useCallback, useMemo, useState } from "react";

import type { CommandEvent } from "../components/CommandPalette";

export function useCommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);

  const parseCommand = useCallback((raw: string): CommandEvent => {
    const trimmed = raw.trim();
    const [name, ...rest] = trimmed.split(/\s+/g);
    const args: Record<string, string> = {};
    for (const token of rest) {
      const [k, v] = token.split("=");
      if (k && v) args[k] = v;
    }
    return {
      raw,
      name: name || "",
      args,
    };
  }, []);

  return useMemo(
    () => ({
      isOpen,
      query,
      setQuery,
      open,
      close,
      parseCommand,
    }),
    [isOpen, query, open, close, parseCommand]
  );
}
