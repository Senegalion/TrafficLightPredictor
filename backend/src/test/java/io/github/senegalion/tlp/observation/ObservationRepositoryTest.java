package io.github.senegalion.tlp.observation;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import io.github.senegalion.tlp.common.SignalPhase;
import io.github.senegalion.tlp.intersection.IntersectionRepository;
import io.github.senegalion.tlp.intersection.TrafficSignal;
import io.github.senegalion.tlp.support.PostgisTestcontainersConfig;
import java.time.Instant;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;
import org.springframework.boot.jdbc.test.autoconfigure.AutoConfigureTestDatabase;
import org.springframework.context.annotation.Import;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;

@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Import(PostgisTestcontainersConfig.class)
class ObservationRepositoryTest {

    private static final Instant T0 = Instant.parse("2026-10-05T10:00:00Z");

    @Autowired
    private ObservationRepository observations;

    @Autowired
    private IntersectionRepository intersections;

    private TrafficSignal signal;

    @BeforeEach
    void setUp() {
        signal = intersections.findAllWithSignals().getFirst().getSignals().getFirst();
    }

    private Observation save(Instant at, SignalPhase phase, Integer duration) {
        return observations.saveAndFlush(new Observation(signal, at, phase, duration, null, "test", true));
    }

    @Test
    void latestAnchorIsMostRecentObservationAtOrBeforeTime() {
        save(T0, SignalPhase.GREEN, 40);
        save(T0.plusSeconds(40), SignalPhase.YELLOW, 3);
        save(T0.plusSeconds(43), SignalPhase.RED, null);

        assertThat(observations.findFirstBySignalIdAndObservedAtLessThanEqualOrderByObservedAtDesc(
                signal.getId(), T0.plusSeconds(42))).get()
                .extracting(Observation::getPhase).isEqualTo(SignalPhase.YELLOW);
        assertThat(observations.findFirstBySignalIdAndObservedAtLessThanEqualOrderByObservedAtDesc(
                signal.getId(), T0.plusSeconds(43))).get()
                .extracting(Observation::getPhase).isEqualTo(SignalPhase.RED);
        assertThat(observations.findFirstBySignalIdAndObservedAtLessThanEqualOrderByObservedAtDesc(
                signal.getId(), T0.minusSeconds(1))).isEmpty();
    }

    @Test
    void pagesAreFilteredByTimeRangeAndSortedNewestFirst() {
        save(T0, SignalPhase.GREEN, 40);
        save(T0.plusSeconds(40), SignalPhase.YELLOW, 3);
        save(T0.plusSeconds(43), SignalPhase.RED, 50);

        var page = observations.findByIntersectionIdAndSignalIdAndObservedAtBetween(
                signal.getIntersection().getId(), signal.getId(), T0.plusSeconds(1), T0.plusSeconds(100),
                PageRequest.of(0, 10, Sort.by(Sort.Direction.DESC, "observedAt")));

        assertThat(page.getContent()).extracting(Observation::getPhase)
                .containsExactly(SignalPhase.RED, SignalPhase.YELLOW);
    }

    @Test
    void duplicateObservationOfSameSignalAndTimeIsRejected() {
        save(T0, SignalPhase.GREEN, 40);

        assertThatThrownBy(() -> save(T0, SignalPhase.RED, 40))
                .isInstanceOf(DataIntegrityViolationException.class);
    }

    @Test
    void databaseRejectsImplausiblePhaseDuration() {
        assertThatThrownBy(() -> save(T0, SignalPhase.GREEN, 10_000))
                .isInstanceOf(DataIntegrityViolationException.class);
    }
}
