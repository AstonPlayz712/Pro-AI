import { describe, expect, test } from "vitest";

import { decidePlatformRoute } from "./platformRouter";

describe("decidePlatformRoute", () => {
  test("routes chat action to /api/chat", () => {
    const route = decidePlatformRoute({ projectId: "chatbot", action: "chat" });
    expect(route.endpoint).toBe("/api/chat");
  });

  test("routes sync action to /api/sync", () => {
    const route = decidePlatformRoute({ projectId: "sync", action: "sync" });
    expect(route.endpoint).toBe("/api/sync");
  });

  test("routes diagnostics action to /api/diagnostics/local", () => {
    const route = decidePlatformRoute({ projectId: "diagnostics", action: "run-diagnostics" });
    expect(route.endpoint).toBe("/api/diagnostics/local");
  });

  test("routes future actions through /api/platform", () => {
    const route = decidePlatformRoute({ projectId: "routing", action: "route-plan" });
    expect(route.endpoint).toBe("/api/platform");
  });
});
