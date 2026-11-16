# syntax=docker/dockerfile:1

# ---- build: install, generate the SYNTHETIC dataset and train the model ----
FROM python:3.12-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 TLP_LOG_FORMAT=text
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .
# Deterministic: fixed seed and end date (see `tlp-ml generate-data --help`).
RUN tlp-ml generate-data --out /build/data/observations.csv \
 && tlp-ml train --data /build/data/observations.csv --artifacts /opt/model --reports /opt/reports

# ---- runtime ----
FROM python:3.12-slim
RUN groupadd --system app && useradd --system --gid app app
COPY --from=build /opt/venv /opt/venv
COPY --from=build /opt/model /opt/model
COPY --from=build /opt/reports /opt/reports
ENV PATH="/opt/venv/bin:$PATH" \
    TLP_ML_ARTIFACTS_DIR=/opt/model \
    TLP_ML_HOST=0.0.0.0 \
    TLP_ML_PORT=8000 \
    PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request,json,sys; sys.exit(0 if json.load(urllib.request.urlopen('http://localhost:8000/health'))['model_loaded'] else 1)"
CMD ["tlp-ml", "serve"]
