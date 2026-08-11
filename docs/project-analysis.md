# Traffic Light Predictor — Project Analysis

## 1. Project Overview

Traffic Light Predictor is a system designed to predict traffic signal phases and estimate the remaining time until the next phase change.

The initial target area is Łódź, Poland.

The system is intended primarily for drivers approaching signalized intersections.

---

## 2. Problem

Drivers approaching a signalized intersection often do not know how long the current traffic signal phase will last.

For example, a driver approaching a green light may not know whether:

- the green phase will continue for several seconds,
- the signal will soon change to yellow,
- the signal will remain green long enough to pass the intersection,
- the driver should maintain their current speed,
- the driver should begin slowing down safely.

The system aims to provide an early prediction of the upcoming traffic signal phase.

---

## 3. Main Objective

The main objective is to develop a system capable of predicting the current and upcoming traffic signal phase for a vehicle approaching an intersection.

The system should provide an estimated time to the next phase change when the prediction confidence is sufficiently high.

The system must also be able to indicate when a reliable prediction cannot be made.

---

## 4. Initial Geographic Scope

The first version of the system will cover:

- Łódź, Poland

Zgierz and other cities may be added in later development stages.

---

## 5. Core Use Case

A driver is approaching a signalized intersection.

The system:

1. Determines the driver's current location.
2. Determines the direction of travel.
3. Identifies the relevant upcoming intersection.
4. Identifies the relevant traffic signal.
5. Determines the current signal phase when possible.
6. Predicts the next phase change.
7. Estimates the remaining duration of the current phase.
8. Provides the prediction to the driver.
9. Provides a confidence level for the prediction.

Example:

    GREEN
    ~12 seconds remaining
    Confidence: 87%

If the prediction is unreliable:

    GREEN
    Prediction unavailable

---

## 6. Important Safety Principle

The system is an assistance and prediction system.

It must not instruct drivers to:

- exceed the speed limit,
- perform dangerous acceleration,
- perform dangerous braking,
- ignore traffic rules,
- intentionally cross an intersection during a red signal.

Predictions should be presented as estimates, not guarantees.

---

## 7. Data Sources

### 7.1 OpenStreetMap

OpenStreetMap will be used as the initial source of static road and traffic signal infrastructure data.

Potential information includes:

- traffic signal locations,
- road geometry,
- intersections,
- road names,
- road directions,
- traffic signal metadata.

### 7.2 Open Data Łódź

The Open Data Łódź portal will be investigated as a source of additional transport and spatial data.

Potentially useful datasets include:

- public transport data,
- GTFS,
- GTFS-RT,
- vehicle positions,
- transport infrastructure,
- spatial data.

### 7.3 Own Observations

The project will collect observations of real traffic signal phases.

Potential observations include:

- timestamp,
- GPS position,
- traffic signal phase,
- intersection,
- direction,
- observation source.

### 7.4 Computer Vision

Computer vision may later be used to automatically detect traffic signal phases from camera footage.

Potential phases:

- RED
- YELLOW
- GREEN

---

## 8. Data Risk

The most important project risk is the lack of a publicly available dataset containing real-time traffic signal phase and timing information for all intersections.

The project therefore assumes that historical traffic signal observations may need to be collected independently.

The availability and quality of these observations must be experimentally validated before implementing the final prediction system.

---

## 9. Research Hypothesis

Historical observations of traffic signal phases contain sufficient temporal and contextual information to predict the next traffic signal phase for at least a subset of intersections in Łódź.

---

## 10. MVP Hypothesis

The MVP will be considered technically promising if the system can achieve useful prediction accuracy on a representative subset of intersections.

Initial target:

    Mean Absolute Error (MAE) <= 5 seconds

This is an initial engineering target and may be revised after the first dataset analysis.

---

## 11. Baseline Model

Before implementing machine learning, a simple statistical baseline will be developed.

The baseline may use:

- historical phase duration,
- historical cycle duration,
- time of day,
- day of week,
- current phase,
- time elapsed since the phase started.

The baseline will provide a reference point for evaluating machine learning models.

---

## 12. Machine Learning

Machine learning will only be introduced after a sufficiently large and reliable dataset has been collected.

Potential input features:

- intersection identifier,
- day of week,
- time of day,
- current phase,
- elapsed phase duration,
- historical phase duration,
- historical cycle duration,
- traffic volume,
- public transport presence,
- weather,
- other relevant contextual information.

Potential predictions:

- next traffic signal phase,
- time until next phase,
- remaining duration of current phase.

---

## 13. Evaluation

The system will be evaluated using quantitative metrics.

Potential metrics:

- MAE,
- RMSE,
- median absolute error,
- P90 error,
- phase classification accuracy.

Evaluation should be performed separately for different intersections and traffic conditions.

---

## 14. Confidence

The system should provide a confidence score or confidence category.

Possible behavior:

High confidence:
- provide a numerical estimate.

Medium confidence:
- provide an estimated range.

Low confidence:
- do not provide a numerical prediction.

---

## 15. Planned System Components

### Data Collector

Collects observations of real traffic signal phases.

### Geospatial Data Service

Stores and queries traffic signal and road infrastructure data.

### Prediction Service

Generates traffic signal phase predictions.

### Backend API

Provides data and predictions to client applications.

### Mobile Application

Provides real-time information to drivers.

### Analytics Dashboard

Provides system monitoring and prediction analysis.

### Machine Learning Pipeline

Processes datasets, trains models and evaluates prediction quality.

---

## 16. Initial Technology Stack

### Backend

- Java
- Spring Boot
- PostgreSQL
- PostGIS

### Data / Machine Learning

- Python
- pandas
- NumPy
- scikit-learn

### Mobile

- Kotlin
- Android

### Infrastructure

- Docker
- GitHub Actions
- Kubernetes (later stage)

---

## 17. Development Strategy

The project will follow an experiment-driven development process.

The system will not be fully implemented before validating data availability.

The development order is:

1. Data source research
2. Static traffic signal dataset
3. Data model
4. Observation collector
5. Initial dataset
6. Data analysis
7. Statistical baseline
8. Machine learning
9. Backend API
10. Mobile application
11. Analytics dashboard
12. Production infrastructure

---

## 18. Success Criteria

The project will be considered successful if it demonstrates that traffic signal phase changes can be predicted with useful accuracy for a meaningful subset of intersections.

The system should also demonstrate:

- reliable geospatial intersection detection,
- sufficient observation data,
- measurable prediction accuracy,
- confidence estimation,
- real-world testing.

---

## 19. Future Development

Potential future extensions:

- Zgierz
- other Polish cities
- crowdsourced observations
- improved computer vision
- real-time traffic data
- public transport priority detection
- route-aware predictions
- Android Auto integration
- green-wave recommendations
- B2B traffic analytics