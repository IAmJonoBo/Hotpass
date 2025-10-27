"""Compatibility shim for the legacy `hotpass-enhanced` entry point."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence

from hotpass.cli import build_parser as _build_parser
from hotpass.cli import main as _cli_main

_DEPRECATION_MESSAGE = (
    "hotpass-enhanced is deprecated. Use `hotpass` with subcommands instead (for example, "
    "`hotpass run` or `hotpass orchestrate`)."
)


def build_enhanced_parser() -> object:
    """Return the unified CLI parser for backwards compatibility."""

    return _build_parser()


def main(argv: Sequence[str] | None = None) -> int:
    """Delegate to the unified CLI after emitting a deprecation warning."""

    print(_DEPRECATION_MESSAGE, file=sys.stderr)
    normalised = list(argv) if argv is not None else None
    return _UNIFIED_ENTRYPOINT(normalised)


_UNIFIED_ENTRYPOINT: Callable[[Sequence[str] | None], int] = _cli_main

def cmd_orchestrate(args: argparse.Namespace) -> int:
    """Execute orchestrated pipeline run with optional enhanced features.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
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
        runner = None
        runner_kwargs: dict[str, object] | None = None

        match_threshold = max(args.linkage_match_threshold, args.linkage_review_threshold)
        review_threshold = args.linkage_review_threshold
        label_studio_config = None
        label_studio_args = (
            args.label_studio_url,
            args.label_studio_token,
            args.label_studio_project,
        )
        if any(value is not None for value in label_studio_args):
            if not (
                args.label_studio_url and args.label_studio_token and args.label_studio_project
            ):
                warning = (
                    "[bold yellow]⚠[/bold yellow] Label Studio options require URL, token, "
                    "and project ID"
                )
                console.print(warning)
            else:
                label_studio_config = LabelStudioConfig(
                    api_url=args.label_studio_url,
                    api_token=args.label_studio_token,
                    project_id=args.label_studio_project,
                )

        if enable_enhanced:
            linkage_thresholds = LinkageThresholds(high=match_threshold, review=review_threshold)
            linkage_config = LinkageConfig(
                use_splink=args.linkage_use_splink or args.enable_all,
                thresholds=linkage_thresholds,
                label_studio=label_studio_config,
            )
            enhanced_config = EnhancedPipelineConfig(
                enable_entity_resolution=args.enable_all or args.enable_entity_resolution,
                enable_geospatial=args.enable_all or args.enable_geospatial,
                enable_enrichment=args.enable_all or args.enable_enrichment,
                enable_compliance=args.enable_all or args.enable_compliance,
                enable_observability=args.enable_all or args.enable_observability,
                geocode_addresses=args.enable_all or args.enable_geospatial,
                enrich_websites=args.enable_all or args.enable_enrichment,
                detect_pii=args.enable_all or args.enable_compliance,
                entity_resolution_threshold=review_threshold,
                use_splink=args.linkage_use_splink or args.enable_all,
                linkage_config=linkage_config,
                linkage_output_dir=str(args.linkage_output_dir)
                if args.linkage_output_dir
                else None,
                linkage_match_threshold=match_threshold,
                telemetry_attributes={
                    "hotpass.profile": args.profile or "default",
                    "hotpass.command": "hotpass-enhanced orchestrate",
                },
            )
            runner = run_enhanced_pipeline
            runner_kwargs = {"enhanced_config": enhanced_config}

        summary = run_pipeline_once(
            PipelineRunOptions(
                input_dir=args.input_dir,
                output_path=args.output_path,
                profile_name=args.profile,
                excel_chunk_size=args.chunk_size,
                archive=args.archive,
                archive_dir=Path("./dist") if args.archive else None,
                runner=runner,
                runner_kwargs=runner_kwargs,
            )
        )
    except PipelineOrchestrationError as exc:
        console.print(f"[bold red]✗[/bold red] Pipeline failed: {exc}")
        return 1
    finally:
        try:
            from hotpass.observability import shutdown_observability

            shutdown_observability()
        except ModuleNotFoundError:
            pass

    if summary.success:
        console.print("[bold green]✓[/bold green] Pipeline completed successfully!")
        console.print(f"  Records processed: {summary.total_records}")
        console.print(f"  Duration: {summary.elapsed_seconds:.2f}s")
        if summary.archive_path:
            console.print(f"  Archive: {summary.archive_path}")
        return 0

    console.print("[bold yellow]⚠[/bold yellow] Pipeline completed with validation warnings")
    return 1


def cmd_resolve(args: argparse.Namespace) -> int:
    """Execute entity resolution.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    import pandas as pd

    console = Console()
    console.print("[bold blue]Running entity resolution...[/bold blue]")

    try:
        # Load input data
        if args.input_file.suffix == ".csv":
            df = pd.read_csv(args.input_file)
        else:
            df = pd.read_excel(args.input_file)

        console.print(f"Loaded {len(df)} records from {args.input_file}")

        review_threshold = args.review_threshold or args.threshold
        match_threshold = max(args.match_threshold, review_threshold)
        label_studio_config = None
        label_studio_args = (
            args.label_studio_url,
            args.label_studio_token,
            args.label_studio_project,
        )
        if any(value is not None for value in label_studio_args):
            if not (
                args.label_studio_url and args.label_studio_token and args.label_studio_project
            ):
                warning = (
                    "[bold yellow]⚠[/bold yellow] Label Studio options require URL, token, "
                    "and project ID"
                )
                console.print(warning)
            else:
                label_studio_config = LabelStudioConfig(
                    api_url=args.label_studio_url,
                    api_token=args.label_studio_token,
                    project_id=args.label_studio_project,
                )

        thresholds = LinkageThresholds(high=match_threshold, review=review_threshold)
        linkage_config = LinkageConfig(
            use_splink=args.use_splink,
            thresholds=thresholds,
            label_studio=label_studio_config,
        ).with_output_root(args.output_file.parent / "linkage")

        linkage_result = link_entities(df, linkage_config)
        deduplicated = linkage_result.deduplicated
        predictions = linkage_result.matches

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
        match_count = int((predictions["classification"] == "match").sum())
        console.print(f"  High-confidence matches: {match_count}")
        review_count = len(linkage_result.review_queue)
        review_path = linkage_config.persistence.review_path()
        console.print(f"  Review queue: {review_count} pairs written to {review_path}")

        return 0

    except (
        FileNotFoundError,
        OSError,
        ValueError,
        pd.errors.ParserError,
        ImportError,
    ) as exc:
        console.print(f"[bold red]✗[/bold red] Entity resolution failed: {exc}")
        return 1


_SAFE_HOST_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def _normalise_dashboard_host(host: str) -> str | None:
    """Validate and normalise dashboard host values.

    The Streamlit runner ultimately binds a socket, so we restrict the host to
    valid DNS labels or IP literals to prevent shell-style injection when the
    value is later echoed back to logs.
    """

    candidate = host.strip()
    if not candidate:
        return None

    if candidate == "localhost":
        return "localhost"

    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        if _SAFE_HOST_PATTERN.fullmatch(candidate):
            return candidate
        return None
    else:
        return candidate


def _load_streamlit_runner() -> tuple[Callable[[list[str]], object] | None, str | None]:
    """Return the Streamlit CLI runner when available.

    Returns a tuple of (runner, error_message). When the runner cannot be
    resolved the error message contains a user-facing explanation.
    """

    try:
        streamlit_cli = importlib.import_module("streamlit.web.cli")
    except ModuleNotFoundError:
        return None, (
            "[bold red]✗[/bold red] Streamlit not found. Install with: uv sync --extra dashboards"
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        return None, (f"[bold red]✗[/bold red] Unable to load Streamlit CLI: {exc}")

    runner = getattr(streamlit_cli, "main_run", None)
    if runner is None:
        return None, (
            "[bold red]✗[/bold red] Streamlit CLI entrypoint missing. Upgrade Streamlit to ≥1.25."
        )

    return runner, None


def cmd_dashboard(args: argparse.Namespace) -> int:
    """Launch the monitoring dashboard.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """

    console = Console()
    console.print("[bold blue]Launching Hotpass dashboard...[/bold blue]")

    dashboard_path = Path(__file__).parent / "dashboard.py"
    if not dashboard_path.exists():  # pragma: no cover - defensive guard
        console.print(f"[bold red]✗[/bold red] Dashboard entrypoint missing at {dashboard_path}")
        return 1

    if not 0 < args.port < 65536:
        console.print(
            "[bold red]✗[/bold red] Invalid port. Provide an integer between 1 and 65535."
        )
        return 1

    host = _normalise_dashboard_host(args.host)
    if host is None:
        console.print("[bold red]✗[/bold red] Invalid host. Use localhost or a valid IP/DNS label.")
        return 1

    runner, error_message = _load_streamlit_runner()
    if runner is None:
        console.print(error_message)
        return 1

    command = [
        str(dashboard_path),
        "--server.port",
        str(args.port),
        "--server.address",
        host,
    ]

    try:
        runner(command)
    except SystemExit as exc:
        code = exc.code or 0
        if code != 0:
            console.print("[bold red]✗[/bold red] Dashboard exited with non-zero status.")
        return int(code)
    except Exception as exc:  # pragma: no cover - defensive guard
        console.print(f"[bold red]✗[/bold red] Dashboard failed to start: {exc}")
        return 1

    return 0


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
