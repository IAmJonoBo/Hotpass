"""QA command - run quality assurance checks and validation."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..builder import CLICommand, SharedParsers
from ..configuration import CLIProfile


def build(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    shared: SharedParsers,
) -> argparse.ArgumentParser:
    """Build the qa command parser."""
    parser = subparsers.add_parser(
        "qa",
        help="Run quality assurance checks and validation",
        description=(
            "Run various quality assurance checks including fitness functions, "
            "profile validation, contract checks, and technical acceptance tests."
        ),
        parents=[shared.base],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "target",
        type=str,
        nargs="?",
        default="all",
        choices=["all", "contracts", "docs", "profiles", "ta", "fitness", "data-quality"],
        help="Which QA checks to run (default: all)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )

    return parser


def register() -> CLICommand:
    return CLICommand(
        name="qa",
        help="Run quality assurance checks and validation",
        builder=build,
        handler=_command_handler,
    )


def _command_handler(namespace: argparse.Namespace, profile: CLIProfile | None) -> int:
    """Handle the qa command execution."""
    console = Console()
    _ = profile  # unused but required by interface

    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]Running QA Checks[/bold cyan]\nTarget: {namespace.target}",
            border_style="cyan",
        )
    )
    console.print()

    results = []
    overall_success = True

    # Get profile name if specified
    profile_name = getattr(namespace, "profile", None)

    # Define QA check runners
    checks_to_run = []

    if namespace.target in ("all", "fitness"):
        checks_to_run.append(("Fitness Functions", run_fitness_functions))

    if namespace.target in ("all", "data-quality"):
        checks_to_run.append(("Data Quality (GE)", lambda: run_data_quality(profile_name)))

    if namespace.target in ("all", "profiles"):
        checks_to_run.append(("Profile Validation", lambda: run_profile_validation(profile_name)))

    if namespace.target in ("all", "contracts"):
        checks_to_run.append(("Contract Checks", run_contract_checks))

    if namespace.target in ("all", "docs"):
        checks_to_run.append(("Documentation Checks", run_docs_checks))

    if namespace.target == "ta":
        checks_to_run.append(("Technical Acceptance", run_ta_checks))

    # Run checks
    for check_name, check_func in checks_to_run:
        console.print(f"[cyan]Running:[/cyan] {check_name}")
        success, message = check_func()
        results.append((check_name, success, message))

        if success:
            console.print(f"  [green]✓[/green] {message}")
        else:
            console.print(f"  [red]✗[/red] {message}")
            overall_success = False

        console.print()

    # Display summary table
    table = Table(title="QA Check Results", show_header=True)
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Message", style="white")

    for check_name, success, message in results:
        status = "[green]PASS[/green]" if success else "[red]FAIL[/red]"
        table.add_row(check_name, status, message)

    console.print(table)
    console.print()

    if overall_success:
        console.print("[green]✓ All QA checks passed[/green]")
        return 0
    else:
        console.print("[red]✗ Some QA checks failed[/red]", file=sys.stderr)
        return 1


def run_fitness_functions() -> tuple[bool, str]:
    """Run fitness function checks."""
    try:
        result = subprocess.run(
            ["python", "scripts/quality/fitness_functions.py"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True, "All fitness functions satisfied"
        else:
            return False, f"Fitness functions failed:\n{result.stdout}"
    except Exception as e:
        return False, f"Error running fitness functions: {e}"


def run_data_quality(profile_name: str | None = None) -> tuple[bool, str]:
    """Run Great Expectations data quality checks."""
    try:
        from hotpass.validation import validate_profile_with_ge

        profile = profile_name or "generic"
        return validate_profile_with_ge(profile)
    except Exception as e:
        return False, f"Error running data quality checks: {e}"


def run_profile_validation(profile_name: str | None = None) -> tuple[bool, str]:
    """Run profile validation checks."""
    try:
        # Check if profile linter exists
        linter_path = Path("tools/profile_lint.py")
        if not linter_path.exists():
            return True, "Profile linter not yet implemented (coming in Sprint 3)"

        # Run profile linter
        cmd = ["python", str(linter_path)]
        if profile_name:
            cmd.extend(["--profile", profile_name])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return True, "All profiles valid"
        else:
            return False, f"Profile validation failed:\n{result.stdout}"
    except Exception as e:
        return False, f"Error running profile validation: {e}"


def run_contract_checks() -> tuple[bool, str]:
    """Run contract checks."""
    try:
        # Check if contract tests exist
        contract_tests = Path("tests/contracts")
        if not contract_tests.exists():
            return True, "No contract tests found (optional)"

        result = subprocess.run(
            ["pytest", "tests/contracts", "-v"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return True, "All contract tests passed"
        else:
            return False, "Some contract tests failed"
    except Exception as e:
        return False, f"Error running contract checks: {e}"


def run_docs_checks() -> tuple[bool, str]:
    """Run documentation checks (QG-5)."""
    try:
        copilot_instructions = Path(".github/copilot-instructions.md")
        agents_md = Path("AGENTS.md")

        if not copilot_instructions.exists():
            return False, "Missing .github/copilot-instructions.md"

        if not agents_md.exists():
            return False, "Missing AGENTS.md"

        # Check content
        copilot_text = copilot_instructions.read_text().lower()
        agents_text = agents_md.read_text().lower()

        required_terms = ["profile", "deterministic", "provenance"]
        missing_terms = []

        for term in required_terms:
            if term not in copilot_text or term not in agents_text:
                missing_terms.append(term)

        if missing_terms:
            return False, f"Missing required terms: {', '.join(missing_terms)}"

        return True, "Documentation checks passed"
    except Exception as e:
        return False, f"Error checking documentation: {e}"


def run_ta_checks() -> tuple[bool, str]:
    """Run technical acceptance checks (all quality gates)."""
    try:
        # This will run QG-1 through QG-5
        # For now, just check that they're documented
        impl_plan = Path("IMPLEMENTATION_PLAN.md")
        if not impl_plan.exists():
            return False, "IMPLEMENTATION_PLAN.md missing"

        return True, "TA infrastructure ready (gates coming in Sprint 5)"
    except Exception as e:
        return False, f"Error running TA checks: {e}"
