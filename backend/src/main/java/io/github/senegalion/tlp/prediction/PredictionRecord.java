package io.github.senegalion.tlp.prediction;

import io.github.senegalion.tlp.common.SignalPhase;
import io.github.senegalion.tlp.intersection.Intersection;
import io.github.senegalion.tlp.intersection.TrafficSignal;
import io.github.senegalion.tlp.observation.Observation;
import io.github.senegalion.tlp.prediction.ml.MlPredictionResponse;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** A stored prediction, kept for traceability and later evaluation against real observations. */
@Entity
@Table(name = "predictions")
public class PredictionRecord {

    private static final double MILLIS_PER_SECOND = 1000.0;

    @Id
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "intersection_id", nullable = false)
    private Intersection intersection;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "signal_id", nullable = false)
    private TrafficSignal signal;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "target_time", nullable = false)
    private Instant targetTime;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private PredictionStatus status;

    @Column(nullable = false)
    private boolean displayable;

    @Enumerated(EnumType.STRING)
    @Column(name = "predicted_phase", length = 8)
    private SignalPhase predictedPhase;

    private Double confidence;

    @Column(name = "probability_red")
    private Double probabilityRed;

    @Column(name = "probability_yellow")
    private Double probabilityYellow;

    @Column(name = "probability_green")
    private Double probabilityGreen;

    @Column(name = "remaining_seconds")
    private Double remainingSeconds;

    @Column(name = "remaining_seconds_lower")
    private Double remainingSecondsLower;

    @Column(name = "remaining_seconds_upper")
    private Double remainingSecondsUpper;

    @Column(name = "model_version", length = 64)
    private String modelVersion;

    @Column(name = "training_data_origin", length = 16)
    private String trainingDataOrigin;

    @Enumerated(EnumType.STRING)
    @Column(name = "data_origin", nullable = false, length = 16)
    private DataOrigin dataOrigin;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "anchor_observation_id")
    private Observation anchorObservation;

    @Column(name = "anchor_age_seconds")
    private Double anchorAgeSeconds;

    private String message;

    protected PredictionRecord() {
        // for JPA
    }

    public PredictionRecord(TrafficSignal signal, Instant createdAt, Instant targetTime, Observation anchor) {
        this.id = UUID.randomUUID();
        this.intersection = signal.getIntersection();
        this.signal = signal;
        this.createdAt = createdAt;
        this.targetTime = targetTime;
        this.anchorObservation = anchor;
        if (anchor == null) {
            this.dataOrigin = DataOrigin.NONE;
        } else {
            this.dataOrigin = anchor.isSimulated() ? DataOrigin.SIMULATED : DataOrigin.REAL;
            this.anchorAgeSeconds = Duration.between(anchor.getObservedAt(), targetTime).toMillis() / MILLIS_PER_SECOND;
        }
    }

    public void markInsufficientData(String reason) {
        this.status = PredictionStatus.INSUFFICIENT_DATA;
        this.displayable = false;
        this.message = reason;
    }

    public void markModelUnavailable(String reason) {
        this.status = PredictionStatus.MODEL_UNAVAILABLE;
        this.displayable = false;
        this.message = reason;
    }

    public void applyModelResult(MlPredictionResponse result) {
        this.status = parseStatus(result.status());
        this.displayable = result.displayable() && status == PredictionStatus.OK;
        this.predictedPhase = result.phase();
        this.confidence = result.confidence();
        Map<SignalPhase, Double> probabilities = result.phaseProbabilities();
        if (probabilities != null) {
            this.probabilityRed = probabilities.get(SignalPhase.RED);
            this.probabilityYellow = probabilities.get(SignalPhase.YELLOW);
            this.probabilityGreen = probabilities.get(SignalPhase.GREEN);
        }
        this.remainingSeconds = result.remainingSeconds();
        this.remainingSecondsLower = result.remainingSecondsLower();
        this.remainingSecondsUpper = result.remainingSecondsUpper();
        this.modelVersion = result.modelVersion();
        this.trainingDataOrigin = result.trainingDataOrigin();
        List<String> reasons = result.reasons();
        this.message = reasons == null || reasons.isEmpty() ? null : String.join(" ", reasons);
    }

    private static PredictionStatus parseStatus(String value) {
        try {
            return PredictionStatus.valueOf(value);
        } catch (IllegalArgumentException | NullPointerException ex) {
            throw new IllegalStateException("Unknown prediction status from ML service: " + value, ex);
        }
    }

    public UUID getId() {
        return id;
    }

    public Intersection getIntersection() {
        return intersection;
    }

    public TrafficSignal getSignal() {
        return signal;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getTargetTime() {
        return targetTime;
    }

    public PredictionStatus getStatus() {
        return status;
    }

    public boolean isDisplayable() {
        return displayable;
    }

    public SignalPhase getPredictedPhase() {
        return predictedPhase;
    }

    public Double getConfidence() {
        return confidence;
    }

    public Double getProbabilityRed() {
        return probabilityRed;
    }

    public Double getProbabilityYellow() {
        return probabilityYellow;
    }

    public Double getProbabilityGreen() {
        return probabilityGreen;
    }

    public Double getRemainingSeconds() {
        return remainingSeconds;
    }

    public Double getRemainingSecondsLower() {
        return remainingSecondsLower;
    }

    public Double getRemainingSecondsUpper() {
        return remainingSecondsUpper;
    }

    public String getModelVersion() {
        return modelVersion;
    }

    public String getTrainingDataOrigin() {
        return trainingDataOrigin;
    }

    public DataOrigin getDataOrigin() {
        return dataOrigin;
    }

    public Observation getAnchorObservation() {
        return anchorObservation;
    }

    public Double getAnchorAgeSeconds() {
        return anchorAgeSeconds;
    }

    public String getMessage() {
        return message;
    }
}
