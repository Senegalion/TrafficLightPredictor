package io.github.senegalion.tlp.observation;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import io.github.senegalion.tlp.common.ConflictException;
import io.github.senegalion.tlp.common.InvalidRequestException;
import io.github.senegalion.tlp.common.SignalPhase;
import io.github.senegalion.tlp.intersection.IntersectionService;
import io.github.senegalion.tlp.intersection.TrafficSignal;
import io.github.senegalion.tlp.support.TestEntities;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ObservationServiceTest {

    private static final Instant NOW = Instant.parse("2026-10-05T10:00:00Z");

    @Mock
    private ObservationRepository repository;

    @Mock
    private IntersectionService intersections;

    private ObservationService service;
    private TrafficSignal signal;

    @BeforeEach
    void setUp() {
        service = new ObservationService(repository, intersections,
                new ObservationProperties(Duration.ofMinutes(1)), Clock.fixed(NOW, ZoneOffset.UTC));
        signal = TestEntities.signal(1L, 10L);
    }

    private CreateObservationRequest request(Instant observedAt) {
        return new CreateObservationRequest(10L, observedAt, SignalPhase.GREEN, 40, TravelDirection.NORTHBOUND,
                "  manual-observation ", false);
    }

    @Test
    void createsObservationForSignalOfIntersection() {
        when(intersections.findSignal(1L, 10L)).thenReturn(signal);
        when(repository.save(any(Observation.class))).thenAnswer(invocation -> invocation.getArgument(0));

        ObservationResponse response = service.create(1L, request(NOW.minusSeconds(5)));

        ArgumentCaptor<Observation> saved = ArgumentCaptor.forClass(Observation.class);
        verify(repository).save(saved.capture());
        assertThat(saved.getValue().getSource()).isEqualTo("manual-observation");
        assertThat(saved.getValue().isSimulated()).isFalse();
        assertThat(response.signalCode()).isEqualTo("LDZ-TEST-S1");
        assertThat(response.intersectionId()).isEqualTo(1L);
    }

    @Test
    void rejectsObservationsFromTheFuture() {
        when(intersections.findSignal(1L, 10L)).thenReturn(signal);

        assertThatThrownBy(() -> service.create(1L, request(NOW.plusSeconds(120))))
                .isInstanceOf(InvalidRequestException.class);
        verify(repository, never()).save(any());
    }

    @Test
    void allowsSmallClockSkew() {
        when(intersections.findSignal(1L, 10L)).thenReturn(signal);
        when(repository.save(any(Observation.class))).thenAnswer(invocation -> invocation.getArgument(0));

        assertThat(service.create(1L, request(NOW.plusSeconds(30)))).isNotNull();
    }

    @Test
    void rejectsDuplicateObservation() {
        when(intersections.findSignal(1L, 10L)).thenReturn(signal);
        when(repository.existsBySignalIdAndObservedAt(10L, NOW)).thenReturn(true);

        assertThatThrownBy(() -> service.create(1L, request(NOW))).isInstanceOf(ConflictException.class);
    }

    @Test
    void rejectsInvertedTimeRange() {
        assertThatThrownBy(() -> service.list(1L, null, NOW, NOW.minusSeconds(1), null))
                .isInstanceOf(InvalidRequestException.class);
    }
}
