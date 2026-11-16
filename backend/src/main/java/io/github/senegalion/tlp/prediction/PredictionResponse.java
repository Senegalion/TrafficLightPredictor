package io.github.senegalion.tlp.prediction;

import io.github.senegalion.tlp.common.SignalPhase;
import io.github.senegalion.tlp.observation.Observation;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.Instant;
import java.util.EnumMap;
import java.util.Map;
import java.util.UUID;

public record PredictionResponse(
        UUID id,
        Long intersectionId,
        String intersectionName,
        Long signalId,
        String signalCode,
        PredictionStatus status,
        @Schema(description = "True only if the prediction meets the reliability policy and may be shown to users")
        boolean displayable,
        SignalPhase predictedPhase,
        @Schema(description = "Calibrated probability of the predicted phase on held-out data. "
                + "It is calibrated on the model's training distribution (synthetic data in the demo), "
                + "not on real-world signals.")
        Double confidence,
        Map<SignalPhase, Double> phaseProbabilities,
        @Schema(description = "Estimated seconds until the predicted phase ends (median estimate)")
        Double remainingSeconds,
        @Schema(description = "Lower bound of the ~80% interval for the remaining time")
        Double remainingSecondsLower,
        @Schema(description = "Upper bound of the ~80% interval for the remaining time")
        Double remainingSecondsUpper,
        Instant targetTime,
        Instant createdAt,
        String modelVersion,
        @Schema(description = "SYNTHETIC, REAL or MIXED: what the model was trained on")
        String trainingDataOrigin,
        @Schema(description = "Origin of the observation used as input")
        DataOrigin dataOrigin,
        AnchorObservation anchorObservation,
        String message,
        String disclaimer) {

    public record AnchorObservation(Long id, SignalPhase phase, Instant observedAt, Integer phaseDurationSeconds,
                                    Double ageSeconds, String source, boolean simulated) {}

    static PredictionResponse from(PredictionRecord record) {
        Observation anchor = record.getAnchorObservation();
        AnchorObservation anchorResponse = anchor == null ? null : new AnchorObservation(anchor.getId(),
                anchor.getPhase(), anchor.getObservedAt(), anchor.getPhaseDurationSeconds(),
                record.getAnchorAgeSeconds(), anchor.getSource(), anchor.isSimulated());
        return new PredictionResponse(record.getId(), record.getIntersection().getId(),
                record.getIntersection().getName(), record.getSignal().getId(), record.getSignal().getCode(),
                record.getStatus(), record.isDisplayable(), record.getPredictedPhase(), record.getConfidence(),
                probabilities(record), record.getRemainingSeconds(), record.getRemainingSecondsLower(),
                record.getRemainingSecondsUpper(), record.getTargetTime(), record.getCreatedAt(),
                record.getModelVersion(), record.getTrainingDataOrigin(), record.getDataOrigin(), anchorResponse,
                record.getMessage(), disclaimer(record));
    }

    private static Map<SignalPhase, Double> probabilities(PredictionRecord record) {
        if (record.getProbabilityRed() == null) {
            return null;
        }
        Map<SignalPhase, Double> map = new EnumMap<>(SignalPhase.class);
        map.put(SignalPhase.RED, record.getProbabilityRed());
        map.put(SignalPhase.YELLOW, record.getProbabilityYellow());
        map.put(SignalPhase.GREEN, record.getProbabilityGreen());
        return map;
    }

    static String disclaimer(PredictionRecord record) {
        StringBuilder text = new StringBuilder("Experimental estimate, not a guarantee. "
                + "Not connected to any traffic signal controller. Always obey the actual traffic signal.");
        if (record.getDataOrigin() == DataOrigin.SIMULATED) {
            text.append(" Input observation is SIMULATED.");
        }
        if (record.getTrainingDataOrigin() != null && !"REAL".equals(record.getTrainingDataOrigin())) {
            text.append(" Model trained on ").append(record.getTrainingDataOrigin()).append(" data.");
        }
        return text.toString();
    }
}
