import type { ChatFile } from "./chatTypes";

let latestUploadedFile: ChatFile | null = null;

export function storeUploadedFile(file: ChatFile) {
  latestUploadedFile = file;
}

export function consumeUploadedFile(): ChatFile | undefined {
  const file = latestUploadedFile ?? undefined;
  latestUploadedFile = null;
  return file;
}
