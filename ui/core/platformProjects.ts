export type ProjectId =
  | "chatbot"
  | "tube-map"
  | "tfl-live-updates"
  | "routing"
  | "offline-tools"
  | "diagnostics"
  | "sync";

export type ProjectCapability =
  | "chat"
  | "network"
  | "maps"
  | "routing"
  | "offline"
  | "diagnostics"
  | "sync";

export type ProjectDefinition = {
  id: ProjectId;
  name: string;
  description: string;
  capabilities: ProjectCapability[];
  prefersLocal?: boolean;
};

export type PlatformTaskAction =
  | "chat"
  | "route-plan"
  | "live-status"
  | "run-diagnostics"
  | "sync"
  | "offline-tool";

export const PROJECTS: ProjectDefinition[] = [
  {
    id: "chatbot",
    name: "Chatbot",
    description: "General conversational assistant with hybrid cloud/local inference.",
    capabilities: ["chat", "offline", "sync"],
  },
  {
    id: "tube-map",
    name: "Tube Map",
    description: "Station/line exploration and map-aware reasoning workflows.",
    capabilities: ["maps", "routing", "chat", "offline"],
  },
  {
    id: "tfl-live-updates",
    name: "TfL Live Updates",
    description: "Real-time transport status, disruption tracking, and advisories.",
    capabilities: ["network", "chat", "diagnostics", "sync"],
  },
  {
    id: "routing",
    name: "Routing",
    description: "Route planning, alternatives, and travel-time reasoning.",
    capabilities: ["routing", "network", "chat", "offline"],
  },
  {
    id: "offline-tools",
    name: "Offline Tools",
    description: "Local-first tools designed for low/no connectivity conditions.",
    capabilities: ["offline", "chat", "diagnostics"],
    prefersLocal: true,
  },
  {
    id: "diagnostics",
    name: "Diagnostics",
    description: "Connectivity, runtime, and health inspection utilities.",
    capabilities: ["diagnostics", "network", "offline"],
    prefersLocal: true,
  },
  {
    id: "sync",
    name: "Sync",
    description: "Multi-device sync orchestration and queue visibility.",
    capabilities: ["sync", "network", "offline"],
  },
];

export function listProjects(): ProjectDefinition[] {
  return PROJECTS;
}

export function getProject(projectId: string | undefined | null): ProjectDefinition {
  const found = PROJECTS.find((project) => project.id === projectId);
  return found ?? PROJECTS[0];
}

export function buildProjectSystemPrompt(projectId: string | undefined | null): string {
  const project = getProject(projectId);
  const caps = project.capabilities.join(", ");
  return [
    `You are operating inside the '${project.name}' project context.`,
    `Project description: ${project.description}`,
    `Enabled capabilities: ${caps}.`,
    "When uncertain, prefer concise and actionable outputs aligned to this project scope.",
  ].join(" ");
}
