import { describe, expect, test } from "vitest";

import { resolveAutomaticMode } from "./modeSwitching";

describe("automatic mode switching", () => {
  test("local->cloud temporary for large task on good connectivity", () => {
    const decision = resolveAutomaticMode("local", "good", true);
    expect(decision.mode).toBe("cloud");
    expect(decision.temporary).toBe(true);
  });

  test("cloud->local temporary while offline", () => {
    const decision = resolveAutomaticMode("cloud", "offline", false);
    expect(decision.mode).toBe("local");
    expect(decision.temporary).toBe(true);
  });

  test("hybrid stays hybrid", () => {
    const decision = resolveAutomaticMode("hybrid", "slow", true);
    expect(decision.mode).toBe("hybrid");
    expect(decision.temporary).toBe(false);
  });
});
