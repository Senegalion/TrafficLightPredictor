# Traffic Light Predictor

**Building AI course project**

## Summary

Traffic Light Predictor is an AI-based project that aims to predict traffic signal phases and estimate the time until the next phase change in Łódź, Poland. It explores how historical observations and machine learning could help drivers better anticipate traffic lights.

## Background

Drivers approaching traffic-light-controlled intersections often do not know how long the current signal phase will last. For example, when approaching a green light, they cannot easily determine whether it will remain green for several seconds or change shortly.

Traffic Light Predictor aims to address this problem by estimating the current traffic signal phase and predicting the approximate time until the next phase change.

The initial project scope focuses on Łódź, Poland.

The motivation behind this project is to explore how artificial intelligence and data analysis can be applied to everyday urban mobility challenges. Better predictions could help drivers make more informed decisions while approaching intersections.

## How is it used?

The planned solution is intended primarily for drivers approaching traffic-light-controlled intersections.

The proposed workflow is:

1. The mobile application determines the driver's location using GPS.
2. The system identifies the upcoming intersection and relevant traffic signal.
3. Available historical observations and contextual information are retrieved.
4. A prediction model estimates the current signal phase and the time until the next phase change.
5. The application presents the estimated phase, remaining time and prediction confidence.

For example, the application could display:

- Current phase: GREEN
- Estimated time until change: approximately 12 seconds
- Prediction confidence: 87%

These values are illustrative examples, not results from a deployed model.

If the system cannot make a sufficiently reliable prediction, it should clearly communicate that the prediction is unavailable.

The application is intended as a driver assistance tool. It must never encourage speeding, dangerous braking or ignoring traffic regulations. Predictions should always be treated as estimates, not guarantees.

## Data sources and AI methods

The project depends on collecting and analysing traffic signal observations and contextual data.

Potential data sources include:

- **OpenStreetMap:** static road infrastructure, traffic signal locations, intersections and road geometry.
- **Open Data Łódź:** potentially useful transport, public infrastructure and spatial datasets.
- **Own observations:** collected traffic signal phases, timestamps, GPS positions, intersection identifiers and travel directions.
- **Additional contextual data:** time of day, day of the week, weather and traffic volume, where available.

One of the main challenges is the availability of reliable historical or real-time traffic signal phase data. Some observations may need to be collected independently.

Potential AI and data analysis methods include:

- Statistical baseline models based on historical signal phase durations.
- Supervised machine learning for predicting the next traffic signal phase.
- Regression models for estimating the remaining duration of a signal phase.
- Computer vision as a potential future method for detecting traffic light colours from camera images.

The models could be evaluated using Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), phase classification accuracy and prediction confidence.

Machine learning will only be introduced after collecting and validating a sufficiently reliable dataset.

## Challenges

The project has several important limitations and challenges:

- **Data availability:** reliable traffic signal phase and timing datasets may not be publicly available.
- **Data quality:** observations may be incomplete, inconsistent or inaccurate.
- **Changing traffic conditions:** signal timing may depend on traffic volume, pedestrian crossings, public transport and other factors.
- **Prediction uncertainty:** the system cannot guarantee that a predicted phase change will happen at the estimated time.
- **Safety:** incorrect predictions must not encourage unsafe driving decisions.
- **Scalability:** different intersections and cities may use different traffic signal configurations.

The system must be able to communicate uncertainty and avoid presenting unreliable predictions as facts.

## What next?

The project will follow an experiment-driven development approach.

The planned development stages are:

1. Investigate available traffic and infrastructure data sources.
2. Identify and map selected traffic-light-controlled intersections in Łódź.
3. Collect and analyse traffic signal observations.
4. Build an initial dataset.
5. Implement a statistical baseline model.
6. Experiment with machine learning models.
7. Evaluate prediction quality using appropriate metrics.
8. Develop a backend API and geospatial data service.
9. Build an Android application.
10. Test the solution in real-world conditions.

In the future, the project could be expanded to other cities, incorporate crowdsourced observations, use computer vision and integrate with Android Auto.

## Acknowledgments

- [Elements of AI – Building AI](https://buildingai.elementsofai.com/) – educational material and inspiration for this project.
- [OpenStreetMap](https://www.openstreetmap.org/) – potential source of geographical and road infrastructure data.
- [Open Data Łódź](https://uml.lodz.pl/) – potential source of local public datasets.

This project is an independent educational initiative. External datasets, software and other materials will be credited according to their respective licences and terms of use.

## Project Status

Research & Development.

The project is currently focused on data acquisition, feasibility validation and research into potential prediction methods.

## Documentation

For a more detailed technical analysis, research hypothesis, risks, evaluation criteria and development plan, see [Project Analysis](docs/project-analysis.md).
