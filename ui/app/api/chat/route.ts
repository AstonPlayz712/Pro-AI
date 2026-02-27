import { NextResponse } from "next/server";

import type { AiMode } from "../../../core/aiModeManager";
import type { ConnectivityState } from "../../../core/connectivity";
import { classifyConnectivity } from "../../../core/connectivityPolicy";
import { isLargeTask, resolveAutomaticMode } from "../../../core/modeSwitching";
import { buildProjectSystemPrompt } from "../../../core/platformProjects";
import { consumeUploadedFile } from "../../../core/serverFileCache";
import { modeSystemPrompt, UNIFIED_ASSISTANT_IDENTITY } from "../../../core/systemPrompts";
import type { ChatFile, ChatMessage } from "../../../core/chatTypes";
import { CloudEngine } from "../../../engines/cloudEngine";
import { HybridEngine } from "../../../engines/hybridEngine";
import { LocalEngine } from "../../../engines/localEngine";

export const runtime = "nodejs";

type ChatRequestBody = {
  messages: ChatMessage[];
  mode?: AiMode;
  cloudModel?: string;
  localModel?: string;
  projectId?: string;
  file?: ChatFile;
  connectivity?: ConnectivityState;
};

export async function POST(req: Request) {
  const body = (await req.json()) as ChatRequestBody;
  const messages = body.messages ?? [];
  const mode = body.mode ?? "hybrid";
  const cloudModel = body.cloudModel;
  const localModel = body.localModel;
  const projectId = body.projectId;
  const connectivity = body.connectivity;
  const file = body.file ?? consumeUploadedFile();
  const quality = classifyConnectivity(connectivity);
  const modeDecision = resolveAutomaticMode(mode, quality, isLargeTask(messages, file));

  const projectPrompt = buildProjectSystemPrompt(projectId);
  const scopedMessages: ChatMessage[] = [
    { role: "system", content: UNIFIED_ASSISTANT_IDENTITY },
    { role: "system", content: modeSystemPrompt(modeDecision.mode) },
    { role: "system", content: projectPrompt },
    ...messages,
  ];

  const engine =
    modeDecision.mode === "cloud"
      ? new CloudEngine({ model: cloudModel })
      : modeDecision.mode === "local"
        ? new LocalEngine({ model: localModel })
        : new HybridEngine({ cloudModel, localModel });

  const iterable = await engine.generate(scopedMessages, { file, connectivity });

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
      "x-mode-current": modeDecision.mode,
      "x-mode-default": mode,
      "x-mode-temporary": String(modeDecision.temporary),
    },
  });

  return res;
}
