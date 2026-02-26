import { NextResponse } from "next/server";

import { listProjects } from "../../../core/platformProjects";

export const runtime = "nodejs";

export async function GET() {
  return NextResponse.json({ ok: true, projects: listProjects() });
}
