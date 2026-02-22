import { getConnectivityState } from "./connectivity";
import type { ConnectivityState } from "./connectivity";

export type EngineMode = "auto" | "force-cloud" | "force-local";

export type SelectedEngine = {
  engineId: "cloud" | "local";
  hybrid: {
    allowSmallOnlineRequests: boolean;
    allowMetadataSync: boolean;
    allowSettingsSync: boolean;
    allowCloudLLMCalls: boolean;
  };
  connectivity: Awaited<ReturnType<typeof getConnectivityState>>;
};

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
      hybrid: {
        allowSmallOnlineRequests: false,
        allowMetadataSync: false,
        allowSettingsSync: false,
        allowCloudLLMCalls: false,
      },
      connectivity,
    };
  }

  // Auto mode.
  if (connectivity.realInternet === true && connectivity.isSlow === false && connectivity.cloudHealthy === true) {
    return {
      engineId: "cloud",
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
    hybrid: {
      allowSmallOnlineRequests: true,
      allowMetadataSync: true,
      allowSettingsSync: true,
      allowCloudLLMCalls: false,
    },
    connectivity,
  };
}
