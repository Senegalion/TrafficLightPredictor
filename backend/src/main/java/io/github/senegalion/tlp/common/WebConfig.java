package io.github.senegalion.tlp.common;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration(proxyBeanMethods = false)
@EnableConfigurationProperties(WebProperties.class)
class WebConfig implements WebMvcConfigurer {

    private static final Logger log = LoggerFactory.getLogger(WebConfig.class);
    static final String OBSERVATION_WRITE_PATH = "/api/v1/intersections/*/observations";

    private final WebProperties properties;

    WebConfig(WebProperties properties) {
        this.properties = properties;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        String apiKey = properties.ingestionApiKey();
        if (apiKey == null || apiKey.isBlank()) {
            log.warn("tlp.web.ingestion-api-key is not set: observation ingestion is open to anyone");
            return;
        }
        registry.addInterceptor(new ApiKeyInterceptor(apiKey)).addPathPatterns(OBSERVATION_WRITE_PATH);
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins(properties.corsAllowedOrigins().toArray(String[]::new))
                .allowedMethods("GET", "POST")
                .allowedHeaders("Content-Type", ApiKeyInterceptor.HEADER);
    }
}
