export function SafetyNotice() {
  return (
    <aside className="safety" role="note" aria-label="Safety notice">
      <strong>Research prototype.</strong> Predictions are statistical estimates, not guarantees. This demo uses{" "}
      <strong>simulated</strong> observations and is <strong>not connected to any traffic signal controller</strong>.
      Never use it to decide whether to accelerate, brake or cross – always obey the actual signal and traffic rules.
    </aside>
  );
}
