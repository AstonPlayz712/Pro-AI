"use client";

import { createContext, useContext, useState } from "react";
import type { Mode } from "../lib/theme";
import type { Tone } from "./useTone";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface DAIGoal {
  id: string;
  description: string;
  successCriteria: string;
}

export interface DAISubtask {
  id: string;
  description: string;
  status: "pending" | "in_progress" | "done" | "blocked";
  confidence: number;
}

export interface DAITimelineEvent {
  timestamp: string;
  eventType: string;
  details: string;
}

export interface DAIChipRef {
  chipId: string;
  source: string;
  confidence: number;
  ttl: number;
  pinned: boolean;
}

export interface DAIHealth {
  chipConflicts: boolean;
  expiredChips: string[];
  lowConfidence: boolean;
}

export interface DAIState {
  goal: DAIGoal | null;
  subtasks: DAISubtask[];
  timeline: DAITimelineEvent[];
  chips: DAIChipRef[];
  mode: Mode;
  tone: Tone;
  health: DAIHealth;
}

// ── Defaults ──────────────────────────────────────────────────────────────────

const DEFAULT_STATE: DAIState = {
  goal: null,
  subtasks: [],
  timeline: [],
  chips: [],
  mode: "architect",
  tone: "precise",
  health: {
    chipConflicts: false,
    expiredChips: [],
    lowConfidence: false,
  },
};

// ── Context ───────────────────────────────────────────────────────────────────

interface DAIStateContextValue {
  state: DAIState;
  setState: React.Dispatch<React.SetStateAction<DAIState>>;
  setGoal: (goal: DAIGoal) => void;
  addSubtask: (subtask: DAISubtask) => void;
  updateSubtask: (id: string, patch: Partial<DAISubtask>) => void;
  addChip: (chip: DAIChipRef) => void;
  removeChip: (chipId: string) => void;
  addTimelineEvent: (event: DAITimelineEvent) => void;
  setMode: (mode: Mode) => void;
  setTone: (tone: Tone) => void;
  setHealth: (health: DAIHealth) => void;
}

export const DAIStateContext = createContext<DAIStateContextValue>(
  {} as DAIStateContextValue,
);

/** Reads DAI state and exposes mutation helpers. */
export function useDAIState(): DAIStateContextValue {
  return useContext(DAIStateContext);
}

/** Full state hook — use inside the workspace provider. */
export function useDAIStateValue(
  initial: Partial<DAIState> = {},
): DAIStateContextValue {
  const [state, setState] = useState<DAIState>({ ...DEFAULT_STATE, ...initial });

  const setGoal = (goal: DAIGoal) =>
    setState((s) => ({ ...s, goal }));

  const addSubtask = (subtask: DAISubtask) =>
    setState((s) => ({ ...s, subtasks: [...s.subtasks, subtask] }));

  const updateSubtask = (id: string, patch: Partial<DAISubtask>) =>
    setState((s) => ({
      ...s,
      subtasks: s.subtasks.map((t) => (t.id === id ? { ...t, ...patch } : t)),
    }));

  const addChip = (chip: DAIChipRef) =>
    setState((s) => ({ ...s, chips: [...s.chips, chip] }));

  const removeChip = (chipId: string) =>
    setState((s) => ({
      ...s,
      chips: s.chips.filter((c) => c.chipId !== chipId),
    }));

  const addTimelineEvent = (event: DAITimelineEvent) =>
    setState((s) => ({ ...s, timeline: [...s.timeline, event] }));

  const setMode = (mode: Mode) => setState((s) => ({ ...s, mode }));
  const setTone = (tone: Tone) => setState((s) => ({ ...s, tone }));
  const setHealth = (health: DAIHealth) => setState((s) => ({ ...s, health }));

  return {
    state,
    setState,
    setGoal,
    addSubtask,
    updateSubtask,
    addChip,
    removeChip,
    addTimelineEvent,
    setMode,
    setTone,
    setHealth,
  };
}
