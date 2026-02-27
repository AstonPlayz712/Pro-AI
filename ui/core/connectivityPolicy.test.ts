import { describe, expect, test } from "vitest";

import { classifyConnectivity } from "./connectivityPolicy";
import type { ConnectivityState } from "./connectivity";

function state(patch: Partial<ConnectivityState>): ConnectivityState {
  return {
    online: true,
    realInternet: true,
    type: "wifi",
    effectiveType: "4g",
    downlink: 50,
    rtt: 30,
    isWifi: true,
    isCellular: false,
    isSlow: false,
    cloudHealthy: true,
    ...patch,
  };
}

describe("connectivity policy", () => {
  test("connectivity tests - offline", () => {
    expect(classifyConnectivity(state({ online: false, realInternet: false }))).toBe("offline");
  });

  test("connectivity tests - slow", () => {
    expect(classifyConnectivity(state({ isSlow: true }))).toBe("slow");
  });

  test("connectivity tests - good", () => {
    expect(classifyConnectivity(state({}))).toBe("good");
  });

  test("connectivity tests - unstable", () => {
    expect(classifyConnectivity(state({ online: true, realInternet: false }))).toBe("unstable");
    expect(classifyConnectivity(state({ cloudHealthy: false }))).toBe("unstable");
  });
});
