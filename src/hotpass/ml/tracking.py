"""MLflow tracking and model registry integration for lead scoring models."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd


class ModelStage(str, Enum):
    """Valid stages for model promotion in the registry."""

    NONE = "None"
    STAGING = "Staging"
    PRODUCTION = "Production"
    ARCHIVED = "Archived"


@dataclass
class MLflowConfig:
    """Configuration for MLflow tracking and registry."""

    tracking_uri: str = "sqlite:///mlflow.db"
    experiment_name: str = "lead_scoring"
    registry_uri: str | None = None
    artifact_location: str | None = None

    @classmethod
    def from_env(cls) -> MLflowConfig:
        """Load configuration from environment variables."""
        return cls(
            tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"),
            experiment_name=os.getenv("MLFLOW_EXPERIMENT_NAME", "lead_scoring"),
            registry_uri=os.getenv("MLFLOW_REGISTRY_URI"),
            artifact_location=os.getenv("MLFLOW_ARTIFACT_LOCATION"),
        )


def init_mlflow(config: MLflowConfig | None = None) -> None:
    """Initialize MLflow tracking with the specified configuration."""
    try:
        import mlflow
    except ImportError as exc:  # pragma: no cover
        msg = (
            "mlflow is required for model tracking. Install the 'ml_scoring' extra "
            "(pip install hotpass[ml_scoring])."
        )
        raise RuntimeError(msg) from exc

    if config is None:
        config = MLflowConfig.from_env()

    mlflow.set_tracking_uri(config.tracking_uri)
    if config.registry_uri:
        mlflow.set_registry_uri(config.registry_uri)

    # Create experiment if it doesn't exist
    experiment = mlflow.get_experiment_by_name(config.experiment_name)
    if experiment is None:
        kwargs = {}
        if config.artifact_location:
            kwargs["artifact_location"] = config.artifact_location
        mlflow.create_experiment(config.experiment_name, **kwargs)

    mlflow.set_experiment(config.experiment_name)


def log_training_run(
    *,
    model: Any,
    params: Mapping[str, Any],
    metrics: Mapping[str, float],
    metadata: Mapping[str, Any],
    artifacts: Mapping[str, Path] | None = None,
    model_name: str = "lead_scoring_model",
    signature: Any = None,
    input_example: pd.DataFrame | None = None,
    run_name: str | None = None,
) -> str:
    """
    Log a training run with MLflow, including model, params, metrics, and artifacts.

    Returns the run ID of the logged run.
    """
    try:
        import mlflow
        from mlflow.models import infer_signature
    except ImportError as exc:  # pragma: no cover
        msg = (
            "mlflow is required for model tracking. Install the 'ml_scoring' extra "
            "(pip install hotpass[ml_scoring])."
        )
        raise RuntimeError(msg) from exc

    if run_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"{model_name}_{timestamp}"

    with mlflow.start_run(run_name=run_name) as run:
        # Log parameters
        mlflow.log_params(params)

        # Log metrics
        mlflow.log_metrics(metrics)

        # Log metadata as tags
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                mlflow.set_tag(key, value)
            elif isinstance(value, (list, tuple)):
                mlflow.set_tag(key, str(value))

        # Infer signature if not provided
        if signature is None and input_example is not None:
            try:
                predictions = model.predict(input_example)
                signature = infer_signature(input_example, predictions)
            except Exception:  # pragma: no cover
                # Signature inference is best-effort
                pass

        # Log the model
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            registered_model_name=model_name,
            signature=signature,
            input_example=input_example,
        )

        # Log additional artifacts
        if artifacts:
            for name, path in artifacts.items():
                if path.exists():
                    if path.is_file():
                        mlflow.log_artifact(str(path), artifact_path=name)
                    else:
                        mlflow.log_artifacts(str(path), artifact_path=name)

        return run.info.run_id


def promote_model(
    *,
    model_name: str,
    version: int | str,
    stage: ModelStage,
    archive_existing: bool = True,
) -> None:
    """
    Promote a model version to a specific stage in the registry.

    Args:
        model_name: Name of the registered model
        version: Version number or "latest" to promote
        stage: Target stage for promotion
        archive_existing: Whether to archive existing models in the target stage
    """
    try:
        import mlflow
        from mlflow.exceptions import MlflowException
    except ImportError as exc:  # pragma: no cover
        msg = (
            "mlflow is required for model tracking. Install the 'ml_scoring' extra "
            "(pip install hotpass[ml_scoring])."
        )
        raise RuntimeError(msg) from exc

    client = mlflow.MlflowClient()

    # Resolve version if "latest"
    if isinstance(version, str) and version.lower() == "latest":
        versions = client.search_model_versions(f"name='{model_name}'")
        if not versions:
            msg = f"No versions found for model '{model_name}'"
            raise ValueError(msg)
        version = max(int(v.version) for v in versions)

    version_str = str(version)

    # Archive existing models in the target stage if requested
    if archive_existing and stage not in (ModelStage.NONE, ModelStage.ARCHIVED):
        try:
            existing = client.get_latest_versions(model_name, stages=[stage.value])
            for existing_version in existing:
                client.transition_model_version_stage(
                    name=model_name,
                    version=existing_version.version,
                    stage=ModelStage.ARCHIVED.value,
                )
        except MlflowException:
            # No existing versions in this stage
            pass

    # Transition the specified version to the target stage
    client.transition_model_version_stage(
        name=model_name,
        version=version_str,
        stage=stage.value,
    )


def load_production_model(model_name: str = "lead_scoring_model") -> Any:
    """
    Load the production model from the registry.

    Returns:
        The loaded model ready for inference.
    """
    try:
        import mlflow
    except ImportError as exc:  # pragma: no cover
        msg = (
            "mlflow is required for model tracking. Install the 'ml_scoring' extra "
            "(pip install hotpass[ml_scoring])."
        )
        raise RuntimeError(msg) from exc

    model_uri = f"models:/{model_name}/Production"
    return mlflow.sklearn.load_model(model_uri)


def get_model_metadata(model_name: str, stage: ModelStage | None = None) -> list[dict]:
    """
    Retrieve metadata for model versions in the registry.

    Args:
        model_name: Name of the registered model
        stage: Optional stage filter (e.g., Production, Staging)

    Returns:
        List of model version metadata dictionaries
    """
    try:
        import mlflow
    except ImportError as exc:  # pragma: no cover
        msg = (
            "mlflow is required for model tracking. Install the 'ml_scoring' extra "
            "(pip install hotpass[ml_scoring])."
        )
        raise RuntimeError(msg) from exc

    client = mlflow.MlflowClient()

    if stage:
        versions = client.get_latest_versions(model_name, stages=[stage.value])
    else:
        versions = client.search_model_versions(f"name='{model_name}'")

    return [
        {
            "version": v.version,
            "stage": v.current_stage,
            "run_id": v.run_id,
            "creation_timestamp": v.creation_timestamp,
            "last_updated_timestamp": v.last_updated_timestamp,
        }
        for v in versions
    ]


__all__ = [
    "MLflowConfig",
    "ModelStage",
    "init_mlflow",
    "log_training_run",
    "promote_model",
    "load_production_model",
    "get_model_metadata",
]
