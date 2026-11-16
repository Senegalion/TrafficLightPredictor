package io.github.senegalion.tlp.prediction;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.UUID;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/predictions")
@Tag(name = "Predictions", description = "Experimental signal phase predictions (estimates, not guarantees)")
public class PredictionController {

    private final PredictionService service;

    public PredictionController(PredictionService service) {
        this.service = service;
    }

    @PostMapping
    @Operation(summary = "Request a prediction for a signal",
            description = "Always returns 201 with a stored prediction. Check `status` and `displayable`: "
                    + "INSUFFICIENT_DATA, LOW_CONFIDENCE, UNSUPPORTED_SIGNAL and MODEL_UNAVAILABLE results "
                    + "must not be shown as an estimate.")
    public ResponseEntity<PredictionResponse> create(@Valid @RequestBody CreatePredictionRequest request) {
        PredictionResponse response = service.create(request);
        return ResponseEntity.created(URI.create("/api/v1/predictions/" + response.id())).body(response);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get a stored prediction")
    public PredictionResponse get(@PathVariable UUID id) {
        return service.get(id);
    }
}
