#!/usr/bin/env python
"""Master quality gate runner for Hotpass.

This script runs all quality gates (QG-1 through QG-5) and generates
a summary report. It can be used locally or in CI.

Usage:
    python scripts/quality/run_all_gates.py          # Run all gates
    python scripts/quality/run_all_gates.py --gate 1 # Run specific gate
    python scripts/quality/run_all_gates.py --json   # JSON output for CI
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class GateResult:
    """Result from running a quality gate."""

    gate_id: str
    name: str
    passed: bool
    message: str
    duration_seconds: float


def run_qg1_cli_integrity() -> GateResult:
    """QG-1: CLI Integrity Gate."""
    import time

    start = time.time()

    try:
        # Check that overview command works
        result = subprocess.run(
            ["uv", "run", "hotpass", "overview"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return GateResult(
                gate_id="QG-1",
                name="CLI Integrity",
                passed=False,
                message=f"overview command failed: {result.stderr}",
                duration_seconds=time.time() - start,
            )

        # Check that all required verbs are present
        required_verbs = ["refine", "enrich", "qa", "contracts", "overview"]
        output_lower = result.stdout.lower()

        missing_verbs = [verb for verb in required_verbs if verb not in output_lower]

        if missing_verbs:
            return GateResult(
                gate_id="QG-1",
                name="CLI Integrity",
                passed=False,
                message=f"Missing CLI verbs: {', '.join(missing_verbs)}",
                duration_seconds=time.time() - start,
            )

        return GateResult(
            gate_id="QG-1",
            name="CLI Integrity",
            passed=True,
            message="All CLI verbs present and functional",
            duration_seconds=time.time() - start,
        )

    except Exception as e:
        return GateResult(
            gate_id="QG-1",
            name="CLI Integrity",
            passed=False,
            message=f"Error running CLI integrity check: {e}",
            duration_seconds=time.time() - start,
        )


def run_qg2_data_quality() -> GateResult:
    """QG-2: Data Quality Gate."""
    import time

    start = time.time()

    # Note: Full Great Expectations integration would go here
    # For now, we check that profiles define expectations

    try:
        import yaml

        profile_path = Path("src/hotpass/profiles/aviation.yaml")
        with open(profile_path) as f:
            profile = yaml.safe_load(f)

        if "refine" not in profile or "expectations" not in profile["refine"]:
            return GateResult(
                gate_id="QG-2",
                name="Data Quality",
                passed=False,
                message="Profile missing expectations definition",
                duration_seconds=time.time() - start,
            )

        if len(profile["refine"]["expectations"]) == 0:
            return GateResult(
                gate_id="QG-2",
                name="Data Quality",
                passed=False,
                message="Profile has no expectations defined",
                duration_seconds=time.time() - start,
            )

        return GateResult(
            gate_id="QG-2",
            name="Data Quality",
            passed=True,
            message=f"Profiles define {len(profile['refine']['expectations'])} expectations",
            duration_seconds=time.time() - start,
        )

    except Exception as e:
        return GateResult(
            gate_id="QG-2",
            name="Data Quality",
            passed=False,
            message=f"Error checking data quality: {e}",
            duration_seconds=time.time() - start,
        )


def run_qg3_enrichment_chain() -> GateResult:
    """QG-3: Enrichment Chain Gate."""
    import time

    start = time.time()

    try:
        # Run enrichment pipeline tests
        result = subprocess.run(
            [
                "uv",
                "run",
                "pytest",
                "tests/enrichment/test_quality_gates.py::TestQG3EnrichmentChainGate",
                "-v",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            return GateResult(
                gate_id="QG-3",
                name="Enrichment Chain",
                passed=False,
                message=f"Enrichment tests failed: {result.stdout}",
                duration_seconds=time.time() - start,
            )

        return GateResult(
            gate_id="QG-3",
            name="Enrichment Chain",
            passed=True,
            message="Enrichment chain tests passed",
            duration_seconds=time.time() - start,
        )

    except Exception as e:
        return GateResult(
            gate_id="QG-3",
            name="Enrichment Chain",
            passed=False,
            message=f"Error running enrichment tests: {e}",
            duration_seconds=time.time() - start,
        )


def run_qg4_mcp_discoverability() -> GateResult:
    """QG-4: MCP Discoverability Gate."""
    import time

    start = time.time()

    try:
        # Check that MCP server has all required tools
        from hotpass.mcp.server import HotpassMCPServer

        server = HotpassMCPServer()
        tool_names = [tool.name for tool in server.tools]

        required_tools = [
            "hotpass.refine",
            "hotpass.enrich",
            "hotpass.qa",
            "hotpass.explain_provenance",
        ]

        missing_tools = [tool for tool in required_tools if tool not in tool_names]

        if missing_tools:
            return GateResult(
                gate_id="QG-4",
                name="MCP Discoverability",
                passed=False,
                message=f"Missing MCP tools: {', '.join(missing_tools)}",
                duration_seconds=time.time() - start,
            )

        return GateResult(
            gate_id="QG-4",
            name="MCP Discoverability",
            passed=True,
            message=f"{len(tool_names)} MCP tools registered and discoverable",
            duration_seconds=time.time() - start,
        )

    except Exception as e:
        return GateResult(
            gate_id="QG-4",
            name="MCP Discoverability",
            passed=False,
            message=f"Error checking MCP discoverability: {e}",
            duration_seconds=time.time() - start,
        )


def run_qg5_docs_instruction() -> GateResult:
    """QG-5: Docs/Instruction Gate."""
    import time

    start = time.time()

    try:
        copilot_instructions = Path(".github/copilot-instructions.md")
        agents_md = Path("AGENTS.md")

        if not copilot_instructions.exists():
            return GateResult(
                gate_id="QG-5",
                name="Docs/Instructions",
                passed=False,
                message=".github/copilot-instructions.md missing",
                duration_seconds=time.time() - start,
            )

        if not agents_md.exists():
            return GateResult(
                gate_id="QG-5",
                name="Docs/Instructions",
                passed=False,
                message="AGENTS.md missing",
                duration_seconds=time.time() - start,
            )

        # Check content
        copilot_text = copilot_instructions.read_text().lower()
        agents_text = agents_md.read_text().lower()

        if len(copilot_text) < 100 or len(agents_text) < 100:
            return GateResult(
                gate_id="QG-5",
                name="Docs/Instructions",
                passed=False,
                message="Documentation files are too short",
                duration_seconds=time.time() - start,
            )

        # Check for required terms
        required_terms = ["profile", "deterministic", "provenance"]
        missing_in_copilot = [t for t in required_terms if t not in copilot_text]
        missing_in_agents = [t for t in required_terms if t not in agents_text]

        if missing_in_copilot or missing_in_agents:
            return GateResult(
                gate_id="QG-5",
                name="Docs/Instructions",
                passed=False,
                message=f"Missing terms in docs: copilot={missing_in_copilot}, agents={missing_in_agents}",
                duration_seconds=time.time() - start,
            )

        return GateResult(
            gate_id="QG-5",
            name="Docs/Instructions",
            passed=True,
            message="All documentation present with required terminology",
            duration_seconds=time.time() - start,
        )

    except Exception as e:
        return GateResult(
            gate_id="QG-5",
            name="Docs/Instructions",
            passed=False,
            message=f"Error checking docs: {e}",
            duration_seconds=time.time() - start,
        )


def main() -> int:
    """Main entry point for quality gate runner."""
    parser = argparse.ArgumentParser(description="Run Hotpass quality gates")
    parser.add_argument(
        "--gate",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Run specific gate only (1-5)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )

    args = parser.parse_args()

    # Define gates to run
    gates = {
        1: ("QG-1: CLI Integrity", run_qg1_cli_integrity),
        2: ("QG-2: Data Quality", run_qg2_data_quality),
        3: ("QG-3: Enrichment Chain", run_qg3_enrichment_chain),
        4: ("QG-4: MCP Discoverability", run_qg4_mcp_discoverability),
        5: ("QG-5: Docs/Instructions", run_qg5_docs_instruction),
    }

    # Run specified gate or all gates
    if args.gate:
        gates_to_run = {args.gate: gates[args.gate]}
    else:
        gates_to_run = gates

    results: list[GateResult] = []

    if not args.json:
        print("=" * 70)
        print("Hotpass Quality Gate Runner")
        print("=" * 70)
        print()

    for gate_num, (gate_name, gate_func) in gates_to_run.items():
        if not args.json:
            print(f"Running {gate_name}...")

        result = gate_func()
        results.append(result)

        if not args.json:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"  {status}: {result.message}")
            print(f"  Duration: {result.duration_seconds:.2f}s")
            print()

    # Print summary
    if args.json:
        # JSON output for CI
        output = {
            "timestamp": datetime.now(UTC).isoformat(),
            "gates": [
                {
                    "id": r.gate_id,
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "duration_seconds": r.duration_seconds,
                }
                for r in results
            ],
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results if r.passed),
                "failed": sum(1 for r in results if not r.passed),
                "all_passed": all(r.passed for r in results),
            },
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"Total gates: {len(results)}")
        print(f"Passed: {sum(1 for r in results if r.passed)}")
        print(f"Failed: {sum(1 for r in results if not r.passed)}")
        print(f"Total duration: {sum(r.duration_seconds for r in results):.2f}s")
        print()

        if all(r.passed for r in results):
            print("✓ All quality gates passed!")
            return 0
        else:
            print("✗ Some quality gates failed")
            failed = [r for r in results if not r.passed]
            for result in failed:
                print(f"  - {result.gate_id}: {result.message}")
            return 1


if __name__ == "__main__":
    sys.exit(main())
