package io.github.senegalion.tlp.prediction.ml;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import io.github.senegalion.tlp.common.SignalPhase;
import java.time.Instant;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

class HttpMlPredictionClientTest {

    private static final Instant NOW = Instant.parse("2026-10-05T10:00:00Z");

    private MockRestServiceServer server;
    private HttpMlPredictionClient client;

    @BeforeEach
    void setUp() {
        RestClient.Builder builder = RestClient.builder().baseUrl("http://ml");
        server = MockRestServiceServer.bindTo(builder).build();
        client = new HttpMlPredictionClient(builder.build());
    }

    @Test
    void sendsSnakeCaseRequestAndParsesResponse() {
        server.expect(requestTo("http://ml/v1/predictions"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(content().json("""
                        {"signal_code": "LDZ-KOS-STR-S1", "target_time": "2026-10-05T10:00:00Z",
                         "anchor": {"phase": "RED", "observed_at": "2026-10-05T09:59:30Z", "phase_duration_s": null}}
                        """))
                .andRespond(withSuccess("""
                        {"status": "OK", "displayable": true, "model_version": "tlp-gbm-x",
                         "training_data_origin": "SYNTHETIC", "reasons": [], "phase": "RED", "confidence": 0.9,
                         "phase_probabilities": {"RED": 0.9, "YELLOW": 0.02, "GREEN": 0.08},
                         "remaining_s": 10.5, "remaining_lower_s": 6.0, "remaining_upper_s": 14.0,
                         "baseline_phase": "RED", "baseline_remaining_s": 11.0, "anchor_age_s": 30.0}
                        """, MediaType.APPLICATION_JSON));

        MlPredictionResponse response = client.predict(new MlPredictionRequest("LDZ-KOS-STR-S1", NOW,
                new MlPredictionRequest.Anchor(SignalPhase.RED, NOW.minusSeconds(30), null)));

        assertThat(response.status()).isEqualTo("OK");
        assertThat(response.phase()).isEqualTo(SignalPhase.RED);
        assertThat(response.phaseProbabilities()).containsEntry(SignalPhase.GREEN, 0.08);
        assertThat(response.remainingSecondsUpper()).isEqualTo(14.0);
        server.verify();
    }

    @Test
    void serverErrorBecomesUnavailableException() {
        server.expect(requestTo("http://ml/v1/predictions")).andRespond(withServerError());

        assertThatThrownBy(() -> client.predict(new MlPredictionRequest("S", NOW, null)))
                .isInstanceOf(MlServiceUnavailableException.class);
    }

    @Test
    void unreachableServiceBecomesUnavailableException() {
        HttpMlPredictionClient unreachable = new HttpMlPredictionClient(
                RestClient.builder().baseUrl("http://127.0.0.1:1").build());

        assertThatThrownBy(unreachable::modelInfo).isInstanceOf(MlServiceUnavailableException.class);
    }
}
