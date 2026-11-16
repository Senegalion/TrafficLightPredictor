import type { Intersection, Observation, Prediction } from "../api/types";

export const intersections: Intersection[] = [
  {
    id: 1,
    code: "LDZ-KOS-STR",
    name: "Al. Kościuszki / Struga",
    city: "Łódź",
    description: "Sample description",
    latitude: 51.765294,
    longitude: 19.4543812,
    locationSource: "OPENSTREETMAP",
    osmReference: "traffic_signals nodes: 1",
    signals: [
      {
        id: 10,
        code: "LDZ-KOS-STR-S1",
        name: "Main road signal group",
        description: null,
        approach: "Al. Tadeusza Kościuszki",
        configurationSource: "SAMPLE",
      },
      {
        id: 11,
        code: "LDZ-KOS-STR-S2",
        name: "Cross street signal group",
        description: null,
        approach: "Andrzeja Struga",
        configurationSource: "SAMPLE",
      },
    ],
  },
  {
    id: 2,
    code: "LDZ-SIE-NAR",
    name: "Sienkiewicza / Narutowicza",
    city: "Łódź",
    description: null,
    latitude: 51.7709,
    longitude: 19.4604,
    locationSource: "OPENSTREETMAP",
    osmReference: null,
    signals: [
      {
        id: 20,
        code: "LDZ-SIE-NAR-S1",
        name: "Main road signal group",
        description: null,
        approach: "Henryka Sienkiewicza",
        configurationSource: "SAMPLE",
      },
    ],
  },
];

export function prediction(overrides: Partial<Prediction> = {}): Prediction {
  return {
    id: "7b0a4f8e-4a56-4a4b-9d60-3c4ab1f0c7a1",
    intersectionId: 1,
    intersectionName: "Al. Kościuszki / Struga",
    signalId: 10,
    signalCode: "LDZ-KOS-STR-S1",
    status: "OK",
    displayable: true,
    predictedPhase: "GREEN",
    confidence: 0.91,
    phaseProbabilities: { RED: 0.05, YELLOW: 0.04, GREEN: 0.91 },
    remainingSeconds: 12.3,
    remainingSecondsLower: 8.1,
    remainingSecondsUpper: 15.6,
    targetTime: "2026-10-05T10:00:00Z",
    createdAt: "2026-10-05T10:00:00Z",
    modelVersion: "tlp-gbm-test",
    trainingDataOrigin: "SYNTHETIC",
    dataOrigin: "SIMULATED",
    anchorObservation: {
      id: 5,
      phase: "GREEN",
      observedAt: "2026-10-05T09:59:40Z",
      phaseDurationSeconds: null,
      ageSeconds: 20,
      source: "demo-simulator",
      simulated: true,
    },
    message: null,
    disclaimer: "Experimental estimate, not a guarantee.",
    ...overrides,
  };
}

export const observations: Observation[] = [
  {
    id: 5,
    intersectionId: 1,
    signalId: 10,
    signalCode: "LDZ-KOS-STR-S1",
    observedAt: "2026-10-05T09:59:40Z",
    phase: "GREEN",
    phaseDurationSeconds: 41,
    direction: null,
    source: "demo-simulator",
    simulated: true,
  },
];

/** Minimal fetch mock routing by URL and method. */
export function mockFetch(routes: Record<string, () => { status?: number; body: unknown }>) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const method = init?.method ?? "GET";
    const key = Object.keys(routes).find((route) => {
      const [routeMethod, routePath] = route.split(" ");
      return routeMethod === method && url.startsWith(routePath);
    });
    if (!key) return new Response(JSON.stringify({ title: "Not found" }), { status: 404 });
    const { status = 200, body } = routes[key]();
    return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
  });
}
