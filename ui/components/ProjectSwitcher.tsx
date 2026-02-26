"use client";

import React from "react";

import { listProjects, type ProjectId } from "../core/platformProjects";
import { useProjectManager } from "../hooks/useProjectManager";

export function ProjectSwitcher(): React.JSX.Element {
  const { project, setProjectId } = useProjectManager();
  const projects = listProjects();

  return (
    <div className="vsc-project-switcher">
      <label className="vsc-label" htmlFor="project-switcher">Project</label>
      <select
        id="project-switcher"
        className="vsc-select"
        value={project.id}
        onChange={(e) => setProjectId(e.target.value as ProjectId)}
      >
        {projects.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>
      <div className="vsc-muted">{project.description}</div>
    </div>
  );
}
