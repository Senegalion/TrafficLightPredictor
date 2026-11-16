import type { DataOrigin, PredictionStatus, SignalPhase } from "../api/types";

export const PHASE_LABEL: Record<SignalPhase, string> = {
  RED: "Red",
  YELLOW: "Yellow",
  GREEN: "Green",
};

export const STATUS_LABEL: Record<PredictionStatus, string> = {
  OK: "Estimate available",
  LOW_CONFIDENCE: "Low confidence – not shown",
  INSUFFICIENT_DATA: "Insufficient data",
  UNSUPPORTED_SIGNAL: "Signal not supported by model",
  MODEL_UNAVAILABLE: "Model unavailable",
};

export const ORIGIN_LABEL: Record<DataOrigin, string> = {
  REAL: "Real observation",
  SIMULATED: "Simulated data",
  NONE: "No observation",
};

export function formatSeconds(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "–";
  return `${Math.round(value)} s`;
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "–";
  return `${Math.round(value * 100)}%`;
}

export function formatAge(seconds: number | null | undefined): string {
  if (seconds == null || Number.isNaN(seconds)) return "–";
  const rounded = Math.max(0, Math.round(seconds));
  if (rounded < 60) return `${rounded} s ago`;
  const minutes = Math.floor(rounded / 60);
  if (minutes < 60) return `${minutes} min ${rounded % 60} s ago`;
  return `${Math.floor(minutes / 60)} h ${minutes % 60} min ago`;
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
