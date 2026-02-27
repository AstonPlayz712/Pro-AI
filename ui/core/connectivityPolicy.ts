import type { ConnectivityState } from "./connectivity";

export type ConnectivityQuality = "offline" | "slow" | "good" | "unstable";

export function classifyConnectivity(state: ConnectivityState | undefined | null): ConnectivityQuality {
  if (!state) return "unstable";
  if (!state.online) return "offline";
  if (!state.realInternet) return "unstable";
  if (state.isSlow) return "slow";
  if (!state.cloudHealthy) return "unstable";
  return "good";
}
