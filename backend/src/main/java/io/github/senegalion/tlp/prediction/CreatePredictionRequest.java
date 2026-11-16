package io.github.senegalion.tlp.prediction;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import java.time.Instant;

public record CreatePredictionRequest(
        @NotNull Long intersectionId,
        @NotNull Long signalId,
        @Schema(description = "Time to predict for (ISO-8601). Defaults to now.")
        Instant targetTime) {}
