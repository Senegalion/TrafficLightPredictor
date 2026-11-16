"""Command-line entry point: ``tlp-ml <command>``."""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from tlp_ml.logging_config import configure_logging

ML_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ML_ROOT / "data" / "synthetic" / "observations.csv"
DEFAULT_ARTIFACTS = ML_ROOT / "artifacts"
DEFAULT_REPORTS = ML_ROOT / "reports"
#: Fixed end date keeps the default synthetic dataset reproducible.
DEFAULT_DATASET_END = "2026-11-01T00:00:00+00:00"
DEFAULT_DATASET_DAYS = 28
DEFAULT_SEED = 42

log = logging.getLogger("tlp_ml")


def _generate(args: argparse.Namespace) -> None:
    from tlp_ml.data.dataset import save_observations
    from tlp_ml.simulation.plans import load_plans
    from tlp_ml.simulation.simulator import generate_observation_dataset

    dataset = generate_observation_dataset(
        load_plans(), datetime.fromisoformat(args.end), args.days, args.seed
    )
    save_observations(dataset, args.out)
    log.info("Synthetic dataset written", extra={"rows": len(dataset), "path": str(args.out)})


def _eda(args: argparse.Namespace) -> None:
    from tlp_ml.data.dataset import load_observations
    from tlp_ml.eda import summarise, write_eda_report

    observations, validation = load_observations(args.data)
    summary = summarise(observations, validation)
    write_eda_report(summary, args.reports / "eda.md")
    log.info("EDA report written", extra={"path": str(args.reports / "eda.md")})


def _train(args: argparse.Namespace) -> None:
    from tlp_ml.training import TrainingConfig, run_training

    report = run_training(
        TrainingConfig(
            data_path=args.data,
            artifacts_dir=args.artifacts,
            reports_dir=args.reports,
            seed=args.seed,
        )
    )
    metrics = report["metrics"]
    print(
        json.dumps(
            {
                "model_version": report["metadata"]["model_version"],
                "training_data_origin": report["metadata"]["training_data_origin"],
                "phase_accuracy": metrics["phase_classification"]["model"]["accuracy"],
                "baseline_phase_accuracy": metrics["phase_classification"]["cycle_baseline"][
                    "accuracy"
                ],
                "remaining_mae_s": metrics["remaining_time"]["model"]["mae_s"],
                "baseline_remaining_mae_s": metrics["remaining_time"]["cycle_baseline"]["mae_s"],
                "selective": metrics["selective"],
            },
            indent=2,
        )
    )


def _serve(args: argparse.Namespace) -> None:
    import uvicorn

    from tlp_ml.service.api import create_app

    uvicorn.run(create_app(args.artifacts), host=args.host, port=args.port, log_config=None)


def _feed(args: argparse.Namespace) -> None:
    from tlp_ml.feed import BackendClient, run_feed
    from tlp_ml.simulation.plans import load_plans

    client = BackendClient(args.backend_url, os.getenv("TLP_INGEST_API_KEY") or None)
    run_feed(
        load_plans(),
        client,
        backfill_s=args.backfill_minutes * 60,
        tick_s=args.tick_seconds,
        seed=args.seed,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tlp-ml", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate-data", help="Generate the SYNTHETIC observation dataset")
    gen.add_argument("--out", type=Path, default=DEFAULT_DATA)
    gen.add_argument("--days", type=int, default=DEFAULT_DATASET_DAYS)
    gen.add_argument("--end", default=DEFAULT_DATASET_END, help="ISO-8601 end timestamp")
    gen.add_argument("--seed", type=int, default=DEFAULT_SEED)
    gen.set_defaults(func=_generate)

    eda = sub.add_parser("eda", help="Write an exploratory data analysis report")
    eda.add_argument("--data", type=Path, default=DEFAULT_DATA)
    eda.add_argument("--reports", type=Path, default=DEFAULT_REPORTS)
    eda.set_defaults(func=_eda)

    train = sub.add_parser("train", help="Train, evaluate and save the model")
    train.add_argument("--data", type=Path, default=DEFAULT_DATA)
    train.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    train.add_argument("--reports", type=Path, default=DEFAULT_REPORTS)
    train.add_argument("--seed", type=int, default=DEFAULT_SEED)
    train.set_defaults(func=_train)

    serve = sub.add_parser("serve", help="Run the FastAPI prediction service")
    serve.add_argument(
        "--artifacts", type=Path, default=Path(os.getenv("TLP_ML_ARTIFACTS_DIR", DEFAULT_ARTIFACTS))
    )
    serve.add_argument("--host", default=os.getenv("TLP_ML_HOST", "127.0.0.1"))
    serve.add_argument("--port", type=int, default=int(os.getenv("TLP_ML_PORT", "8000")))
    serve.set_defaults(func=_serve)

    feed = sub.add_parser("simulate-feed", help="Post SIMULATED observations to the backend")
    feed.add_argument(
        "--backend-url", default=os.getenv("TLP_BACKEND_URL", "http://localhost:8080")
    )
    feed.add_argument(
        "--backfill-minutes", type=int, default=int(os.getenv("TLP_FEED_BACKFILL_MINUTES", "120"))
    )
    feed.add_argument("--tick-seconds", type=float, default=1.0)
    feed.add_argument("--seed", type=int, default=None)
    feed.set_defaults(func=_feed)
    return parser


def main(argv: list[str] | None = None) -> None:
    configure_logging()
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
