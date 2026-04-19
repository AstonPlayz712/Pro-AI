"use client";

import React from "react";
import { ModeContext, useModeState } from "../../hooks/useMode";
import { ToneContext, useToneState } from "../../hooks/useTone";
import { DAIStateContext, useDAIStateValue } from "../../hooks/useDAIState";
import { BlocksContext, useBlocksValue } from "../../hooks/useBlocks";
import { modeAccentStyle } from "../../lib/theme";

interface WorkspaceShellProps {
  children: React.ReactNode;
}

/**
 * WorkspaceShell
 *
 * The outermost provider tree and layout container for the Auto workspace.
 * Sets up all context values (mode, tone, DAI state, blocks) and injects the
 * mode-aware accent as CSS variables so every child component can consume
 * `--color-accent` without knowing the active mode.
 */
export default function WorkspaceShell({ children }: WorkspaceShellProps) {
  const modeCtx = useModeState("architect");
  const toneCtx = useToneState("precise");
  const daiCtx = useDAIStateValue();
  const blocksCtx = useBlocksValue();

  return (
    <ModeContext.Provider value={modeCtx}>
      <ToneContext.Provider value={toneCtx}>
        <DAIStateContext.Provider value={daiCtx}>
          <BlocksContext.Provider value={blocksCtx}>
            <div
              style={{
                ...modeAccentStyle(modeCtx.mode),
                display: "flex",
                flexDirection: "column",
                height: "100vh",
                overflow: "hidden",
                background: "var(--color-bg)",
                color: "var(--color-text)",
              }}
            >
              {children}
            </div>
          </BlocksContext.Provider>
        </DAIStateContext.Provider>
      </ToneContext.Provider>
    </ModeContext.Provider>
  );
}
