import { describe, expect, test } from "vitest";

import { buildProjectSystemPrompt, getProject, listProjects } from "./platformProjects";

describe("platformProjects", () => {
  test("lists supported projects", () => {
    const projects = listProjects();
    expect(projects.length).toBeGreaterThanOrEqual(7);
  });

  test("falls back to chatbot for unknown project", () => {
    const project = getProject("unknown-id");
    expect(project.id).toBe("chatbot");
  });

  test("builds project-scoped system prompt", () => {
    const prompt = buildProjectSystemPrompt("tube-map");
    expect(prompt).toContain("Tube Map");
    expect(prompt).toContain("Enabled capabilities");
  });
});
