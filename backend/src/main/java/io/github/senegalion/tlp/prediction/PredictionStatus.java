package io.github.senegalion.tlp.prediction;

public enum PredictionStatus {
    /** Prediction is considered reliable enough to be displayed. */
    OK,
    /** The model produced a prediction, but it does not meet the reliability policy; do not display it. */
    LOW_CONFIDENCE,
    /** No sufficiently recent observation exists to predict from. */
    INSUFFICIENT_DATA,
    /** The model has not been trained for this signal. */
    UNSUPPORTED_SIGNAL,
    /** The ML service could not be reached. */
    MODEL_UNAVAILABLE
}
