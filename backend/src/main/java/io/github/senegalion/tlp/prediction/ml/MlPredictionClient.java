package io.github.senegalion.tlp.prediction.ml;

import java.util.Map;

/** Port to the Python ML prediction service. */
public interface MlPredictionClient {

    /**
     * @throws MlServiceUnavailableException if the service cannot be reached or fails
     */
    MlPredictionResponse predict(MlPredictionRequest request);

    /**
     * @throws MlServiceUnavailableException if the service cannot be reached or has no model loaded
     */
    Map<String, Object> modelInfo();
}
