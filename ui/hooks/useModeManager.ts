"use client";

/** Hook wrapper around the global mode context. */

import { useContext } from "react";

import { ModeContext } from "../context/ModeContext";

export function useModeManager() {
  const ctx = useContext(ModeContext);
  if (!ctx) {
    throw new Error("useModeManager must be used within <ModeProvider>.");
  }
  return ctx;
}
