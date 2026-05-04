import type {
  InstrumentPayload,
  Preset,
  RatesResponse,
  SnrResponse,
  SourcePayload,
  StrategyResponse
} from "./types";

export const API_BASE = import.meta.env.VITE_API_URL ?? "";

export function apiAsset(path: string): string {
  return `${API_BASE}${path}`;
}

async function request<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getPresets(): Promise<Preset[]> {
  const data = await request<{ presets: Preset[] }>("/api/presets");
  return data.presets;
}

export async function runSnr(payload: {
  source: SourcePayload;
  config: InstrumentPayload;
  t_total_s: number;
}): Promise<SnrResponse> {
  return request<SnrResponse>("/api/snr-from-time", payload);
}

export async function runRates(payload: {
  source: SourcePayload;
  config: InstrumentPayload;
}): Promise<RatesResponse> {
  return request<RatesResponse>("/api/observation-rates", payload);
}

export async function compareStrategies(payload: {
  source: SourcePayload;
  config: InstrumentPayload;
  t_total_s: number;
}): Promise<StrategyResponse> {
  return request<StrategyResponse>("/api/compare-strategies", payload);
}

export async function runTimeFromSnr(payload: {
  source: SourcePayload;
  config: InstrumentPayload;
  target_snr: number;
  ref_nm: number;
}): Promise<{ t_total_s: number; target_snr: number; ref_nm: number }> {
  return request("/api/time-from-snr", payload);
}

export async function optimizeConfig(payload: {
  source: SourcePayload;
  config: InstrumentPayload;
  science_goal: {
    ref_nm: number;
    target_snr: number;
    target_resolution: number;
    max_time_s: number;
  };
}): Promise<{ config_recommended: Record<string, number | string | boolean> }> {
  return request("/api/optimize-config", payload);
}
