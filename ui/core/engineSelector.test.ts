import { describe, expect, test } from "vitest";

import { selectEngine } from "./engineSelector";
import type { ConnectivityState } from "./connectivity";

function c(patch: Partial<ConnectivityState>): ConnectivityState {
  return {
    online: true,
    realInternet: true,
    type: "wifi",
    effectiveType: "4g",
    downlink: 50,
    rtt: 50,
    isWifi: true,
    isCellular: false,
    isSlow: false,
    cloudHealthy: true,
    ...patch,
  };
}

describe("selectEngine", () => {
  test("force-cloud always selects cloud", async () => {
    const sel = await selectEngine("force-cloud", { connectivity: c({ online: false, realInternet: false, cloudHealthy: false }) });
    expect(sel.engineId).toBe("cloud");
    expect(sel.decision.reasonCode).toBe("forced_cloud");
  });

  test("force-local always selects local", async () => {
    const sel = await selectEngine("force-local", { connectivity: c({ cloudHealthy: true }) });
    expect(sel.engineId).toBe("local");
    expect(sel.decision.reasonCode).toBe("forced_local");
  });

  test("offline selects local", async () => {
    const sel = await selectEngine("auto", { connectivity: c({ online: false, realInternet: false, cloudHealthy: false }) });
    expect(sel.engineId).toBe("local");
    expect(sel.decision.reasonCode).toBe("offline");
  });

  test("unstable internet selects local", async () => {
    const sel = await selectEngine("auto", { connectivity: c({ online: true, realInternet: false, cloudHealthy: false }) });
    expect(sel.engineId).toBe("local");
    expect(sel.decision.reasonCode).toBe("unstable_internet");
  });

  test("slow connection selects local", async () => {
    const sel = await selectEngine("auto", { connectivity: c({ isSlow: true }) });
    expect(sel.engineId).toBe("local");
    expect(sel.decision.reasonCode).toBe("slow_connection");
  });

  test("cloud unhealthy selects local", async () => {
    const sel = await selectEngine("auto", { connectivity: c({ cloudHealthy: false }) });
    expect(sel.engineId).toBe("local");
    expect(sel.decision.reasonCode).toBe("cloud_unhealthy");
  });

  test("stable internet + healthy cloud selects cloud", async () => {
    const sel = await selectEngine("auto", { connectivity: c({ online: true, realInternet: true, isSlow: false, cloudHealthy: true }) });
    expect(sel.engineId).toBe("cloud");
    expect(sel.decision.reasonCode).toBe("cloud_ok");
  });
});
