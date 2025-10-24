"""Prefect-based orchestration for Hotpass pipeline.

This module provides workflow orchestration using Prefect, enabling:
- Task-based pipeline execution with automatic retries and error handling
- Logging and metrics collection via OpenTelemetry
- Configurable scheduling and monitoring
- State persistence and recovery
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from prefect import flow, task
from prefect.logging import get_run_logger

from .artifacts import create_refined_archive
from .config import get_default_profile
from .data_sources import ExcelReadOptions
from .pipeline import PipelineConfig, run_pipeline


@task(name="run-pipeline", retries=2, retry_delay_seconds=10)
def run_pipeline_task(
    config: PipelineConfig,
) -> dict[str, Any]:
    """Run the Hotpass pipeline as a Prefect task.

    Args:
        config: Pipeline configuration

    Returns:
        Pipeline execution results
    """
    logger = get_run_logger()
    logger.info(f"Running pipeline with input_dir={config.input_dir}")

    start_time = time.time()

    result = run_pipeline(config)

    elapsed = time.time() - start_time

    logger.info(
        f"Pipeline completed in {elapsed:.2f} seconds - "
        f"{len(result.refined)} organizations processed"
    )

    return {
        "success": result.quality_report.expectations_passed,
        "total_records": len(result.refined),
        "elapsed_seconds": elapsed,
        "quality_report": result.quality_report.to_dict(),
        "output_path": str(config.output_path),
    }


@flow(name="hotpass-refinement-pipeline", log_prints=True, validate_parameters=False)
def refinement_pipeline_flow(
    input_dir: str = "./data",
    output_path: str = "./data/refined_data.xlsx",
    profile_name: str = "aviation",
    excel_chunk_size: int | None = None,
    archive: bool = False,
    dist_dir: str = "./dist",
) -> dict[str, Any]:
    """Main Hotpass refinement pipeline as a Prefect flow.

    Args:
        input_dir: Directory containing input Excel files
        output_path: Path for the output refined workbook
        profile_name: Name of the industry profile to use
        excel_chunk_size: Optional chunk size for Excel reading
        archive: Whether to create a packaged archive
        dist_dir: Directory for archive output

    Returns:
        Pipeline execution results dictionary
    """
    logger = get_run_logger()
    logger.info(f"Starting Hotpass refinement pipeline (profile: {profile_name})")

    # Load the profile
    profile = get_default_profile(profile_name)

    # Build configuration
    config = PipelineConfig(
        input_dir=Path(input_dir),
        output_path=Path(output_path),
        industry_profile=profile,
        excel_options=ExcelReadOptions(chunk_size=excel_chunk_size),
    )

    # Handle archive settings manually since PipelineConfig doesn't have these fields
    # We'll need to call archiving separately if needed

    # Execute pipeline
    result = run_pipeline_task(config)

    # Handle archiving if requested
    if archive:
        logger.info("Creating archive from output file...")
        try:
            archive_dir = Path(dist_dir)
            archive_dir.mkdir(parents=True, exist_ok=True)
            archive_path = create_refined_archive(
                excel_path=Path(result["output_path"]),
                archive_dir=archive_dir,
            )
            logger.info(f"Archive created: {archive_path}")
            result["archive_path"] = str(archive_path)
        except Exception as e:
            logger.error(f"Failed to create archive: {e}")
            # Don't fail the entire flow for archiving errors
            result["archive_error"] = str(e)

    logger.info(
        f"Pipeline flow completed - "
        f"Status: {'SUCCESS' if result['success'] else 'VALIDATION_FAILED'}"
    )

    return result


def deploy_pipeline(
    name: str = "hotpass-refinement",
    cron_schedule: str | None = None,
    work_pool: str | None = None,
) -> None:
    """Deploy the Hotpass pipeline to Prefect.

    Args:
        name: Deployment name
        cron_schedule: Optional cron schedule (e.g., "0 2 * * *" for daily at 2am)
        work_pool: Optional work pool name for execution
    """
    from prefect.deployments import serve

    # Note: deployment API may require adjustments based on Prefect version
    deployment = refinement_pipeline_flow.to_deployment(name=name)
    if work_pool:
        deployment.work_pool_name = work_pool  # type: ignore

    serve(deployment)  # type: ignore


if __name__ == "__main__":
    # Run the flow directly for testing
    result = refinement_pipeline_flow()
    print(f"\nPipeline execution result: {result}")
