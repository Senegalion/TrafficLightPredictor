package io.github.senegalion.tlp.intersection;

public record TrafficSignalResponse(
        Long id,
        String code,
        String name,
        String description,
        String approach,
        ConfigurationSource configurationSource) {

    static TrafficSignalResponse from(TrafficSignal signal) {
        return new TrafficSignalResponse(signal.getId(), signal.getCode(), signal.getName(),
                signal.getDescription(), signal.getApproach(), signal.getConfigurationSource());
    }
}
