package io.github.senegalion.tlp.observation;

import io.github.senegalion.tlp.common.SignalPhase;
import java.time.Instant;

public record ObservationResponse(
        Long id,
        Long intersectionId,
        Long signalId,
        String signalCode,
        Instant observedAt,
        SignalPhase phase,
        Integer phaseDurationSeconds,
        TravelDirection direction,
        String source,
        boolean simulated) {

    public static ObservationResponse from(Observation observation) {
        return new ObservationResponse(observation.getId(), observation.getIntersection().getId(),
                observation.getSignal().getId(), observation.getSignal().getCode(), observation.getObservedAt(),
                observation.getPhase(), observation.getPhaseDurationSeconds(), observation.getDirection(),
                observation.getSource(), observation.isSimulated());
    }
}
