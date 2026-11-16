import type { Prediction, SignalPhase } from "../api/types";
import { formatAge, formatPercent, formatSeconds, ORIGIN_LABEL, PHASE_LABEL, STATUS_LABEL } from "../lib/format";
import { Badge } from "./Badge";
import { TrafficLight } from "./TrafficLight";

const PHASES: SignalPhase[] = ["RED", "YELLOW", "GREEN"];

function statusTone(prediction: Prediction) {
  if (prediction.status === "OK") return "success";
  if (prediction.status === "LOW_CONFIDENCE") return "warning";
  return "danger";
}

export function PredictionResult({ prediction }: { prediction: Prediction }) {
  const hasModelOutput = prediction.predictedPhase != null;
  const anchor = prediction.anchorObservation;

  return (
    <article className="prediction" aria-live="polite" aria-label="Prediction result">
      <div className="prediction__badges">
        <Badge tone={statusTone(prediction)}>{STATUS_LABEL[prediction.status]}</Badge>
        <Badge tone={prediction.dataOrigin === "REAL" ? "info" : "warning"}>
          {ORIGIN_LABEL[prediction.dataOrigin]}
        </Badge>
        {prediction.trainingDataOrigin && prediction.trainingDataOrigin !== "REAL" && (
          <Badge tone="warning" title="The model was trained on simulated data">
            Model trained on {prediction.trainingDataOrigin.toLowerCase()} data
          </Badge>
        )}
      </div>

      <div className="prediction__main">
        <TrafficLight phase={prediction.predictedPhase} uncertain={!prediction.displayable} />

        {prediction.displayable && prediction.predictedPhase ? (
          <div className="prediction__estimate">
            <p className="prediction__phase">{PHASE_LABEL[prediction.predictedPhase]}</p>
            <p className="prediction__remaining">
              <span className="prediction__remaining-value">~{formatSeconds(prediction.remainingSeconds)}</span>{" "}
              until change (estimate)
            </p>
            <p className="muted">
              Likely range: {formatSeconds(prediction.remainingSecondsLower)} –{" "}
              {formatSeconds(prediction.remainingSecondsUpper)} (≈80% interval)
            </p>
            <p>
              Confidence: <strong>{formatPercent(prediction.confidence)}</strong>
            </p>
          </div>
        ) : (
          <div className="prediction__estimate">
            <p className="prediction__phase prediction__phase--unavailable">No reliable estimate</p>
            {prediction.message && <p>{prediction.message}</p>}
          </div>
        )}
      </div>

      {hasModelOutput && (
        <details className="prediction__details" open={prediction.displayable}>
          <summary>Model output{prediction.displayable ? "" : " (not reliable enough to display)"}</summary>
          <table className="probabilities">
            <caption className="visually-hidden">Calibrated phase probabilities</caption>
            <tbody>
              {PHASES.map((phase) => {
                const value = prediction.phaseProbabilities?.[phase] ?? 0;
                return (
                  <tr key={phase}>
                    <th scope="row">{PHASE_LABEL[phase]}</th>
                    <td className="probabilities__bar-cell">
                      <span
                        className={`probabilities__bar probabilities__bar--${phase.toLowerCase()}`}
                        style={{ width: `${Math.round(value * 100)}%` }}
                      />
                    </td>
                    <td className="probabilities__value">{formatPercent(value)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="muted small">
            Remaining time (median): {formatSeconds(prediction.remainingSeconds)}, interval{" "}
            {formatSeconds(prediction.remainingSecondsLower)}–{formatSeconds(prediction.remainingSecondsUpper)}.
            Confidence is the probability of the predicted phase after isotonic calibration on held-out{" "}
            {prediction.trainingDataOrigin === "REAL" ? "" : "synthetic "}data; it is not validated on real signals.
          </p>
        </details>
      )}

      <dl className="prediction__meta">
        {anchor && (
          <>
            <dt>Based on</dt>
            <dd>
              {PHASE_LABEL[anchor.phase]} observed {formatAge(anchor.ageSeconds)} ({anchor.source},{" "}
              {anchor.simulated ? "simulated" : "real"})
            </dd>
          </>
        )}
        <dt>Model</dt>
        <dd>{prediction.modelVersion ?? "–"}</dd>
      </dl>

      <p className="disclaimer" role="note">
        {prediction.disclaimer}
      </p>
    </article>
  );
}
