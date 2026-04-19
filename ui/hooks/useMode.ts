"use client";

import { createContext, useContext, useState } from "react";
import type { Mode } from "../lib/theme";

interface ModeContextValue {
  mode: Mode;
  setMode: (mode: Mode) => void;
}

export const ModeContext = createContext<ModeContextValue>({
  mode: "architect",
  setMode: () => undefined,
});

/** Reads the current DAI mode and exposes a setter. */
export function useMode(): ModeContextValue {
  return useContext(ModeContext);
}

/** Provider component — wrap the workspace root with this. */
export function useModeState(initial: Mode = "architect") {
  const [mode, setMode] = useState<Mode>(initial);
  return { mode, setMode };
}
