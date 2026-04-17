// Thin fetch wrapper for the FastAPI backend.
// In dev (SvelteKit) we rely on the Vite proxy; in Tauri builds we hit the
// full URL from PUBLIC_API_BASE.
import { env } from '$env/dynamic/public';

const BASE = env.PUBLIC_API_BASE ?? '';

export interface RunRequest {
  intent: string;
  payload: Record<string, unknown>;
  user_id: string;
  session_id?: string | null;
  sensitivity?: string;
  complexity?: string;
  latency_budget_ms?: number | null;
}

export interface RouteInfo {
  target: string;
  reason: string;
  confidence: number;
}

export interface ContextInfo {
  memory_size: number;
  system_state: Record<string, unknown>;
  notes: string[];
}

export interface EngineResult {
  engine: string;
  task_id: string;
  intent: string;
  payload: Record<string, unknown>;
  context_notes: string[];
}

export interface RunResponse {
  task_id: string;
  intent: string;
  route: RouteInfo;
  context: ContextInfo;
  result: EngineResult;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  autolinkRun: (req: RunRequest) => post<RunResponse>('/autolink/run', req),
  autolinkPing: () => get<{ status: string; service: string }>('/autolink/ping'),
  daiRun: (req: RunRequest) => post<RunResponse>('/dai/run', req),
  daiSystemMap: () => get<Record<string, unknown>>('/dai/system-map'),
  daiEvolutionLog: () => get<Record<string, unknown>>('/dai/evolution-log')
};
