import type { Intersection, ModelInfo, Observation, Page, Prediction } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { Accept: "application/json", ...(init?.body ? { "Content-Type": "application/json" } : {}) },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const problem = await response.json();
      detail = problem.detail ?? problem.title ?? detail;
    } catch {
      // Body is not JSON; keep the status text.
    }
    throw new ApiError(detail || `Request failed with status ${response.status}`, response.status);
  }
  return response.json() as Promise<T>;
}

export const api = {
  listIntersections: () => request<Intersection[]>("/api/v1/intersections"),

  listObservations: (intersectionId: number, signalId: number, size = 20) =>
    request<Page<Observation>>(
      `/api/v1/intersections/${intersectionId}/observations?signalId=${signalId}&size=${size}`,
    ),

  createPrediction: (intersectionId: number, signalId: number) =>
    request<Prediction>("/api/v1/predictions", {
      method: "POST",
      body: JSON.stringify({ intersectionId, signalId }),
    }),

  modelInfo: () => request<ModelInfo>("/api/v1/model"),
};
