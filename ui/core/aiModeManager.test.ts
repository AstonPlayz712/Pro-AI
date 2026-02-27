import { describe, expect, test } from "vitest";

import { AiModeManager } from "./aiModeManager";

describe("AiModeManager", () => {
  test("local mode test", () => {
    const mgr = new AiModeManager("local");
    expect(mgr.defaultMode).toBe("local");
    expect(mgr.currentMode).toBe("local");
  });

  test("cloud mode test", () => {
    const mgr = new AiModeManager("cloud");
    expect(mgr.defaultMode).toBe("cloud");
    expect(mgr.currentMode).toBe("cloud");
  });

  test("hybrid mode test", () => {
    const mgr = new AiModeManager("hybrid");
    expect(mgr.defaultMode).toBe("hybrid");
    expect(mgr.currentMode).toBe("hybrid");
  });

  test("temporary switching test", () => {
    const mgr = new AiModeManager("local");
    mgr.temporarilyUse("cloud");
    expect(mgr.currentMode).toBe("cloud");
    expect(mgr.defaultMode).toBe("local");
  });

  test("return-to-default test", () => {
    const mgr = new AiModeManager("hybrid");
    mgr.temporarilyUse("local");
    mgr.resetToDefault();
    expect(mgr.currentMode).toBe("hybrid");
  });
});
