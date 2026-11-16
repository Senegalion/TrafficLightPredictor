import type { SignalPhase } from "../api/types";
import { PHASE_LABEL } from "../lib/format";

interface Props {
  phase: SignalPhase | null;
  /** True when the phase is a model output that is not reliable enough to display as a fact. */
  uncertain?: boolean;
}

const LAMPS: SignalPhase[] = ["RED", "YELLOW", "GREEN"];

export function TrafficLight({ phase, uncertain = false }: Props) {
  const label =
    phase == null
      ? "No phase estimate"
      : `${uncertain ? "Uncertain estimate" : "Estimated phase"}: ${PHASE_LABEL[phase]}`;
  return (
    <div className={`traffic-light${uncertain ? " traffic-light--uncertain" : ""}`} role="img" aria-label={label}>
      {LAMPS.map((lamp) => (
        <span
          key={lamp}
          data-testid={`lamp-${lamp}`}
          data-lit={lamp === phase}
          className={`lamp lamp--${lamp.toLowerCase()}${lamp === phase ? " lamp--lit" : ""}`}
        />
      ))}
    </div>
  );
}
