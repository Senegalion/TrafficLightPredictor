package io.github.senegalion.tlp.prediction.ml;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

@ConfigurationProperties("tlp.ml")
public record MlServiceProperties(
        @DefaultValue("http://localhost:8000") String baseUrl,
        @DefaultValue("PT2S") Duration connectTimeout,
        @DefaultValue("PT5S") Duration readTimeout) {}
