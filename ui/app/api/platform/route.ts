import { NextResponse } from "next/server";

import { getProject, type PlatformTaskAction, type ProjectId } from "../../../core/platformProjects";
import { decidePlatformRoute } from "../../../core/platformRouter";

export const runtime = "nodejs";

type PlatformRequestBody = {
  projectId?: ProjectId;
  action?: PlatformTaskAction;
  payload?: Record<string, unknown>;
};

export async function POST(req: Request) {
  const body = (await req.json().catch(() => null)) as PlatformRequestBody | null;
  const projectId = body?.projectId ?? "chatbot";
  const action = body?.action ?? "chat";
  const project = getProject(projectId);
  const route = decidePlatformRoute({ projectId: project.id, action, payload: body?.payload });

  if (route.endpoint !== "/api/platform") {
    return NextResponse.json({
      ok: true,
      delegated: true,
      project,
      route,
      hint: "Use delegated endpoint for this action.",
    });
  }

  return NextResponse.json({
    ok: true,
    delegated: false,
    project,
    action,
    payload: body?.payload ?? {},
    message: "Platform endpoint accepted request. Add concrete project handlers as modules are implemented.",
  });
}
