import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api/client";
import type { Intersection } from "./api/types";
import { IntersectionDetails } from "./components/IntersectionDetails";
import { IntersectionList } from "./components/IntersectionList";
import { IntersectionMap } from "./components/IntersectionMap";
import { ModelInfoCard } from "./components/ModelInfoCard";
import { ObservationHistory } from "./components/ObservationHistory";
import { PredictionPanel } from "./components/PredictionPanel";
import { SafetyNotice } from "./components/SafetyNotice";

const INTERSECTION_PARAM = "intersection";

export default function App() {
  const [intersections, setIntersections] = useState<Intersection[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [signalId, setSignalId] = useState<number | null>(null);
  const [historyKey, setHistoryKey] = useState(0);

  useEffect(() => {
    api
      .listIntersections()
      .then((loaded) => {
        setIntersections(loaded);
        // Deep link: ?intersection=LDZ-KOS-STR preselects an intersection.
        const code = new URLSearchParams(window.location.search).get(INTERSECTION_PARAM);
        const linked = loaded.find((intersection) => intersection.code === code);
        if (linked) {
          setSelectedId(linked.id);
          setSignalId(linked.signals[0]?.id ?? null);
        }
      })
      .catch((e: unknown) => setLoadError(e instanceof Error ? e.message : "Could not load intersections"));
  }, []);

  const selected = useMemo(
    () => intersections.find((intersection) => intersection.id === selectedId) ?? null,
    [intersections, selectedId],
  );

  const selectIntersection = useCallback(
    (id: number) => {
      setSelectedId(id);
      const intersection = intersections.find((i) => i.id === id);
      setSignalId(intersection?.signals[0]?.id ?? null);
      if (intersection) {
        const url = new URL(window.location.href);
        url.searchParams.set(INTERSECTION_PARAM, intersection.code);
        window.history.replaceState(null, "", url);
      }
    },
    [intersections],
  );

  const refreshHistory = useCallback(() => setHistoryKey((key) => key + 1), []);

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1>Traffic Light Predictor</h1>
          <p className="muted">Experimental traffic signal phase estimation · Łódź, Poland</p>
        </div>
      </header>

      <SafetyNotice />

      <main className="layout">
        <div className="layout__sidebar">
          <section className="card" aria-labelledby="intersections-heading">
            <h2 id="intersections-heading">Intersections</h2>
            {loadError && (
              <p className="error" role="alert">
                {loadError}
              </p>
            )}
            <IntersectionMap intersections={intersections} selectedId={selectedId} onSelect={selectIntersection} />
            <IntersectionList intersections={intersections} selectedId={selectedId} onSelect={selectIntersection} />
          </section>
          <ModelInfoCard />
          <section className="card" aria-labelledby="about-heading">
            <h2 id="about-heading">How it works</h2>
            <ol className="small">
              <li>Choose an intersection and a signal group.</li>
              <li>The backend finds the latest observation of that signal (at most 15 minutes old).</li>
              <li>
                A gradient-boosting model estimates the current phase and the seconds left in it, with a calibrated
                confidence and an ≈80% interval.
              </li>
              <li>If the estimate does not meet the reliability policy it is not shown.</li>
            </ol>
          </section>
        </div>

        <div className="layout__content">
          {selected && signalId != null ? (
            <>
              <IntersectionDetails
                intersection={selected}
                selectedSignalId={signalId}
                onSelectSignal={setSignalId}
              />
              <PredictionPanel intersectionId={selected.id} signalId={signalId} onPredicted={refreshHistory} />
              <ObservationHistory intersectionId={selected.id} signalId={signalId} refreshKey={historyKey} />
            </>
          ) : (
            <section className="card empty-state">
              <h2>Select an intersection</h2>
              <p className="muted">Pick an intersection on the map or from the list to request a prediction.</p>
            </section>
          )}
        </div>
      </main>

      <footer className="app__footer small muted">
        Intersection locations © OpenStreetMap contributors (ODbL). Signal groups and all observations in this demo are
        sample/simulated data. MIT licensed research prototype.
      </footer>
    </div>
  );
}
