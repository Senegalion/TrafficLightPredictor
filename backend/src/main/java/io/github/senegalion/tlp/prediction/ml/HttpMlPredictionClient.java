package io.github.senegalion.tlp.prediction.ml;

import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

public class HttpMlPredictionClient implements MlPredictionClient {

    private static final Logger log = LoggerFactory.getLogger(HttpMlPredictionClient.class);

    private final RestClient restClient;

    public HttpMlPredictionClient(RestClient restClient) {
        this.restClient = restClient;
    }

    @Override
    public MlPredictionResponse predict(MlPredictionRequest request) {
        try {
            MlPredictionResponse response = restClient.post()
                    .uri("/v1/predictions")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(MlPredictionResponse.class);
            if (response == null) {
                throw new MlServiceUnavailableException("ML service returned an empty response", null);
            }
            return response;
        } catch (RestClientException ex) {
            log.warn("ML prediction request failed: {}", ex.getMessage());
            throw new MlServiceUnavailableException("ML service is unavailable", ex);
        }
    }

    @Override
    public Map<String, Object> modelInfo() {
        try {
            return restClient.get()
                    .uri("/v1/model")
                    .retrieve()
                    .body(new ParameterizedTypeReference<>() {});
        } catch (RestClientException ex) {
            throw new MlServiceUnavailableException("ML service is unavailable", ex);
        }
    }
}
