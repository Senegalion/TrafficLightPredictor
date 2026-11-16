import type { Intersection } from "../api/types";
import { Badge } from "./Badge";

interface Props {
  intersection: Intersection;
  selectedSignalId: number | null;
  onSelectSignal: (id: number) => void;
}

export function IntersectionDetails({ intersection, selectedSignalId, onSelectSignal }: Props) {
  return (
    <section className="card" aria-labelledby="intersection-heading">
      <div className="card__header">
        <h2 id="intersection-heading">{intersection.name}</h2>
        <Badge tone="info" title={intersection.osmReference ?? undefined}>
          {intersection.locationSource === "OPENSTREETMAP" ? "Location from OpenStreetMap" : "Sample location"}
        </Badge>
      </div>
      {intersection.description && <p className="muted">{intersection.description}</p>}
      <p className="small muted">
        {intersection.latitude.toFixed(5)}, {intersection.longitude.toFixed(5)} · {intersection.code}
      </p>

      <fieldset className="signal-picker">
        <legend>Signal group</legend>
        {intersection.signals.map((signal) => (
          <label key={signal.id} className={`signal-option${signal.id === selectedSignalId ? " is-selected" : ""}`}>
            <input
              type="radio"
              name="signal"
              value={signal.id}
              checked={signal.id === selectedSignalId}
              onChange={() => onSelectSignal(signal.id)}
            />
            <span>
              <strong>{signal.approach ?? signal.name}</strong>
              <span className="small muted"> · {signal.code}</span>
            </span>
            {signal.configurationSource === "SAMPLE" && (
              <Badge tone="warning" title="Invented for the demo, not verified on site">
                Sample configuration
              </Badge>
            )}
          </label>
        ))}
      </fieldset>
    </section>
  );
}
