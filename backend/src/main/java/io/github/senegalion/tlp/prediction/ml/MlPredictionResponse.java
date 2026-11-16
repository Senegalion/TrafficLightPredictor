package io.github.senegalion.tlp.prediction.ml;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.github.senegalion.tlp.common.SignalPhase;
import java.util.List;
import java.util.Map;

/** Response body of the ML service's {@code POST /v1/predictions}. */
@JsonIgnoreProperties(ignoreUnknown = true)
public record MlPredictionResponse(
        @JsonProperty("status") String status,
        @JsonProperty("displayable") boolean displayable,
        @JsonProperty("model_version") String modelVersion,
        @JsonProperty("training_data_origin") String trainingDataOrigin,
        @JsonProperty("reasons") List<String> reasons,
        @JsonProperty("phase") SignalPhase phase,
        @JsonProperty("confidence") Double confidence,
        @JsonProperty("phase_probabilities") Map<SignalPhase, Double> phaseProbabilities,
        @JsonProperty("remaining_s") Double remainingSeconds,
        @JsonProperty("remaining_lower_s") Double remainingSecondsLower,
        @JsonProperty("remaining_upper_s") Double remainingSecondsUpper,
        @JsonProperty("anchor_age_s") Double anchorAgeSeconds) {}
