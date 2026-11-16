import type { Intersection } from "../api/types";

interface Props {
  intersections: Intersection[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export function IntersectionList({ intersections, selectedId, onSelect }: Props) {
  return (
    <ul className="intersection-list" aria-label="Intersections">
      {intersections.map((intersection) => (
        <li key={intersection.id}>
          <button
            type="button"
            className={`intersection-list__item${intersection.id === selectedId ? " is-selected" : ""}`}
            aria-pressed={intersection.id === selectedId}
            onClick={() => onSelect(intersection.id)}
          >
            <span className="intersection-list__name">{intersection.name}</span>
            <span className="intersection-list__meta">
              {intersection.city} · {intersection.signals.length} signal groups
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
