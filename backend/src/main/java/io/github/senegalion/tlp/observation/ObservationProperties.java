package io.github.senegalion.tlp.observation;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * @param maxClockSkew how far in the future an observation timestamp may be (client clock drift)
 */
@ConfigurationProperties("tlp.observations")
public record ObservationProperties(@DefaultValue("PT1M") Duration maxClockSkew) {}
