package io.github.senegalion.tlp.observation;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import io.github.senegalion.tlp.common.ConflictException;
import io.github.senegalion.tlp.common.SignalPhase;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(ObservationController.class)
@TestPropertySource(properties = "tlp.web.ingestion-api-key=test-key")
class ObservationControllerTest {

    private static final String VALID_BODY = """
            {"signalId": 10, "observedAt": "2026-10-05T10:00:00Z", "phase": "GREEN",
             "phaseDurationSeconds": 40, "source": "manual-observation", "simulated": false}
            """;

    @Autowired
    private MockMvc mvc;

    @MockitoBean
    private ObservationService service;

    @Test
    void createsObservationWithValidApiKey() throws Exception {
        when(service.create(eq(1L), any())).thenReturn(new ObservationResponse(5L, 1L, 10L, "LDZ-KOS-STR-S1",
                Instant.parse("2026-10-05T10:00:00Z"), SignalPhase.GREEN, 40, null, "manual-observation", false));

        mvc.perform(post("/api/v1/intersections/1/observations")
                        .header("X-Api-Key", "test-key")
                        .contentType(MediaType.APPLICATION_JSON).content(VALID_BODY))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", "/api/v1/intersections/1/observations/5"))
                .andExpect(jsonPath("$.simulated").value(false));
    }

    @Test
    void rejectsMissingApiKey() throws Exception {
        mvc.perform(post("/api/v1/intersections/1/observations")
                        .contentType(MediaType.APPLICATION_JSON).content(VALID_BODY))
                .andExpect(status().isUnauthorized());
        verifyNoInteractions(service);
    }

    @Test
    void rejectsWrongApiKey() throws Exception {
        mvc.perform(post("/api/v1/intersections/1/observations")
                        .header("X-Api-Key", "wrong")
                        .contentType(MediaType.APPLICATION_JSON).content(VALID_BODY))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void rejectsInvalidBodyWithFieldErrors() throws Exception {
        mvc.perform(post("/api/v1/intersections/1/observations")
                        .header("X-Api-Key", "test-key")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"signalId": 10, "observedAt": "2026-10-05T10:00:00Z", "phase": "GREEN",
                                 "phaseDurationSeconds": 0, "source": " "}
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errors[?(@.field == 'simulated')]").exists())
                .andExpect(jsonPath("$.errors[?(@.field == 'source')]").exists())
                .andExpect(jsonPath("$.errors[?(@.field == 'phaseDurationSeconds')]").exists());
    }

    @Test
    void rejectsUnknownPhase() throws Exception {
        mvc.perform(post("/api/v1/intersections/1/observations")
                        .header("X-Api-Key", "test-key")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(VALID_BODY.replace("GREEN", "BLUE")))
                .andExpect(status().isBadRequest());
    }

    @Test
    void duplicateReturnsConflict() throws Exception {
        when(service.create(eq(1L), any())).thenThrow(new ConflictException("duplicate"));

        mvc.perform(post("/api/v1/intersections/1/observations")
                        .header("X-Api-Key", "test-key")
                        .contentType(MediaType.APPLICATION_JSON).content(VALID_BODY))
                .andExpect(status().isConflict());
    }
}
