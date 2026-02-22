"use client";

/** Global mode context used to switch between workspace views. */

import React, { createContext, useCallback, useMemo, useState } from "react";

export type Mode = "smart" | "debug" | "automation" | "insight";

export type ModeContextValue = {
  mode: Mode;
  setMode: (mode: Mode) => void;
};

export const ModeContext = createContext<ModeContextValue | null>(null);

export function ModeProvider({ children }: { children: React.ReactNode }): React.JSX.Element {
  const [mode, setModeState] = useState<Mode>("smart");

  const setMode = useCallback((next: Mode) => setModeState(next), []);

  const value = useMemo(() => ({ mode, setMode }), [mode, setMode]);

  return <ModeContext.Provider value={value}>{children}</ModeContext.Provider>;
}
