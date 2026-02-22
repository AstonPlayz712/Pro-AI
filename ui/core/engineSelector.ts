import { getConnectivityState } from "./connectivity";
import type { ConnectivityState } from "./connectivity";

export type EngineMode = "auto" | "force-cloud" | "force-local";

export type SelectedEngine = {
  engineId: "cloud" | "local";
  decision: {
    reasonCode:
      | "forced_cloud"
      | "forced_local"
      | "offline"
      | "unstable_internet"
      | "slow_connection"
      | "cloud_unhealthy"
      | "cloud_ok";
    reason: string;
  };
  hybrid: {
    allowSmallOnlineRequests: boolean;
    allowMetadataSync: boolean;
    allowSettingsSync: boolean;
    allowCloudLLMCalls: boolean;
  };
  connectivity: Awaited<ReturnType<typeof getConnectivityState>>;
};

export function explainDecision(sel: SelectedEngine): string {
  return sel.decision.reason;
}

export async function selectEngine(
  mode: EngineMode,
  opts?: {
    connectivity?: ConnectivityState;
  }
): Promise<SelectedEngine> {
  const connectivity = opts?.connectivity ?? (await getConnectivityState());

  if (mode === "force-cloud") {
    return {
      engineId: "cloud",
      decision: { reasonCode: "forced_cloud", reason: "Forced Cloud mode" },
      hybrid: {
        allowSmallOnlineRequests: true,
        allowMetadataSync: true,
        allowSettingsSync: true,
        allowCloudLLMCalls: true,
      },
      connectivity,
    };
  }

  if (mode === "force-local") {
    return {
      engineId: "local",
      decision: { reasonCode: "forced_local", reason: "Forced Local mode" },
      hybrid: {
        allowSmallOnlineRequests: false,
        allowMetadataSync: false,
        allowSettingsSync: false,
        allowCloudLLMCalls: false,
      },
      connectivity,
    };
  }

  if (!connectivity.online) {
    return {
      engineId: "local",
      decision: { reasonCode: "offline", reason: "Offline" },
      hybrid: {
        allowSmallOnlineRequests: false,
        allowMetadataSync: false,
        allowSettingsSync: false,
        allowCloudLLMCalls: false,
      },
      connectivity,
    };
  }

  if (connectivity.online && !connectivity.realInternet) {
    return {
      engineId: "local",
      decision: { reasonCode: "unstable_internet", reason: "Online but internet looks unstable" },
      hybrid: {
        allowSmallOnlineRequests: true,
        allowMetadataSync: true,
        allowSettingsSync: true,
        allowCloudLLMCalls: false,
      },
      connectivity,
    };
  }

  if (connectivity.isSlow) {
    return {
      engineId: "local",
      decision: { reasonCode: "slow_connection", reason: "Slow connection detected" },
      hybrid: {
        allowSmallOnlineRequests: true,
        allowMetadataSync: true,
        allowSettingsSync: true,
        allowCloudLLMCalls: false,
      },
      connectivity,
    };
  }

  if (!connectivity.cloudHealthy) {
    return {
      engineId: "local",
      decision: { reasonCode: "cloud_unhealthy", reason: "Cloud LLM health check failed" },
      hybrid: {
        allowSmallOnlineRequests: true,
        allowMetadataSync: true,
        allowSettingsSync: true,
        allowCloudLLMCalls: false,
      },
      connectivity,
    };
  }

  // Auto mode.
  if (connectivity.realInternet === true && connectivity.isSlow === false && connectivity.cloudHealthy === true) {
    return {
      engineId: "cloud",
      decision: { reasonCode: "cloud_ok", reason: "Internet looks stable and cloud is healthy" },
      hybrid: {
        allowSmallOnlineRequests: true,
        allowMetadataSync: true,
        allowSettingsSync: true,
        allowCloudLLMCalls: true,
      },
      connectivity,
    };
  }

  // Hybrid: local due to slowness/instability.
  return {
    engineId: "local",
    decision: { reasonCode: "cloud_unhealthy", reason: "Falling back to local" },
    hybrid: {
      allowSmallOnlineRequests: true,
      allowMetadataSync: true,
      allowSettingsSync: true,
      allowCloudLLMCalls: false,
    },
    connectivity,
  };
}
