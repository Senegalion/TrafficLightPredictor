package io.github.senegalion.tlp.prediction;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * @param maxAnchorAge oldest observation the system will extrapolate from; keep in sync with the ML
 *                     service's reliability policy ({@code max_anchor_age_s})
 * @param maxFutureTarget how far ahead of "now" a prediction may be requested
 * @param maxPastTarget how far back a (retrospective) prediction may be requested
 */
@ConfigurationProperties("tlp.predictions")
public record PredictionProperties(
        @DefaultValue("PT15M") Duration maxAnchorAge,
        @DefaultValue("PT2M") Duration maxFutureTarget,
        @DefaultValue("P7D") Duration maxPastTarget) {}
