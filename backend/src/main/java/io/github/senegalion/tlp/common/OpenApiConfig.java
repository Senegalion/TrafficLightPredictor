package io.github.senegalion.tlp.common;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
class OpenApiConfig {

    @Bean
    OpenAPI trafficLightPredictorOpenApi() {
        return new OpenAPI().info(new Info()
                .title("Traffic Light Predictor API")
                .version("v1")
                .description("""
                        Experimental research prototype. Predictions are statistical estimates, not \
                        guarantees, and are not connected to any traffic signal controller. The demo \
                        runs on SIMULATED observations; always obey the actual traffic signals.""")
                .license(new License().name("MIT")));
    }
}
