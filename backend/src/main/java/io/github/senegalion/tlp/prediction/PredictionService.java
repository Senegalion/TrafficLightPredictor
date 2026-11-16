package io.github.senegalion.tlp.prediction;

import io.github.senegalion.tlp.common.InvalidRequestException;
import io.github.senegalion.tlp.common.ResourceNotFoundException;
import io.github.senegalion.tlp.intersection.IntersectionService;
import io.github.senegalion.tlp.intersection.TrafficSignal;
import io.github.senegalion.tlp.observation.Observation;
import io.github.senegalion.tlp.observation.ObservationService;
import io.github.senegalion.tlp.prediction.ml.MlPredictionClient;
import io.github.senegalion.tlp.prediction.ml.MlPredictionRequest;
import io.github.senegalion.tlp.prediction.ml.MlPredictionResponse;
import io.github.senegalion.tlp.prediction.ml.MlServiceUnavailableException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Optional;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PredictionService {

    private static final Logger log = LoggerFactory.getLogger(PredictionService.class);

    private final IntersectionService intersections;
    private final ObservationService observations;
    private final PredictionRepository predictions;
    private final MlPredictionClient mlClient;
    private final PredictionProperties properties;
    private final Clock clock;

    public PredictionService(IntersectionService intersections, ObservationService observations,
                             PredictionRepository predictions, MlPredictionClient mlClient,
                             PredictionProperties properties, Clock clock) {
        this.intersections = intersections;
        this.observations = observations;
        this.predictions = predictions;
        this.mlClient = mlClient;
        this.properties = properties;
        this.clock = clock;
    }

    @Transactional
    public PredictionResponse create(CreatePredictionRequest request) {
        TrafficSignal signal = intersections.findSignal(request.intersectionId(), request.signalId());
        Instant now = clock.instant();
        Instant target = request.targetTime() == null ? now : request.targetTime();
        validateTarget(target, now);

        Optional<Observation> anchor = observations.latestAtOrBefore(signal.getId(), target);
        PredictionRecord record = new PredictionRecord(signal, now, target, anchor.orElse(null));

        if (anchor.isEmpty()) {
            record.markInsufficientData("No observation of this signal exists at or before the target time.");
        } else if (Duration.between(anchor.get().getObservedAt(), target).compareTo(properties.maxAnchorAge()) > 0) {
            record.markInsufficientData("The latest observation is older than %d minutes; no prediction is made."
                    .formatted(properties.maxAnchorAge().toMinutes()));
        } else {
            requestModelPrediction(record, signal, anchor.get(), target);
        }

        predictions.save(record);
        log.info("Prediction {} for signal {}: status={} displayable={}",
                record.getId(), signal.getCode(), record.getStatus(), record.isDisplayable());
        return PredictionResponse.from(record);
    }

    private void requestModelPrediction(PredictionRecord record, TrafficSignal signal, Observation anchor,
                                        Instant target) {
        MlPredictionRequest mlRequest = new MlPredictionRequest(signal.getCode(), target,
                new MlPredictionRequest.Anchor(anchor.getPhase(), anchor.getObservedAt(),
                        anchor.getPhaseDurationSeconds()));
        try {
            MlPredictionResponse result = mlClient.predict(mlRequest);
            record.applyModelResult(result);
        } catch (MlServiceUnavailableException ex) {
            record.markModelUnavailable("The prediction model is currently unavailable.");
        } catch (IllegalStateException ex) {
            log.error("Unexpected response from ML service", ex);
            record.markModelUnavailable("The prediction model returned an unexpected response.");
        }
    }

    private void validateTarget(Instant target, Instant now) {
        if (target.isAfter(now.plus(properties.maxFutureTarget()))) {
            throw new InvalidRequestException("targetTime may be at most %d seconds in the future"
                    .formatted(properties.maxFutureTarget().toSeconds()));
        }
        if (target.isBefore(now.minus(properties.maxPastTarget()))) {
            throw new InvalidRequestException("targetTime may be at most %d days in the past"
                    .formatted(properties.maxPastTarget().toDays()));
        }
    }

    @Transactional(readOnly = true)
    public PredictionResponse get(UUID id) {
        return predictions.findWithDetailsById(id)
                .map(PredictionResponse::from)
                .orElseThrow(() -> new ResourceNotFoundException("Prediction", id));
    }
}
