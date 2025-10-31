from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.assertions import expect

pytest.importorskip("license_expression")

from ops.compliance.check_scancode import evaluate


def test_evaluate_passes_allowed_license(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    data = {
        "files": [
            {
                "path": "LICENSE",
                "licenses": [
                    {
                        "spdx_license_expression": "MIT",
                    }
                ],
            }
        ]
    }
    report.write_text(json.dumps(data), encoding="utf-8")
    policy = tmp_path / "policy.yml"
    policy.write_text(
        "allowed:\n  - MIT\nforbidden: []\nfail_on_unknown: false\n",
        encoding="utf-8",
    )

    exit_code = evaluate(report, policy)
    expect(exit_code == 0, "Should pass when license is in allowed list")


def test_evaluate_blocks_forbidden_license(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    data = {
        "files": [
            {
                "path": "vendor/code.py",
                "licenses": [
                    {
                        "spdx_license_expression": "GPL-3.0",  # forbidden
                    }
                ],
            }
        ]
    }
    report.write_text(json.dumps(data), encoding="utf-8")
    policy = tmp_path / "policy.yml"
    policy.write_text(
        "allowed:\n  - MIT\nforbidden:\n  - GPL-3.0\nfail_on_unknown: true\n",
        encoding="utf-8",
    )

    exit_code = evaluate(report, policy)
    expect(exit_code != 0, "Should fail when license is in forbidden list")
