import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Prediction } from "../api/types";
import { PredictionResult } from "./PredictionResult";

/** How often the optional auto-refresh requests a new prediction. */
export const AUTO_REFRESH_INTERVAL_MS = 5000;

interface Props {
  intersectionId: number;
  signalId: number;
  onPredicted?: () => void;
}

export function PredictionPanel({ intersectionId, signalId, onPredicted }: Props) {
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const requestId = useRef(0);

  const predict = useCallback(async () => {
    const current = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const result = await api.createPrediction(intersectionId, signalId);
      if (current === requestId.current) {
        setPrediction(result);
        onPredicted?.();
      }
    } catch (e) {
      if (current === requestId.current) {
        setError(e instanceof Error ? e.message : "Prediction request failed");
      }
    } finally {
      if (current === requestId.current) setLoading(false);
    }
  }, [intersectionId, signalId, onPredicted]);

  useEffect(() => {
    // A new signal invalidates the previous result.
    requestId.current++;
    setPrediction(null);
    setError(null);
    setLoading(false);
  }, [intersectionId, signalId]);

  useEffect(() => {
    if (!autoRefresh) return undefined;
    const timer = window.setInterval(predict, AUTO_REFRESH_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [autoRefresh, predict]);

  return (
    <section className="card" aria-labelledby="prediction-heading">
      <div className="card__header">
        <h2 id="prediction-heading">Prediction</h2>
        <div className="controls">
          <label className="toggle">
            <input type="checkbox" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} />
            Auto-refresh every {AUTO_REFRESH_INTERVAL_MS / 1000} s
          </label>
          <button type="button" className="button" onClick={predict} disabled={loading}>
            {loading ? "Predicting…" : "Predict now"}
          </button>
        </div>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {prediction ? (
        <PredictionResult prediction={prediction} />
      ) : (
        !error && <p className="muted">Request a prediction for the selected signal group.</p>
      )}
    </section>
  );
}
