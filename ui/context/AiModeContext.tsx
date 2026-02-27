"use client";

import React, { createContext, useMemo, useState } from "react";

import { AiModeManager, type AiMode } from "../core/aiModeManager";

type AiModeContextValue = {
  defaultMode: AiMode;
  currentMode: AiMode;
  setDefaultMode: (mode: AiMode) => void;
  temporarilyUse: (mode: AiMode) => void;
  resetToDefault: () => void;
};

const STORAGE_KEY = "pro-ai:default-ai-mode";

export const AiModeContext = createContext<AiModeContextValue | null>(null);

export function AiModeProvider({ children }: { children: React.ReactNode }): React.JSX.Element {
  const initial = (() => {
    if (typeof window === "undefined") return "hybrid" as AiMode;
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === "local" || stored === "cloud" || stored === "hybrid" ? stored : "hybrid";
  })();

  const [manager] = useState(() => new AiModeManager(initial));
  const [defaultMode, setDefaultModeState] = useState<AiMode>(manager.defaultMode);
  const [currentMode, setCurrentModeState] = useState<AiMode>(manager.currentMode);

  const value = useMemo<AiModeContextValue>(
    () => ({
      defaultMode,
      currentMode,
      setDefaultMode(mode) {
        manager.setDefaultMode(mode);
        setDefaultModeState(manager.defaultMode);
        setCurrentModeState(manager.currentMode);
        localStorage.setItem(STORAGE_KEY, mode);
      },
      temporarilyUse(mode) {
        manager.temporarilyUse(mode);
        setCurrentModeState(manager.currentMode);
      },
      resetToDefault() {
        manager.resetToDefault();
        setCurrentModeState(manager.currentMode);
      },
    }),
    [currentMode, defaultMode, manager],
  );

  return <AiModeContext.Provider value={value}>{children}</AiModeContext.Provider>;
}
