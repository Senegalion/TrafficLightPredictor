package io.github.senegalion.tlp.observation;

import io.github.senegalion.tlp.common.SignalPhase;
import io.github.senegalion.tlp.intersection.Intersection;
import io.github.senegalion.tlp.intersection.TrafficSignal;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.Instant;

/**
 * "Signal {@code signal} was observed switching to {@code phase} at {@code observedAt}".
 * {@code phaseDurationSeconds} is known only if the observer also saw the phase end.
 */
@Entity
@Table(name = "observations")
public class Observation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "intersection_id", nullable = false)
    private Intersection intersection;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "signal_id", nullable = false)
    private TrafficSignal signal;

    @Column(name = "observed_at", nullable = false)
    private Instant observedAt;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 8)
    private SignalPhase phase;

    @Column(name = "phase_duration_seconds")
    private Integer phaseDurationSeconds;

    @Enumerated(EnumType.STRING)
    @Column(length = 16)
    private TravelDirection direction;

    @Column(nullable = false, length = 64)
    private String source;

    @Column(nullable = false)
    private boolean simulated;

    @Column(name = "created_at", nullable = false, insertable = false, updatable = false)
    private Instant createdAt;

    protected Observation() {
        // for JPA
    }

    public Observation(TrafficSignal signal, Instant observedAt, SignalPhase phase, Integer phaseDurationSeconds,
                       TravelDirection direction, String source, boolean simulated) {
        this.intersection = signal.getIntersection();
        this.signal = signal;
        this.observedAt = observedAt;
        this.phase = phase;
        this.phaseDurationSeconds = phaseDurationSeconds;
        this.direction = direction;
        this.source = source;
        this.simulated = simulated;
    }

    public Long getId() {
        return id;
    }

    public Intersection getIntersection() {
        return intersection;
    }

    public TrafficSignal getSignal() {
        return signal;
    }

    public Instant getObservedAt() {
        return observedAt;
    }

    public SignalPhase getPhase() {
        return phase;
    }

    public Integer getPhaseDurationSeconds() {
        return phaseDurationSeconds;
    }

    public TravelDirection getDirection() {
        return direction;
    }

    public String getSource() {
        return source;
    }

    public boolean isSimulated() {
        return simulated;
    }
}
