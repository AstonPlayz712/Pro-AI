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

export type ConnectivityOptions = {
  ttlMs?: number;
  forceRefresh?: boolean;
  healthTimeoutMs?: number;
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

type Cached<T> = {
  value: T;
  ts: number;
};

const stateCache: {
  cached?: Cached<ConnectivityState>;
  inflight?: Promise<ConnectivityState>;
} = {};

type HealthCache = {
  cached?: Cached<boolean>;
  inflight?: Promise<boolean>;
  failures: number;
  nextAllowedAt: number;
};

const internetHealth: HealthCache = { failures: 0, nextAllowedAt: 0 };
const cloudHealth: HealthCache = { failures: 0, nextAllowedAt: 0 };

function backoffDelayMs(failures: number) {
  const base = 500;
  const max = 30_000;
  const pow = Math.min(10, Math.max(0, failures));
  return Math.min(max, base * 2 ** pow);
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

async function cachedHealthCheck(cache: HealthCache, fn: (timeoutMs: number) => Promise<boolean>, timeoutMs: number): Promise<boolean> {
  const now = Date.now();
  if (cache.cached && now - cache.cached.ts < 2_000) return cache.cached.value;
  if (now < cache.nextAllowedAt && cache.cached) return cache.cached.value;
  if (cache.inflight) return cache.inflight;

  cache.inflight = (async () => {
    const ok = await fn(timeoutMs);
    cache.cached = { value: ok, ts: Date.now() };
    cache.failures = ok ? 0 : cache.failures + 1;
    cache.nextAllowedAt = ok ? 0 : Date.now() + backoffDelayMs(cache.failures);
    cache.inflight = undefined;
    return ok;
  })();
  return cache.inflight;
}

export async function getConnectivityState(options: ConnectivityOptions = {}): Promise<ConnectivityState> {
  const ttlMs = options.ttlMs ?? 1500;
  const timeoutMs = options.healthTimeoutMs ?? 1500;
  const force = options.forceRefresh ?? false;
  const now = Date.now();

  if (!force && stateCache.cached && now - stateCache.cached.ts < ttlMs) return stateCache.cached.value;
  if (!force && stateCache.inflight) return stateCache.inflight;

  stateCache.inflight = (async () => {
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

    // Real internet + cloud health are checked server-side to avoid CORS.
    // These calls are cached and backed off to prevent health-check storms.
    const realInternet = online ? await cachedHealthCheck(internetHealth, serverInternetCheck, timeoutMs) : false;
    const cloudHealthy = realInternet ? await cachedHealthCheck(cloudHealth, serverCloudHealthCheck, timeoutMs) : false;

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

    stateCache.cached = { value: state, ts: Date.now() };
    stateCache.inflight = undefined;
    return state;
  })();

  return stateCache.inflight;
}
