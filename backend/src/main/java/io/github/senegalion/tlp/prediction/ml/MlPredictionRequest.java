package io.github.senegalion.tlp.prediction.ml;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.github.senegalion.tlp.common.SignalPhase;
import java.time.Instant;

/** Request body of the ML service's {@code POST /v1/predictions}. */
public record MlPredictionRequest(
        @JsonProperty("signal_code") String signalCode,
        @JsonProperty("target_time") Instant targetTime,
        @JsonProperty("anchor") Anchor anchor) {

    public record Anchor(
            @JsonProperty("phase") SignalPhase phase,
            @JsonProperty("observed_at") Instant observedAt,
            @JsonProperty("phase_duration_s") Integer phaseDurationSeconds) {}
}
