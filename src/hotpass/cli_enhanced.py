"""Enhanced CLI commands for orchestration and entity resolution features.

This module extends the Hotpass CLI with commands for:
- Running the pipeline with Prefect orchestration
- Entity resolution with Splink
- Launching the monitoring dashboard
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console


def build_enhanced_parser() -> argparse.ArgumentParser:
    """Build parser for enhanced CLI commands.

    Returns:
        ArgumentParser with orchestration and entity resolution commands
    """
    parser = argparse.ArgumentParser(
        prog="hotpass-enhanced",
        description="Enhanced Hotpass commands for orchestration and entity resolution",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Orchestrate command
    orchestrate = subparsers.add_parser(
        "orchestrate",
        help="Run pipeline with Prefect orchestration and enhanced features",
    )
    orchestrate.add_argument(
        "--input-dir",
        type=Path,
        default=Path("./data"),
        help="Directory containing input Excel files",
    )
    orchestrate.add_argument(
        "--output-path",
        type=Path,
        default=Path("./data/refined_data.xlsx"),
        help="Path for output file",
    )
    orchestrate.add_argument(
        "--profile",
        default="aviation",
        help="Industry profile to use",
    )
    orchestrate.add_argument(
        "--chunk-size",
        type=int,
        help="Excel chunk size for large files",
    )
    orchestrate.add_argument(
        "--archive",
        action="store_true",
        help="Create packaged archive",
    )
    # Enhanced features flags
    orchestrate.add_argument(
        "--enable-entity-resolution",
        action="store_true",
        help="Enable entity resolution to deduplicate records",
    )
    orchestrate.add_argument(
        "--enable-geospatial",
        action="store_true",
        help="Enable geospatial enrichment (geocoding)",
    )
    orchestrate.add_argument(
        "--enable-enrichment",
        action="store_true",
        help="Enable external data enrichment (web scraping)",
    )
    orchestrate.add_argument(
        "--enable-compliance",
        action="store_true",
        help="Enable compliance tracking and PII detection",
    )
    orchestrate.add_argument(
        "--enable-observability",
        action="store_true",
        help="Enable OpenTelemetry observability",
    )
    orchestrate.add_argument(
        "--enable-all",
        action="store_true",
        help="Enable all enhanced features",
    )

    # Entity resolution command
    resolve = subparsers.add_parser(
        "resolve",
        help="Run entity resolution on existing data",
    )
    resolve.add_argument(
        "--input-file",
        type=Path,
        required=True,
        help="Input Excel/CSV file with potential duplicates",
    )
    resolve.add_argument(
        "--output-file",
        type=Path,
        required=True,
        help="Output file for deduplicated data",
    )
    resolve.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Match probability threshold (0.0-1.0)",
    )
    resolve.add_argument(
        "--use-splink",
        action="store_true",
        help="Use Splink for probabilistic matching (default: fallback)",
    )

    # Dashboard command
    dashboard = subparsers.add_parser(
        "dashboard",
        help="Launch monitoring dashboard",
    )
    dashboard.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port for Streamlit dashboard",
    )
    dashboard.add_argument(
        "--host",
        default="localhost",
        help="Host for dashboard server",
    )

    # Deploy command for Prefect
    deploy = subparsers.add_parser(
        "deploy",
        help="Deploy pipeline to Prefect",
    )
    deploy.add_argument(
        "--name",
        default="hotpass-refinement",
        help="Deployment name",
    )
    deploy.add_argument(
        "--schedule",
        help="Cron schedule (e.g., '0 2 * * *' for daily at 2am)",
    )
    deploy.add_argument(
        "--work-pool",
        help="Prefect work pool name",
    )

    return parser


def cmd_orchestrate(args: argparse.Namespace) -> int:
    """Execute orchestrated pipeline run with optional enhanced features.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from hotpass.config import get_default_profile
    from hotpass.data_sources import ExcelReadOptions
    from hotpass.pipeline import PipelineConfig
    from hotpass.pipeline_enhanced import EnhancedPipelineConfig, run_enhanced_pipeline

    console = Console()

    # Check if enhanced features are enabled
    enable_enhanced = (
        args.enable_all
        or args.enable_entity_resolution
        or args.enable_geospatial
        or args.enable_enrichment
        or args.enable_compliance
        or args.enable_observability
    )

    if enable_enhanced:
        console.print("[bold blue]Running enhanced pipeline with advanced features...[/bold blue]")
    else:
        console.print("[bold blue]Running orchestrated pipeline with Prefect...[/bold blue]")

    try:
        # Load profile and create config
        profile = get_default_profile(args.profile)
        config = PipelineConfig(
            input_dir=args.input_dir,
            output_path=args.output_path,
            industry_profile=profile,
            excel_options=ExcelReadOptions(chunk_size=args.chunk_size),
        )

        if enable_enhanced:
            # Use enhanced pipeline
            enhanced_config = EnhancedPipelineConfig(
                enable_entity_resolution=args.enable_all or args.enable_entity_resolution,
                enable_geospatial=args.enable_all or args.enable_geospatial,
                enable_enrichment=args.enable_all or args.enable_enrichment,
                enable_compliance=args.enable_all or args.enable_compliance,
                enable_observability=args.enable_all or args.enable_observability,
                geocode_addresses=args.enable_all or args.enable_geospatial,
                enrich_websites=args.enable_all or args.enable_enrichment,
                detect_pii=args.enable_all or args.enable_compliance,
            )

            result = run_enhanced_pipeline(config, enhanced_config)

            # Handle archiving if requested
            if args.archive:
                from hotpass.artifacts import create_refined_archive

                console.print("[blue]Creating archive...[/blue]")
                archive_path = create_refined_archive(
                    excel_path=config.output_path,
                    archive_dir=Path("./dist"),
                )
                console.print(f"Archive created: {archive_path}")

            if result.quality_report.expectations_passed:
                console.print("[bold green]✓[/bold green] Pipeline completed successfully!")
                console.print(f"  Records processed: {len(result.refined)}")
                if "total_seconds" in result.performance_metrics:
                    console.print(f"  Duration: {result.performance_metrics['total_seconds']:.2f}s")
                return 0
            else:
                console.print(
                    "[bold yellow]⚠[/bold yellow] Pipeline completed with validation warnings"
                )
                return 1
        else:
            # Use original Prefect orchestration
            from hotpass.orchestration import refinement_pipeline_flow

            flow_result = refinement_pipeline_flow(
                input_dir=str(args.input_dir),
                output_path=str(args.output_path),
                profile_name=args.profile,
                excel_chunk_size=args.chunk_size,
                archive=args.archive,
            )

            if flow_result["success"]:
                console.print("[bold green]✓[/bold green] Pipeline completed successfully!")
                console.print(f"  Records processed: {flow_result['total_records']}")
                console.print(f"  Duration: {flow_result['elapsed_seconds']:.2f}s")
                return 0
            else:
                console.print(
                    "[bold yellow]⚠[/bold yellow] Pipeline completed with validation warnings"
                )
                return 1

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Pipeline failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def cmd_resolve(args: argparse.Namespace) -> int:
    """Execute entity resolution.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    import pandas as pd

    from hotpass.entity_resolution import resolve_entities_fallback, resolve_entities_with_splink

    console = Console()
    console.print("[bold blue]Running entity resolution...[/bold blue]")

    try:
        # Load input data
        if args.input_file.suffix == ".csv":
            df = pd.read_csv(args.input_file)
        else:
            df = pd.read_excel(args.input_file)

        console.print(f"Loaded {len(df)} records from {args.input_file}")

        # Resolve entities
        if args.use_splink:
            deduplicated, predictions = resolve_entities_with_splink(df, args.threshold)
        else:
            deduplicated, predictions = resolve_entities_fallback(df, args.threshold)

        # Save output
        if args.output_file.suffix == ".csv":
            deduplicated.to_csv(args.output_file, index=False)
        else:
            deduplicated.to_excel(args.output_file, index=False, engine="openpyxl")

        duplicates_removed = len(df) - len(deduplicated)
        console.print("[bold green]✓[/bold green] Entity resolution complete!")
        console.print(f"  Original records: {len(df)}")
        console.print(f"  Deduplicated records: {len(deduplicated)}")
        console.print(f"  Duplicates removed: {duplicates_removed}")
        console.print(f"  Output saved to: {args.output_file}")

        return 0

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Entity resolution failed: {e}")
        return 1


def cmd_dashboard(args: argparse.Namespace) -> int:
    """Launch the monitoring dashboard.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    import subprocess
    from pathlib import Path

    console = Console()
    console.print("[bold blue]Launching Hotpass dashboard...[/bold blue]")

    dashboard_path = Path(__file__).parent / "dashboard.py"

    try:
        subprocess.run(
            [
                "streamlit",
                "run",
                str(dashboard_path),
                "--server.port",
                str(args.port),
                "--server.address",
                args.host,
            ],
            check=True,
        )
        return 0
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]✗[/bold red] Dashboard failed to start: {e}")
        return 1
    except FileNotFoundError:
        console.print(
            "[bold red]✗[/bold red] Streamlit not found. Install with: uv sync --extra dashboards"
        )
        return 1


def cmd_deploy(args: argparse.Namespace) -> int:
    """Deploy pipeline to Prefect.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from hotpass.orchestration import deploy_pipeline

    console = Console()
    console.print("[bold blue]Deploying pipeline to Prefect...[/bold blue]")

    try:
        deploy_pipeline(
            name=args.name,
            cron_schedule=args.schedule,
            work_pool=args.work_pool,
        )
        console.print("[bold green]✓[/bold green] Pipeline deployed successfully!")
        return 0
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Deployment failed: {e}")
        return 1


def main(argv: list[str] | None = None) -> int:
    """Main entry point for enhanced CLI.

    Args:
        argv: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code
    """
    parser = build_enhanced_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    # Dispatch to command handlers
    commands = {
        "orchestrate": cmd_orchestrate,
        "resolve": cmd_resolve,
        "dashboard": cmd_dashboard,
        "deploy": cmd_deploy,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
