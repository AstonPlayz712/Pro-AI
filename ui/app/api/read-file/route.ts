import { NextResponse } from "next/server";
import mammoth from "mammoth";
import { PDFParse } from "pdf-parse";

import { storeUploadedFile } from "../../../core/serverFileCache";
import type { ChatFile } from "../../../core/chatTypes";

export const runtime = "nodejs";

async function extractText(file: File): Promise<string> {
  const lower = file.name.toLowerCase();
  const bytes = Buffer.from(await file.arrayBuffer());

  if (file.type.includes("text") || lower.endsWith(".txt") || lower.endsWith(".md")) {
    return bytes.toString("utf-8");
  }

  if (file.type.includes("pdf") || lower.endsWith(".pdf")) {
    const parser = new PDFParse({ data: bytes });
    const parsed = await parser.getText();
    await parser.destroy();
    return parsed.text ?? "";
  }

  if (
    file.type.includes("word") ||
    lower.endsWith(".docx")
  ) {
    const parsed = await mammoth.extractRawText({ buffer: bytes });
    return parsed.value ?? "";
  }

  throw new Error("Unsupported file type. Please upload PDF, DOCX, or TXT.");
}

export async function POST(req: Request) {
  try {
    const form = await req.formData();
    const uploaded = form.get("file");
    if (!(uploaded instanceof File)) {
      return NextResponse.json({ ok: false, error: "Missing file upload." }, { status: 400 });
    }

    const content = (await extractText(uploaded)).trim();
    const file: ChatFile = {
      name: uploaded.name,
      type: uploaded.type || "application/octet-stream",
      content,
    };
    storeUploadedFile(file);

    return NextResponse.json({ ok: true, file });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: message }, { status: 400 });
  }
}
