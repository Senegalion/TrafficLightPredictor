import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ModelInfo } from "../api/types";
import { formatPercent } from "../lib/format";
import { Badge } from "./Badge";

export function ModelInfoCard() {
  const [info, setInfo] = useState<ModelInfo | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    api
      .modelInfo()
      .then(setInfo)
      .catch(() => setUnavailable(true));
  }, []);

  return (
    <section className="card" aria-labelledby="model-heading">
      <h2 id="model-heading">Model</h2>
      {unavailable && <p className="muted">The ML service is not reachable right now.</p>}
      {info && (
        <dl className="kv">
          <dt>Version</dt>
          <dd>{info.model_version}</dd>
          <dt>Training data</dt>
          <dd>
            <Badge tone={info.training_data_origin === "REAL" ? "info" : "warning"}>{info.training_data_origin}</Badge>
          </dd>
          <dt>Shown only if</dt>
          <dd>
            confidence ≥ {formatPercent(info.reliability_policy.min_confidence)}, interval ≤{" "}
            {info.reliability_policy.max_interval_width_s} s, observation ≤{" "}
            {Math.round(info.reliability_policy.max_anchor_age_s / 60)} min old
          </dd>
        </dl>
      )}
    </section>
  );
}
