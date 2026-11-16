package io.github.senegalion.tlp.intersection;

import io.github.senegalion.tlp.common.ResourceNotFoundException;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class IntersectionService {

    private final IntersectionRepository intersections;
    private final TrafficSignalRepository signals;

    public IntersectionService(IntersectionRepository intersections, TrafficSignalRepository signals) {
        this.intersections = intersections;
        this.signals = signals;
    }

    public List<IntersectionResponse> list() {
        return intersections.findAllWithSignals().stream().map(IntersectionResponse::from).toList();
    }

    public IntersectionResponse get(Long id) {
        return IntersectionResponse.from(findIntersection(id));
    }

    public List<NearbyIntersectionResponse> nearby(double latitude, double longitude, double radiusMeters,
                                                   int maxResults) {
        List<IntersectionRepository.NearbyIntersectionRow> rows =
                intersections.findNearby(latitude, longitude, radiusMeters, maxResults);
        Map<Long, Intersection> byId = intersections.findAllById(
                        rows.stream().map(IntersectionRepository.NearbyIntersectionRow::getId).toList())
                .stream()
                .collect(Collectors.toMap(Intersection::getId, Function.identity()));
        return rows.stream()
                .map(row -> new NearbyIntersectionResponse(
                        row.getDistanceMeters(), IntersectionResponse.from(byId.get(row.getId()))))
                .toList();
    }

    public Intersection findIntersection(Long id) {
        return intersections.findWithSignalsById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Intersection", id));
    }

    /** Returns the signal if it exists and belongs to the intersection, otherwise throws 404. */
    public TrafficSignal findSignal(Long intersectionId, Long signalId) {
        findIntersection(intersectionId);
        return signals.findById(signalId)
                .filter(signal -> signal.belongsTo(intersectionId))
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Traffic signal", signalId + " at intersection " + intersectionId));
    }
}
