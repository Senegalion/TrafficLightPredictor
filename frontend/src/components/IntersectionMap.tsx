import "leaflet/dist/leaflet.css";
import { CircleMarker, MapContainer, TileLayer, Tooltip } from "react-leaflet";
import type { Intersection } from "../api/types";

const LODZ_CENTER: [number, number] = [51.7592, 19.456];
const DEFAULT_ZOOM = 12;
const MARKER_RADIUS = 9;

interface Props {
  intersections: Intersection[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export function IntersectionMap({ intersections, selectedId, onSelect }: Props) {
  return (
    <MapContainer center={LODZ_CENTER} zoom={DEFAULT_ZOOM} className="map" scrollWheelZoom={false}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {intersections.map((intersection) => {
        const selected = intersection.id === selectedId;
        return (
          <CircleMarker
            key={intersection.id}
            center={[intersection.latitude, intersection.longitude]}
            radius={MARKER_RADIUS}
            pathOptions={{
              color: selected ? "#0b5cad" : "#333",
              fillColor: selected ? "#2f81f7" : "#f5a524",
              fillOpacity: 0.9,
              weight: selected ? 3 : 1,
            }}
            eventHandlers={{ click: () => onSelect(intersection.id) }}
          >
            <Tooltip>{intersection.name}</Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
