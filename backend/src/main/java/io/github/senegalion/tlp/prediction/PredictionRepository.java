package io.github.senegalion.tlp.prediction;

import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PredictionRepository extends JpaRepository<PredictionRecord, UUID> {

    @EntityGraph(attributePaths = {"intersection", "signal", "anchorObservation"})
    Optional<PredictionRecord> findWithDetailsById(UUID id);
}
