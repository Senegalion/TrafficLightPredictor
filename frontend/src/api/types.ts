export type SignalPhase = "RED" | "YELLOW" | "GREEN";

export type PredictionStatus =
  | "OK"
  | "LOW_CONFIDENCE"
  | "INSUFFICIENT_DATA"
  | "UNSUPPORTED_SIGNAL"
  | "MODEL_UNAVAILABLE";

export type DataOrigin = "REAL" | "SIMULATED" | "NONE";

export interface TrafficSignal {
  id: number;
  code: string;
  name: string;
  description: string | null;
  approach: string | null;
  configurationSource: "SAMPLE" | "VERIFIED";
}

export interface Intersection {
  id: number;
  code: string;
  name: string;
  city: string;
  description: string | null;
  latitude: number;
  longitude: number;
  locationSource: "OPENSTREETMAP" | "SAMPLE";
  osmReference: string | null;
  signals: TrafficSignal[];
}

export interface Observation {
  id: number;
  intersectionId: number;
  signalId: number;
  signalCode: string;
  observedAt: string;
  phase: SignalPhase;
  phaseDurationSeconds: number | null;
  direction: string | null;
  source: string;
  simulated: boolean;
}

export interface Page<T> {
  content: T[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
}

export interface AnchorObservation {
  id: number;
  phase: SignalPhase;
  observedAt: string;
  phaseDurationSeconds: number | null;
  ageSeconds: number | null;
  source: string;
  simulated: boolean;
}

export interface Prediction {
  id: string;
  intersectionId: number;
  intersectionName: string;
  signalId: number;
  signalCode: string;
  status: PredictionStatus;
  displayable: boolean;
  predictedPhase: SignalPhase | null;
  confidence: number | null;
  phaseProbabilities: Partial<Record<SignalPhase, number>> | null;
  remainingSeconds: number | null;
  remainingSecondsLower: number | null;
  remainingSecondsUpper: number | null;
  targetTime: string;
  createdAt: string;
  modelVersion: string | null;
  trainingDataOrigin: string | null;
  dataOrigin: DataOrigin;
  anchorObservation: AnchorObservation | null;
  message: string | null;
  disclaimer: string;
}

export interface ModelInfo {
  model_version: string;
  trained_at: string;
  training_data_origin: string;
  signals: string[];
  dataset_time_range: [string, string];
  reliability_policy: {
    min_confidence: number;
    max_interval_width_s: number;
    max_anchor_age_s: number;
  };
}
