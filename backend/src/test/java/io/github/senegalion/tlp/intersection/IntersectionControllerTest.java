package io.github.senegalion.tlp.intersection;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import io.github.senegalion.tlp.common.ResourceNotFoundException;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(IntersectionController.class)
class IntersectionControllerTest {

    private static final IntersectionResponse INTERSECTION = new IntersectionResponse(1L, "LDZ-KOS-STR",
            "Al. Kościuszki / Struga", "Łódź", "desc", 51.765, 19.454, LocationSource.OPENSTREETMAP, "nodes",
            List.of(new TrafficSignalResponse(10L, "LDZ-KOS-STR-S1", "Main", null, "Al. Kościuszki",
                    ConfigurationSource.SAMPLE)));

    @Autowired
    private MockMvc mvc;

    @MockitoBean
    private IntersectionService service;

    @Test
    void listsIntersections() throws Exception {
        when(service.list()).thenReturn(List.of(INTERSECTION));

        mvc.perform(get("/api/v1/intersections"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].code").value("LDZ-KOS-STR"))
                .andExpect(jsonPath("$[0].locationSource").value("OPENSTREETMAP"))
                .andExpect(jsonPath("$[0].signals[0].configurationSource").value("SAMPLE"));
    }

    @Test
    void unknownIntersectionReturnsProblemDetail() throws Exception {
        when(service.get(99L)).thenThrow(new ResourceNotFoundException("Intersection", 99L));

        mvc.perform(get("/api/v1/intersections/99"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.title").value("Resource not found"))
                .andExpect(jsonPath("$.status").value(404));
    }

    @Test
    void nearbyReturnsDistances() throws Exception {
        when(service.nearby(51.765, 19.454, 500, 10))
                .thenReturn(List.of(new NearbyIntersectionResponse(12.5, INTERSECTION)));

        mvc.perform(get("/api/v1/intersections/nearby")
                        .param("latitude", "51.765").param("longitude", "19.454").param("radiusMeters", "500"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].distanceMeters").value(12.5))
                .andExpect(jsonPath("$[0].intersection.id").value(1));
    }

    @Test
    void nearbyRejectsInvalidCoordinates() throws Exception {
        mvc.perform(get("/api/v1/intersections/nearby").param("latitude", "123").param("longitude", "19"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void nearbyRejectsTooLargeRadius() throws Exception {
        mvc.perform(get("/api/v1/intersections/nearby")
                        .param("latitude", "51").param("longitude", "19").param("radiusMeters", "999999"))
                .andExpect(status().isBadRequest());
    }
}
