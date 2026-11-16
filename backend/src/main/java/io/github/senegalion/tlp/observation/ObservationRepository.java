package io.github.senegalion.tlp.observation;

import java.time.Instant;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ObservationRepository extends JpaRepository<Observation, Long> {

    @EntityGraph(attributePaths = "signal")
    Page<Observation> findByIntersectionIdAndObservedAtBetween(
            Long intersectionId, Instant from, Instant to, Pageable pageable);

    @EntityGraph(attributePaths = "signal")
    Page<Observation> findByIntersectionIdAndSignalIdAndObservedAtBetween(
            Long intersectionId, Long signalId, Instant from, Instant to, Pageable pageable);

    /** The most recent observation of a signal at or before {@code time}: the prediction anchor. */
    Optional<Observation> findFirstBySignalIdAndObservedAtLessThanEqualOrderByObservedAtDesc(
            Long signalId, Instant time);

    boolean existsBySignalIdAndObservedAt(Long signalId, Instant observedAt);
}
