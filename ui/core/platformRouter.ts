import { getProject, type PlatformTaskAction, type ProjectId } from "./platformProjects";

export type PlatformTaskRequest = {
  projectId: ProjectId;
  action: PlatformTaskAction;
  payload?: Record<string, unknown>;
};

export type PlatformRouteDecision = {
  endpoint: string;
  method: "POST" | "GET";
  projectId: ProjectId;
  action: PlatformTaskAction;
};

export function decidePlatformRoute(request: PlatformTaskRequest): PlatformRouteDecision {
  const project = getProject(request.projectId);

  switch (request.action) {
    case "chat":
      return { endpoint: "/api/chat", method: "POST", projectId: project.id, action: request.action };
    case "run-diagnostics":
      return { endpoint: "/api/diagnostics/local", method: "POST", projectId: project.id, action: request.action };
    case "sync":
      return { endpoint: "/api/sync", method: "POST", projectId: project.id, action: request.action };
    case "live-status":
      return { endpoint: "/api/health/internet", method: "GET", projectId: project.id, action: request.action };
    case "route-plan":
    case "offline-tool":
    default:
      return { endpoint: "/api/platform", method: "POST", projectId: project.id, action: request.action };
  }
}
