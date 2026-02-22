export type ConnectivityType = "wifi" | "cellular" | "ethernet" | "unknown";

export type ConnectivityState = {
  online: boolean;
  realInternet: boolean;
  type: ConnectivityType;
  effectiveType: string;
  downlink: number;
  rtt: number;
  isWifi: boolean;
  isCellular: boolean;
  isSlow: boolean;
  cloudHealthy: boolean;
};

type NetworkInformationLike = {
  type?: string;
  effectiveType?: string;
  downlink?: number;
  rtt?: number;
  saveData?: boolean;
  addEventListener?: (name: string, cb: () => void) => void;
  removeEventListener?: (name: string, cb: () => void) => void;
};

function getNavigatorConnection(): NetworkInformationLike | undefined {
  if (typeof navigator === "undefined") return undefined;
  const anyNav = navigator as unknown as { connection?: NetworkInformationLike; mozConnection?: NetworkInformationLike; webkitConnection?: NetworkInformationLike };
  return anyNav.connection ?? anyNav.mozConnection ?? anyNav.webkitConnection;
}

function normalizeType(type?: string): ConnectivityType {
  const t = (type ?? "").toLowerCase();
  if (t.includes("wifi")) return "wifi";
  if (t.includes("cell") || t.includes("mobile")) return "cellular";
  if (t.includes("ether")) return "ethernet";
  return "unknown";
}

async function serverInternetCheck(timeoutMs: number): Promise<boolean> {
  try {
    const resp = await fetch(`/api/health/internet?timeout=${timeoutMs}`, { cache: "no-store" });
    if (!resp.ok) return false;
    const json = (await resp.json()) as { ok?: boolean };
    return Boolean(json.ok);
  } catch {
    return false;
  }
}

async function serverCloudHealthCheck(timeoutMs: number): Promise<boolean> {
  try {
    const resp = await fetch(`/api/health/cloud?timeout=${timeoutMs}`, { cache: "no-store" });
    if (!resp.ok) return false;
    const json = (await resp.json()) as { ok?: boolean };
    return Boolean(json.ok);
  } catch {
    return false;
  }
}

export async function getConnectivityState() {
  const online = typeof navigator !== "undefined" ? navigator.onLine : true;

  const conn = getNavigatorConnection();
  const type = normalizeType(conn?.type);
  const effectiveType = conn?.effectiveType ?? "unknown";
  const downlink = typeof conn?.downlink === "number" ? conn.downlink : 0;
  const rtt = typeof conn?.rtt === "number" ? conn.rtt : 0;

  const isWifi = type === "wifi";
  const isCellular = type === "cellular";

  // Heuristic for slow connections.
  const isSlow =
    (effectiveType === "2g" || effectiveType === "slow-2g") ||
    (downlink > 0 && downlink < 1.5) ||
    (rtt > 0 && rtt > 600) ||
    Boolean(conn?.saveData);

  // Real internet + cloud health are checked server-side to avoid CORS and to use short timeouts.
  const realInternet = online ? await serverInternetCheck(1500) : false;
  const cloudHealthy = realInternet ? await serverCloudHealthCheck(1500) : false;

  const state: ConnectivityState = {
    online,
    realInternet,
    type,
    effectiveType,
    downlink,
    rtt,
    isWifi,
    isCellular,
    isSlow,
    cloudHealthy,
  };
  return state;
}
