import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Observation } from "../api/types";
import { formatSeconds, formatTime, PHASE_LABEL } from "../lib/format";
import { Badge } from "./Badge";

const HISTORY_SIZE = 15;

interface Props {
  intersectionId: number;
  signalId: number;
  /** Changing this value triggers a reload. */
  refreshKey: number;
}

export function ObservationHistory({ intersectionId, signalId, refreshKey }: Props) {
  const [observations, setObservations] = useState<Observation[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .listObservations(intersectionId, signalId, HISTORY_SIZE)
      .then((page) => {
        if (cancelled) return;
        setObservations(page.content);
        setTotal(page.totalElements);
        setError(null);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not load observations");
      });
    return () => {
      cancelled = true;
    };
  }, [intersectionId, signalId, refreshKey]);

  return (
    <section className="card" aria-labelledby="history-heading">
      <div className="card__header">
        <h2 id="history-heading">Recent observations</h2>
        <span className="small muted">{total} stored for this signal group</span>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {observations && observations.length === 0 && <p className="muted">No observations yet.</p>}
      {observations && observations.length > 0 && (
        <div className="table-scroll">
          <table className="history">
            <thead>
              <tr>
                <th scope="col">Phase started</th>
                <th scope="col">Phase</th>
                <th scope="col">Duration</th>
                <th scope="col">Source</th>
                <th scope="col">Data</th>
              </tr>
            </thead>
            <tbody>
              {observations.map((o) => (
                <tr key={o.id}>
                  <td>{formatTime(o.observedAt)}</td>
                  <td>
                    <span className={`phase-chip phase-chip--${o.phase.toLowerCase()}`}>{PHASE_LABEL[o.phase]}</span>
                  </td>
                  <td>{o.phaseDurationSeconds == null ? "unknown" : formatSeconds(o.phaseDurationSeconds)}</td>
                  <td className="small">{o.source}</td>
                  <td>
                    {o.simulated ? <Badge tone="warning">Simulated</Badge> : <Badge tone="info">Real</Badge>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
