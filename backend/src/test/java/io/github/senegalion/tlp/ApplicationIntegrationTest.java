package io.github.senegalion.tlp;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.jayway.jsonpath.JsonPath;
import io.github.senegalion.tlp.common.SignalPhase;
import io.github.senegalion.tlp.prediction.ml.MlPredictionClient;
import io.github.senegalion.tlp.prediction.ml.MlPredictionResponse;
import io.github.senegalion.tlp.prediction.ml.MlServiceUnavailableException;
import io.github.senegalion.tlp.support.PostgisTestcontainersConfig;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

/** Full application against PostGIS (Testcontainers); only the Python ML service is mocked. */
@SpringBootTest
@AutoConfigureMockMvc
@Import(PostgisTestcontainersConfig.class)
class ApplicationIntegrationTest {

    @Autowired
    private MockMvc mvc;

    @MockitoBean
    private MlPredictionClient mlClient;

    private long[] firstIntersectionAndSignal(int signalIndex) throws Exception {
        String body = mvc.perform(get("/api/v1/intersections")).andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        long intersectionId = ((Number) JsonPath.read(body, "$[0].id")).longValue();
        long signalId = ((Number) JsonPath.read(body, "$[0].signals[" + signalIndex + "].id")).longValue();
        return new long[] {intersectionId, signalId};
    }

    private String postObservation(long intersectionId, long signalId, Instant observedAt) throws Exception {
        return mvc.perform(post("/api/v1/intersections/{id}/observations", intersectionId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"signalId": %d, "observedAt": "%s", "phase": "GREEN",
                                 "source": "integration-test", "simulated": true}
                                """.formatted(signalId, observedAt)))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
    }

    private String requestPrediction(long intersectionId, long signalId) throws Exception {
        return mvc.perform(post("/api/v1/predictions").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"intersectionId\": %d, \"signalId\": %d}".formatted(intersectionId, signalId)))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
    }

    @Test
    void observationToPredictionRoundTrip() throws Exception {
        long[] ids = firstIntersectionAndSignal(0);
        when(mlClient.predict(any())).thenReturn(new MlPredictionResponse("OK", true, "tlp-gbm-it", "SYNTHETIC",
                List.of(), SignalPhase.GREEN, 0.93,
                Map.of(SignalPhase.RED, 0.03, SignalPhase.YELLOW, 0.04, SignalPhase.GREEN, 0.93),
                21.0, 17.0, 25.0, 15.0));

        String observation = postObservation(ids[0], ids[1], Instant.now().minusSeconds(15).truncatedTo(ChronoUnit.SECONDS));
        long observationId = ((Number) JsonPath.read(observation, "$.id")).longValue();

        String prediction = requestPrediction(ids[0], ids[1]);
        assertThat((String) JsonPath.read(prediction, "$.status")).isEqualTo("OK");
        assertThat((String) JsonPath.read(prediction, "$.dataOrigin")).isEqualTo("SIMULATED");
        assertThat(((Number) JsonPath.read(prediction, "$.anchorObservation.id")).longValue()).isEqualTo(observationId);
        String id = JsonPath.read(prediction, "$.id");

        mvc.perform(get("/api/v1/predictions/{id}", id))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.predictedPhase").value("GREEN"))
                .andExpect(jsonPath("$.phaseProbabilities.GREEN").value(0.93))
                .andExpect(jsonPath("$.modelVersion").value("tlp-gbm-it"));

        mvc.perform(get("/api/v1/intersections/{id}/observations", ids[0]).param("signalId", String.valueOf(ids[1])))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[0].id").value(observationId))
                .andExpect(jsonPath("$.content[0].simulated").value(true));
    }

    @Test
    void signalWithoutObservationsHasInsufficientData() throws Exception {
        long[] ids = firstIntersectionAndSignal(1);

        String prediction = requestPrediction(ids[0], ids[1]);

        assertThat((String) JsonPath.read(prediction, "$.status")).isEqualTo("INSUFFICIENT_DATA");
        assertThat((Boolean) JsonPath.read(prediction, "$.displayable")).isFalse();
    }

    @Test
    void modelOutageIsReportedNotThrown() throws Exception {
        String body = mvc.perform(get("/api/v1/intersections")).andReturn().getResponse().getContentAsString();
        long intersectionId = ((Number) JsonPath.read(body, "$[1].id")).longValue();
        long signalId = ((Number) JsonPath.read(body, "$[1].signals[0].id")).longValue();
        when(mlClient.predict(any())).thenThrow(new MlServiceUnavailableException("down", null));
        postObservation(intersectionId, signalId, Instant.now().minusSeconds(5).truncatedTo(ChronoUnit.SECONDS));

        String prediction = requestPrediction(intersectionId, signalId);

        assertThat((String) JsonPath.read(prediction, "$.status")).isEqualTo("MODEL_UNAVAILABLE");
    }

    @Test
    void signalOfAnotherIntersectionIsNotFound() throws Exception {
        String body = mvc.perform(get("/api/v1/intersections")).andReturn().getResponse().getContentAsString();
        long firstIntersection = ((Number) JsonPath.read(body, "$[0].id")).longValue();
        long signalOfSecond = ((Number) JsonPath.read(body, "$[1].signals[0].id")).longValue();

        mvc.perform(post("/api/v1/predictions").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"intersectionId\": %d, \"signalId\": %d}".formatted(firstIntersection, signalOfSecond)))
                .andExpect(status().isNotFound());
    }

    @Test
    void healthAndOpenApiAreExposed() throws Exception {
        mvc.perform(get("/actuator/health")).andExpect(status().isOk()).andExpect(jsonPath("$.status").value("UP"));
        mvc.perform(get("/v3/api-docs")).andExpect(status().isOk())
                .andExpect(jsonPath("$.info.title").value("Traffic Light Predictor API"));
    }
}
