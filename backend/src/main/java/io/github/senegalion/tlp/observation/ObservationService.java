package io.github.senegalion.tlp.observation;

import io.github.senegalion.tlp.common.ConflictException;
import io.github.senegalion.tlp.common.InvalidRequestException;
import io.github.senegalion.tlp.common.PageResponse;
import io.github.senegalion.tlp.common.ResourceNotFoundException;
import io.github.senegalion.tlp.intersection.IntersectionService;
import io.github.senegalion.tlp.intersection.TrafficSignal;
import java.time.Clock;
import java.time.Instant;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class ObservationService {

    /** Defaults for open-ended time filters. */
    static final Instant EARLIEST = Instant.parse("2000-01-01T00:00:00Z");
    static final Instant LATEST = Instant.parse("2100-01-01T00:00:00Z");

    private final ObservationRepository observations;
    private final IntersectionService intersections;
    private final ObservationProperties properties;
    private final Clock clock;

    public ObservationService(ObservationRepository observations, IntersectionService intersections,
                              ObservationProperties properties, Clock clock) {
        this.observations = observations;
        this.intersections = intersections;
        this.properties = properties;
        this.clock = clock;
    }

    @Transactional
    public ObservationResponse create(Long intersectionId, CreateObservationRequest request) {
        TrafficSignal signal = intersections.findSignal(intersectionId, request.signalId());
        Instant latestAllowed = clock.instant().plus(properties.maxClockSkew());
        if (request.observedAt().isAfter(latestAllowed)) {
            throw new InvalidRequestException("observedAt must not be in the future");
        }
        if (observations.existsBySignalIdAndObservedAt(signal.getId(), request.observedAt())) {
            throw new ConflictException("An observation of this signal at %s already exists"
                    .formatted(request.observedAt()));
        }
        Observation saved = observations.save(new Observation(signal, request.observedAt(), request.phase(),
                request.phaseDurationSeconds(), request.direction(), request.source().strip(),
                request.simulated()));
        return ObservationResponse.from(saved);
    }

    public PageResponse<ObservationResponse> list(Long intersectionId, Long signalId, Instant from, Instant to,
                                                  Pageable pageable) {
        intersections.findIntersection(intersectionId);
        Instant start = from == null ? EARLIEST : from;
        Instant end = to == null ? LATEST : to;
        if (start.isAfter(end)) {
            throw new InvalidRequestException("'from' must not be after 'to'");
        }
        Page<Observation> page = signalId == null
                ? observations.findByIntersectionIdAndObservedAtBetween(intersectionId, start, end, pageable)
                : observations.findByIntersectionIdAndSignalIdAndObservedAtBetween(
                        intersectionId, signalId, start, end, pageable);
        return PageResponse.of(page, ObservationResponse::from);
    }

    public ObservationResponse get(Long intersectionId, Long observationId) {
        return observations.findById(observationId)
                .filter(observation -> observation.getIntersection().getId().equals(intersectionId))
                .map(ObservationResponse::from)
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Observation", observationId + " at intersection " + intersectionId));
    }

    public Optional<Observation> latestAtOrBefore(Long signalId, Instant time) {
        return observations.findFirstBySignalIdAndObservedAtLessThanEqualOrderByObservedAtDesc(signalId, time);
    }
}
