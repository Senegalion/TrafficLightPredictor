package io.github.senegalion.tlp.intersection;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/intersections")
@Tag(name = "Intersections", description = "Signalised intersections and their signal groups")
public class IntersectionController {

    static final int MAX_RADIUS_METERS = 20_000;
    static final int MAX_NEARBY_RESULTS = 50;

    private final IntersectionService service;

    public IntersectionController(IntersectionService service) {
        this.service = service;
    }

    @GetMapping
    @Operation(summary = "List all intersections with their signal groups")
    public List<IntersectionResponse> list() {
        return service.list();
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get one intersection")
    public IntersectionResponse get(@PathVariable Long id) {
        return service.get(id);
    }

    @GetMapping("/nearby")
    @Operation(summary = "Find intersections near a location, nearest first")
    public List<NearbyIntersectionResponse> nearby(
            @RequestParam @DecimalMin("-90") @DecimalMax("90") double latitude,
            @RequestParam @DecimalMin("-180") @DecimalMax("180") double longitude,
            @Parameter(description = "Search radius in metres")
            @RequestParam(defaultValue = "1000") @Min(1) @Max(MAX_RADIUS_METERS) int radiusMeters,
            @RequestParam(defaultValue = "10") @Min(1) @Max(MAX_NEARBY_RESULTS) int limit) {
        return service.nearby(latitude, longitude, radiusMeters, limit);
    }
}
