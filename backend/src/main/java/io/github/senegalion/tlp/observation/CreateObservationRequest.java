package io.github.senegalion.tlp.observation;

import io.github.senegalion.tlp.common.SignalPhase;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.Instant;

public record CreateObservationRequest(
        @NotNull Long signalId,
        @Schema(description = "When the signal was observed switching to the phase (ISO-8601)")
        @NotNull Instant observedAt,
        @NotNull SignalPhase phase,
        @Schema(description = "How long the phase lasted, if the observer saw it end")
        @Min(MIN_PHASE_DURATION_SECONDS) @Max(MAX_PHASE_DURATION_SECONDS) Integer phaseDurationSeconds,
        TravelDirection direction,
        @Schema(example = "manual-observation") @NotBlank @Size(max = 64) String source,
        @Schema(description = "Must be true for simulated/synthetic records. Required so that every record is labelled.")
        @NotNull Boolean simulated) {

    public static final int MIN_PHASE_DURATION_SECONDS = 1;
    /** Longer phases are treated as recording errors; matches the database constraint. */
    public static final int MAX_PHASE_DURATION_SECONDS = 300;
}
