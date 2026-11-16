package io.github.senegalion.tlp.intersection;

import static org.assertj.core.api.Assertions.assertThat;

import io.github.senegalion.tlp.support.PostgisTestcontainersConfig;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;
import org.springframework.boot.jdbc.test.autoconfigure.AutoConfigureTestDatabase;
import org.springframework.context.annotation.Import;

@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Import(PostgisTestcontainersConfig.class)
class IntersectionRepositoryTest {

    private static final double KOSCIUSZKI_STRUGA_LAT = 51.7652940;
    private static final double KOSCIUSZKI_STRUGA_LON = 19.4543812;

    @Autowired
    private IntersectionRepository repository;

    @Test
    void flywaySeedContainsSampleIntersectionsWithSignals() {
        List<Intersection> all = repository.findAllWithSignals();

        assertThat(all).hasSize(6);
        assertThat(all).allSatisfy(intersection -> {
            assertThat(intersection.getCity()).isEqualTo("Łódź");
            assertThat(intersection.getLocationSource()).isEqualTo(LocationSource.OPENSTREETMAP);
            assertThat(intersection.getSignals()).hasSize(2)
                    .allSatisfy(signal -> assertThat(signal.getConfigurationSource())
                            .isEqualTo(ConfigurationSource.SAMPLE));
        });
    }

    @Test
    void findNearbyReturnsIntersectionsOrderedByDistance() {
        List<IntersectionRepository.NearbyIntersectionRow> rows =
                repository.findNearby(KOSCIUSZKI_STRUGA_LAT, KOSCIUSZKI_STRUGA_LON, 1000, 10);

        assertThat(rows).hasSizeGreaterThanOrEqualTo(2);
        assertThat(rows.getFirst().getDistanceMeters()).isLessThan(1.0);
        assertThat(rows).extracting(IntersectionRepository.NearbyIntersectionRow::getDistanceMeters).isSorted();
        Intersection nearest = repository.findById(rows.getFirst().getId()).orElseThrow();
        assertThat(nearest.getCode()).isEqualTo("LDZ-KOS-STR");
        // Al. Kościuszki / Zamenhofa is roughly 350 m south.
        assertThat(rows.get(1).getDistanceMeters()).isBetween(300.0, 400.0);
    }

    @Test
    void findNearbyRespectsRadiusAndLimit() {
        assertThat(repository.findNearby(KOSCIUSZKI_STRUGA_LAT, KOSCIUSZKI_STRUGA_LON, 100, 10)).hasSize(1);
        assertThat(repository.findNearby(KOSCIUSZKI_STRUGA_LAT, KOSCIUSZKI_STRUGA_LON, 20_000, 3)).hasSize(3);
        assertThat(repository.findNearby(52.2297, 21.0122, 20_000, 10)).isEmpty(); // Warsaw
    }
}
