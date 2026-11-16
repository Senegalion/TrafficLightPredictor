package io.github.senegalion.tlp.intersection;

import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface IntersectionRepository extends JpaRepository<Intersection, Long> {

    @EntityGraph(attributePaths = "signals")
    @Query("select i from Intersection i order by i.name")
    List<Intersection> findAllWithSignals();

    @EntityGraph(attributePaths = "signals")
    @Query("select i from Intersection i where i.id = :id")
    Optional<Intersection> findWithSignalsById(@Param("id") Long id);

    /** Intersections within {@code radiusMeters} of a point, nearest first (PostGIS geography distance). */
    @Query(value = """
            SELECT i.id AS id,
                   ST_Distance(i.location, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography) AS distanceMeters
            FROM intersections i
            WHERE ST_DWithin(i.location, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography, :radiusMeters)
            ORDER BY distanceMeters
            LIMIT :maxResults
            """, nativeQuery = true)
    List<NearbyIntersectionRow> findNearby(@Param("latitude") double latitude,
                                           @Param("longitude") double longitude,
                                           @Param("radiusMeters") double radiusMeters,
                                           @Param("maxResults") int maxResults);

    interface NearbyIntersectionRow {
        Long getId();

        Double getDistanceMeters();
    }
}
