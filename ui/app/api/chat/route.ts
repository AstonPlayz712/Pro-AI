import { NextResponse } from "next/server";

import type { ChatMessage } from "../../../core/chatTypes";
import type { EngineMode } from "../../../core/engineSelector";
import { selectEngine } from "../../../core/engineSelector";
import type { ConnectivityState } from "../../../core/connectivity";
import { buildProjectSystemPrompt } from "../../../core/platformProjects";
import { CloudEngine } from "../../../engines/cloudEngine";
import { LocalEngine } from "../../../engines/localEngine";

export const runtime = "nodejs";

type ChatRequestBody = {
  messages: ChatMessage[];
  mode?: EngineMode;
  cloudModel?: string;
  localModel?: string;
  projectId?: string;
  connectivity?: ConnectivityState;
};

export async function POST(req: Request) {
  const body = (await req.json()) as ChatRequestBody;
  const messages = body.messages ?? [];
  const mode = body.mode ?? "auto";
  const cloudModel = body.cloudModel;
  const localModel = body.localModel;
  const projectId = body.projectId;
  const connectivity = body.connectivity;
  const projectPrompt = buildProjectSystemPrompt(projectId);
  const scopedMessages: ChatMessage[] = [{ role: "system", content: projectPrompt }, ...messages];

  const selected = await selectEngine(mode, { connectivity });
  const engine =
    selected.engineId === "cloud"
      ? new CloudEngine({ model: cloudModel })
      : new LocalEngine({ model: localModel });

  const iterable = await engine.generate(scopedMessages);

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const encoder = new TextEncoder();
      try {
        for await (const chunk of iterable) {
          controller.enqueue(encoder.encode(chunk));
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        controller.enqueue(encoder.encode(`\n[error:${engine.id}] ${message}\n`));
      } finally {
        controller.close();
      }
    },
  });

  const res = new NextResponse(stream, {
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "x-engine-id": engine.id,
    },
  });

  return res;
}
