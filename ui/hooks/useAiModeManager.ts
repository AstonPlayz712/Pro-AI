"use client";

import { useContext } from "react";

import { AiModeContext } from "../context/AiModeContext";

export function useAiModeManager() {
  const ctx = useContext(AiModeContext);
  if (!ctx) {
    throw new Error("useAiModeManager must be used within <AiModeProvider>.");
  }
  return ctx;
}
