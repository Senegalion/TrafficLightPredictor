package io.github.senegalion.tlp;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class TrafficLightPredictorApplication {

    public static void main(String[] args) {
        SpringApplication.run(TrafficLightPredictorApplication.class, args);
    }
}
