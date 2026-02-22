"use client";

/** Command palette placeholder: accepts text and emits structured command events. */

import React from "react";

import { useCommandPalette } from "../hooks/useCommandPalette";

export type CommandEvent = {
  raw: string;
  name: string;
  args: Record<string, string>;
};

export type CommandPaletteProps = {
  onCommand?: (event: CommandEvent) => void;
};

export function CommandPalette({ onCommand }: CommandPaletteProps): React.JSX.Element {
  const { isOpen, query, setQuery, open, close, parseCommand } = useCommandPalette();

  if (!isOpen) {
    return (
      <button type="button" className="vsc-command-open" onClick={open}>
        Command Palette
      </button>
    );
  }

  return (
    <div className="vsc-command" role="dialog" aria-label="Command palette">
      <form
        className="vsc-command__form"
        onSubmit={(e) => {
          e.preventDefault();
          const event = parseCommand(query);
          onCommand?.(event);
          close();
          setQuery("");
        }}
      >
        <input
          className="vsc-command__input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type a command…"
          autoFocus
        />
        <div className="vsc-command__actions">
          <button type="submit" className="vsc-command__btn">
            Run
          </button>
          <button type="button" className="vsc-command__btn" onClick={close}>
            Close
          </button>
        </div>
      </form>
      <div className="vsc-command__hint vsc-muted">Placeholder: wired to emit a structured event.</div>
    </div>
  );
}
