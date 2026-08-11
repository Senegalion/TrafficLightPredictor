# Traffic Light Predictor

> Intelligent traffic signal phase and timing prediction system for Łódź, Poland.

## Project Status

🚧 **Research & Development**

The project is currently in the data acquisition and feasibility validation stage.

## Problem

Drivers approaching traffic-light-controlled intersections often do not know how long the current signal phase will last.

Traffic Light Predictor aims to estimate the current traffic signal phase and predict the approximate time until the next phase change.

The system is designed to provide predictions before the driver reaches the intersection.

## Initial Scope

The first version focuses exclusively on:

- 📍 Łódź, Poland

Additional cities may be supported in future versions.

## Core Idea

```text
GPS
 ↓
Upcoming intersection
 ↓
Traffic signal identification
 ↓
Historical observations
 ↓
Prediction model
 ↓
Current phase + estimated time to change
 ↓
Mobile application
```

## Example

🟢 GREEN

Estimated change:
~12 seconds

Confidence:
87%

The system must be able to indicate when a reliable prediction is not available.

## Main Components

- Data Collector
- Geospatial Data Service
- Prediction / ML Pipeline
- Backend API
- Android Application
- Analytics Dashboard
- Infrastructure

## Technology

### Backend
- Java
- Spring Boot
- PostgreSQL
- PostGIS

### Data & ML
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
- Kubernetes

## Development Approach

The project follows an experiment-driven approach.

The first objective is not to build the complete application.

The first objective is to determine whether real traffic signal observations contain enough information to make useful predictions.

Development therefore starts with:

1. Data source research
2. Traffic signal mapping
3. Observation collection
4. Dataset creation
5. Baseline prediction
6. Machine learning
7. Backend
8. Mobile application

## Documentation

- [Project Analysis](docs/project-analysis.md)

The project analysis contains the project's assumptions, risks, research hypothesis, success criteria, and development plan.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.