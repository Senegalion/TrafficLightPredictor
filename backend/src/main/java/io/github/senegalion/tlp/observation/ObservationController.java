package io.github.senegalion.tlp.observation;

import io.github.senegalion.tlp.common.PageResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.net.URI;
import java.time.Instant;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/intersections/{intersectionId}/observations")
@Tag(name = "Observations", description = "Historical signal phase observations (real or simulated)")
public class ObservationController {

    static final int MAX_PAGE_SIZE = 200;

    private final ObservationService service;

    public ObservationController(ObservationService service) {
        this.service = service;
    }

    @GetMapping
    @Operation(summary = "List observations of an intersection, newest first")
    public PageResponse<ObservationResponse> list(
            @PathVariable Long intersectionId,
            @RequestParam(required = false) Long signalId,
            @Parameter(description = "Inclusive lower bound (ISO-8601)")
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant from,
            @Parameter(description = "Inclusive upper bound (ISO-8601)")
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant to,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "50") @Min(1) @Max(MAX_PAGE_SIZE) int size) {
        PageRequest pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "observedAt"));
        return service.list(intersectionId, signalId, from, to, pageable);
    }

    @GetMapping("/{observationId}")
    @Operation(summary = "Get one observation")
    public ObservationResponse get(@PathVariable Long intersectionId, @PathVariable Long observationId) {
        return service.get(intersectionId, observationId);
    }

    @PostMapping
    @Operation(summary = "Submit an observation",
            description = "Requires the X-Api-Key header when an ingestion key is configured.")
    public ResponseEntity<ObservationResponse> create(@PathVariable Long intersectionId,
                                                      @Valid @RequestBody CreateObservationRequest request) {
        ObservationResponse created = service.create(intersectionId, request);
        URI location = URI.create("/api/v1/intersections/%d/observations/%d"
                .formatted(intersectionId, created.id()));
        return ResponseEntity.created(location).body(created);
    }
}
