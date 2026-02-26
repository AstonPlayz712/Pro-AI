"use client";

import { useContext } from "react";

import { ProjectContext } from "../context/ProjectContext";

export function useProjectManager() {
  const ctx = useContext(ProjectContext);
  if (!ctx) {
    throw new Error("useProjectManager must be used within <ProjectProvider>.");
  }
  return ctx;
}
