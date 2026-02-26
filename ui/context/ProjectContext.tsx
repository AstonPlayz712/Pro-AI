"use client";

import React, { createContext, useCallback, useEffect, useMemo, useState } from "react";

import { getProject, type ProjectDefinition, type ProjectId } from "../core/platformProjects";

type ProjectContextValue = {
  project: ProjectDefinition;
  setProjectId: (projectId: ProjectId) => void;
};

const STORAGE_KEY = "pro-ai:project-id";

export const ProjectContext = createContext<ProjectContextValue | null>(null);

export function ProjectProvider({ children }: { children: React.ReactNode }): React.JSX.Element {
  const [projectId, setProjectIdState] = useState<ProjectId>("chatbot");

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return;
    const project = getProject(stored);
    setProjectIdState(project.id);
  }, []);

  const setProjectId = useCallback((nextProjectId: ProjectId) => {
    setProjectIdState(nextProjectId);
    localStorage.setItem(STORAGE_KEY, nextProjectId);
  }, []);

  const value = useMemo(
    () => ({
      project: getProject(projectId),
      setProjectId,
    }),
    [projectId, setProjectId],
  );

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
}
