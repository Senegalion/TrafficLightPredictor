package io.github.senegalion.tlp.prediction;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import io.github.senegalion.tlp.common.InvalidRequestException;
import io.github.senegalion.tlp.common.ResourceNotFoundException;
import io.github.senegalion.tlp.prediction.ml.MlPredictionClient;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest({PredictionController.class, ModelInfoController.class})
class PredictionControllerTest {

    private static final UUID ID = UUID.fromString("7b0a4f8e-4a56-4a4b-9d60-3c4ab1f0c7a1");

    @Autowired
    private MockMvc mvc;

    @MockitoBean
    private PredictionService service;

    @MockitoBean
    private MlPredictionClient mlClient;

    private static PredictionResponse insufficient() {
        Instant now = Instant.parse("2026-10-05T10:00:00Z");
        return new PredictionResponse(ID, 1L, "Al. Kościuszki / Struga", 10L, "LDZ-KOS-STR-S1",
                PredictionStatus.INSUFFICIENT_DATA, false, null, null, null, null, null, null, now, now, null, null,
                DataOrigin.NONE, null, "No observation", "Experimental estimate, not a guarantee.");
    }

    @Test
    void createsPrediction() throws Exception {
        when(service.create(any())).thenReturn(insufficient());

        mvc.perform(post("/api/v1/predictions").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"intersectionId\": 1, \"signalId\": 10}"))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", "/api/v1/predictions/" + ID))
                .andExpect(jsonPath("$.status").value("INSUFFICIENT_DATA"))
                .andExpect(jsonPath("$.displayable").value(false))
                .andExpect(jsonPath("$.disclaimer").isNotEmpty());
    }

    @Test
    void rejectsMissingSignal() throws Exception {
        mvc.perform(post("/api/v1/predictions").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"intersectionId\": 1}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void businessRuleViolationIsBadRequest() throws Exception {
        when(service.create(any())).thenThrow(new InvalidRequestException("too far in future"));

        mvc.perform(post("/api/v1/predictions").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"intersectionId\": 1, \"signalId\": 10, \"targetTime\": \"2030-01-01T00:00:00Z\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value("too far in future"));
    }

    @Test
    void getsStoredPrediction() throws Exception {
        when(service.get(ID)).thenReturn(insufficient());

        mvc.perform(get("/api/v1/predictions/" + ID))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(ID.toString()));
    }

    @Test
    void unknownPredictionIsNotFound() throws Exception {
        when(service.get(any())).thenThrow(new ResourceNotFoundException("Prediction", ID));

        mvc.perform(get("/api/v1/predictions/" + ID)).andExpect(status().isNotFound());
    }

    @Test
    void malformedIdIsBadRequest() throws Exception {
        mvc.perform(get("/api/v1/predictions/not-a-uuid")).andExpect(status().isBadRequest());
    }

    @Test
    void modelInfoUnavailableIs503() throws Exception {
        when(mlClient.modelInfo()).thenThrow(
                new io.github.senegalion.tlp.prediction.ml.MlServiceUnavailableException("down", null));

        mvc.perform(get("/api/v1/model")).andExpect(status().isServiceUnavailable());
    }
}
