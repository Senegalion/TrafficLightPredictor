package io.github.senegalion.tlp.intersection;

import java.util.List;

public record IntersectionResponse(
        Long id,
        String code,
        String name,
        String city,
        String description,
        double latitude,
        double longitude,
        LocationSource locationSource,
        String osmReference,
        List<TrafficSignalResponse> signals) {

    static IntersectionResponse from(Intersection intersection) {
        return new IntersectionResponse(intersection.getId(), intersection.getCode(), intersection.getName(),
                intersection.getCity(), intersection.getDescription(), intersection.getLatitude(),
                intersection.getLongitude(), intersection.getLocationSource(), intersection.getOsmReference(),
                intersection.getSignals().stream().map(TrafficSignalResponse::from).toList());
    }
}
