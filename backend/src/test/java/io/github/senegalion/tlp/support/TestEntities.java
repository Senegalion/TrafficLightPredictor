package io.github.senegalion.tlp.support;

import io.github.senegalion.tlp.common.SignalPhase;
import io.github.senegalion.tlp.intersection.ConfigurationSource;
import io.github.senegalion.tlp.intersection.Intersection;
import io.github.senegalion.tlp.intersection.LocationSource;
import io.github.senegalion.tlp.intersection.TrafficSignal;
import io.github.senegalion.tlp.observation.Observation;
import java.time.Instant;
import org.springframework.test.util.ReflectionTestUtils;

/** Builds detached entities with ids for unit tests. */
public final class TestEntities {

    private TestEntities() {
    }

    public static TrafficSignal signal(long intersectionId, long signalId) {
        Intersection intersection = new Intersection("LDZ-TEST", "Test / Example", "Łódź", 51.76, 19.45,
                LocationSource.SAMPLE);
        ReflectionTestUtils.setField(intersection, "id", intersectionId);
        TrafficSignal signal = intersection.addSignal("LDZ-TEST-S1", "Main road", ConfigurationSource.SAMPLE);
        ReflectionTestUtils.setField(signal, "id", signalId);
        return signal;
    }

    public static Observation observation(TrafficSignal signal, Instant observedAt, SignalPhase phase,
                                          boolean simulated) {
        Observation observation = new Observation(signal, observedAt, phase, null, null, "test", simulated);
        ReflectionTestUtils.setField(observation, "id", 99L);
        return observation;
    }
}
