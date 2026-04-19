"use client";

import { createContext, useContext, useState } from "react";

export type Tone = "precise" | "conversational" | "minimalist" | "technical";

interface ToneContextValue {
  tone: Tone;
  setTone: (tone: Tone) => void;
}

export const ToneContext = createContext<ToneContextValue>({
  tone: "precise",
  setTone: () => undefined,
});

/** Reads the active DAI tone and exposes a setter. */
export function useTone(): ToneContextValue {
  return useContext(ToneContext);
}

/** State hook — use inside the workspace provider. */
export function useToneState(initial: Tone = "precise") {
  const [tone, setTone] = useState<Tone>(initial);
  return { tone, setTone };
}
