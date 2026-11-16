package io.github.senegalion.tlp.prediction;

/** Origin of the observation a prediction was computed from. */
public enum DataOrigin {
    REAL,
    SIMULATED,
    /** No observation was used. */
    NONE
}
