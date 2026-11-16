package io.github.senegalion.tlp.prediction;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import io.github.senegalion.tlp.common.InvalidRequestException;
import io.github.senegalion.tlp.common.SignalPhase;
import io.github.senegalion.tlp.intersection.IntersectionService;
import io.github.senegalion.tlp.intersection.TrafficSignal;
import io.github.senegalion.tlp.observation.Observation;
import io.github.senegalion.tlp.observation.ObservationService;
import io.github.senegalion.tlp.prediction.ml.MlPredictionClient;
import io.github.senegalion.tlp.prediction.ml.MlPredictionRequest;
import io.github.senegalion.tlp.prediction.ml.MlPredictionResponse;
import io.github.senegalion.tlp.prediction.ml.MlServiceUnavailableException;
import io.github.senegalion.tlp.support.TestEntities;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class PredictionServiceTest {

    private static final Instant NOW = Instant.parse("2026-10-05T10:00:00Z");

    @Mock
    private IntersectionService intersections;
    @Mock
    private ObservationService observations;
    @Mock
    private PredictionRepository predictions;
    @Mock
    private MlPredictionClient mlClient;

    private PredictionService service;
    private TrafficSignal signal;

    @BeforeEach
    void setUp() {
        PredictionProperties properties =
                new PredictionProperties(Duration.ofMinutes(15), Duration.ofMinutes(2), Duration.ofDays(7));
        service = new PredictionService(intersections, observations, predictions, mlClient, properties,
                Clock.fixed(NOW, ZoneOffset.UTC));
        signal = TestEntities.signal(1L, 10L);
    }

    private static MlPredictionResponse okResponse() {
        return new MlPredictionResponse("OK", true, "tlp-gbm-test", "SYNTHETIC", List.of(), SignalPhase.GREEN, 0.91,
                Map.of(SignalPhase.RED, 0.05, SignalPhase.YELLOW, 0.04, SignalPhase.GREEN, 0.91),
                12.0, 8.0, 15.0, 20.0);
    }

    @Test
    void noObservationMeansInsufficientDataWithoutCallingModel() {
        when(intersections.findSignal(1L, 10L)).thenReturn(signal);
        when(observations.latestAtOrBefore(10L, NOW)).thenReturn(Optional.empty());

        PredictionResponse response = service.create(new CreatePredictionRequest(1L, 10L, null));

        assertThat(response.status()).isEqualTo(PredictionStatus.INSUFFICIENT_DATA);
        assertThat(response.displayable()).isFalse();
        assertThat(response.dataOrigin()).isEqualTo(DataOrigin.NONE);
        assertThat(response.predictedPhase()).isNull();
        verifyNoInteractions(mlClient);
        verify(predictions).save(any(PredictionRecord.class));
    }

    @Test
    void staleObservationMeansInsufficientData() {
        Observation old = TestEntities.observation(signal, NOW.minus(Duration.ofMinutes(20)), SignalPhase.RED, true);
        when(intersections.findSignal(1L, 10L)).thenReturn(signal);
        when(observations.latestAtOrBefore(10L, NOW)).thenReturn(Optional.of(old));

        PredictionResponse response = service.create(new CreatePredictionRequest(1L, 10L, null));

        assertThat(response.status()).isEqualTo(PredictionStatus.INSUFFICIENT_DATA);
        assertThat(response.anchorObservation().ageSeconds()).isEqualTo(1200.0);
        verify(mlClient, never()).predict(any());
    }

    @Test
    void freshObservationIsSentToModelAndResultMapped() {
        Observation anchor = TestEntities.observation(signal, NOW.minusSeconds(20), SignalPhase.GREEN, true);
        when(intersections.findSignal(1L, 10L)).thenReturn(signal);
        when(observations.latestAtOrBefore(10L, NOW)).thenReturn(Optional.of(anchor));
        when(mlClient.predict(any())).thenReturn(okResponse());

        PredictionResponse response = service.create(new CreatePredictionRequest(1L, 10L, null));

        ArgumentCaptor<MlPredictionRequest> sent = ArgumentCaptor.forClass(MlPredictionRequest.class);
        verify(mlClient).predict(sent.capture());
        assertThat(sent.getValue().signalCode()).isEqualTo("LDZ-TEST-S1");
        assertThat(sent.getValue().targetTime()).isEqualTo(NOW);
        assertThat(sent.getValue().anchor().phase()).isEqualTo(SignalPhase.GREEN);
        assertThat(sent.getValue().anchor().observedAt()).isEqualTo(NOW.minusSeconds(20));

        assertThat(response.status()).isEqualTo(PredictionStatus.OK);
        assertThat(response.displayable()).isTrue();
        assertThat(response.predictedPhase()).isEqualTo(SignalPhase.GREEN);
        assertThat(response.confidence()).isEqualTo(0.91);
        assertThat(response.phaseProbabilities()).containsEntry(SignalPhase.RED, 0.05);
        assertThat(response.remainingSeconds()).isEqualTo(12.0);
        assertThat(response.remainingSecondsLower()).isEqualTo(8.0);
        assertThat(response.remainingSecondsUpper()).isEqualTo(15.0);
        assertThat(response.modelVersion()).isEqualTo("tlp-gbm-test");
        assertThat(response.dataOrigin()).isEqualTo(DataOrigin.SIMULATED);
        assertThat(response.disclaimer()).contains("SIMULATED").contains("SYNTHETIC").contains("not a guarantee");
    }

    @Test
    void lowConfidenceResultIsNeverDisplayable() {
        Observation anchor = TestEntities.observation(signal, NOW.minusSeconds(400), SignalPhase.RED, false);
        when(intersections.findSignal(1L, 10L)).thenReturn(signal);
        when(observations.latestAtOrBefore(10L, NOW)).thenReturn(Optional.of(anchor));
        when(mlClient.predict(any())).thenReturn(new MlPredictionResponse("LOW_CONFIDENCE", false, "v", "SYNTHETIC",
                List.of("Calibrated confidence 0.55 is below the display threshold 0.80."), SignalPhase.RED, 0.55,
                Map.of(SignalPhase.RED, 0.55, SignalPhase.YELLOW, 0.05, SignalPhase.GREEN, 0.40),
                20.0, 2.0, 45.0, 400.0));

        PredictionResponse response = service.create(new CreatePredictionRequest(1L, 10L, null));

        assertThat(response.status()).isEqualTo(PredictionStatus.LOW_CONFIDENCE);
        assertThat(response.displayable()).isFalse();
        assertThat(response.dataOrigin()).isEqualTo(DataOrigin.REAL);
        assertThat(response.message()).contains("below the display threshold");
    }

    @Test
    void unavailableModelIsReportedAsStatus() {
        Observation anchor = TestEntities.observation(signal, NOW.minusSeconds(20), SignalPhase.GREEN, true);
        when(intersections.findSignal(1L, 10L)).thenReturn(signal);
        when(observations.latestAtOrBefore(10L, NOW)).thenReturn(Optional.of(anchor));
        when(mlClient.predict(any())).thenThrow(new MlServiceUnavailableException("down", null));

        PredictionResponse response = service.create(new CreatePredictionRequest(1L, 10L, null));

        assertThat(response.status()).isEqualTo(PredictionStatus.MODEL_UNAVAILABLE);
        assertThat(response.displayable()).isFalse();
    }

    @Test
    void unknownModelStatusIsTreatedAsUnavailable() {
        Observation anchor = TestEntities.observation(signal, NOW.minusSeconds(20), SignalPhase.GREEN, true);
        when(intersections.findSignal(1L, 10L)).thenReturn(signal);
        when(observations.latestAtOrBefore(10L, NOW)).thenReturn(Optional.of(anchor));
        when(mlClient.predict(any())).thenReturn(new MlPredictionResponse("SOMETHING_NEW", true, "v", "SYNTHETIC",
                List.of(), null, null, null, null, null, null, null));

        assertThat(service.create(new CreatePredictionRequest(1L, 10L, null)).status())
                .isEqualTo(PredictionStatus.MODEL_UNAVAILABLE);
    }

    @Test
    void targetTooFarInFutureIsRejected() {
        when(intersections.findSignal(1L, 10L)).thenReturn(signal);

        assertThatThrownBy(() -> service.create(new CreatePredictionRequest(1L, 10L, NOW.plusSeconds(600))))
                .isInstanceOf(InvalidRequestException.class);
        verifyNoInteractions(predictions);
    }

    @Test
    void targetTooFarInPastIsRejected() {
        when(intersections.findSignal(1L, 10L)).thenReturn(signal);

        assertThatThrownBy(() -> service.create(
                new CreatePredictionRequest(1L, 10L, NOW.minus(Duration.ofDays(30)))))
                .isInstanceOf(InvalidRequestException.class);
    }
}
