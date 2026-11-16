package io.github.senegalion.tlp.prediction;

import io.github.senegalion.tlp.prediction.ml.MlPredictionClient;
import io.github.senegalion.tlp.prediction.ml.MlServiceUnavailableException;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Tag(name = "Model", description = "Information about the deployed prediction model")
public class ModelInfoController {

    private final MlPredictionClient mlClient;

    public ModelInfoController(MlPredictionClient mlClient) {
        this.mlClient = mlClient;
    }

    @GetMapping("/api/v1/model")
    @Operation(summary = "Model version, training data origin and reliability policy")
    public Map<String, Object> modelInfo() {
        return mlClient.modelInfo();
    }

    @ExceptionHandler(MlServiceUnavailableException.class)
    ProblemDetail handleUnavailable(MlServiceUnavailableException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.SERVICE_UNAVAILABLE, ex.getMessage());
        problem.setTitle("Model unavailable");
        return problem;
    }
}
