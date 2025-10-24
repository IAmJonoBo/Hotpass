"""Configuration doctor utilities for diagnosing and fixing configuration issues."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import IndustryProfile, get_default_profile

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticResult:
    """Result of a configuration diagnostic check."""

    check_name: str
    passed: bool
    message: str
    fix_suggestion: str | None = None
    severity: str = "info"  # info, warning, error, critical


class ConfigDoctor:
    """Diagnose and suggest fixes for configuration issues."""

    def __init__(self, config_path: Path | None = None, profile: IndustryProfile | None = None):
        self.config_path = config_path
        self.profile = profile or get_default_profile()
        self.diagnostics: list[DiagnosticResult] = []

    def diagnose(self) -> list[DiagnosticResult]:
        """Run all diagnostic checks."""
        self.diagnostics = []

        self._check_profile_validity()
        self._check_validation_thresholds()
        self._check_source_priorities()
        self._check_column_synonyms()
        self._check_required_fields()

        return self.diagnostics

    def _add_diagnostic(
        self,
        check_name: str,
        passed: bool,
        message: str,
        fix_suggestion: str | None = None,
        severity: str = "info",
    ) -> None:
        """Add a diagnostic result."""
        self.diagnostics.append(
            DiagnosticResult(
                check_name=check_name,
                passed=passed,
                message=message,
                fix_suggestion=fix_suggestion,
                severity=severity,
            )
        )

    def _check_profile_validity(self) -> None:
        """Check if profile has valid basic configuration."""
        if not self.profile.name:
            self._add_diagnostic(
                "profile_name",
                False,
                "Profile name is empty",
                "Set a meaningful profile name",
                "error",
            )
        else:
            self._add_diagnostic(
                "profile_name", True, f"Profile name is set to '{self.profile.name}'"
            )

        if not self.profile.display_name:
            self._add_diagnostic(
                "profile_display_name",
                False,
                "Profile display name is empty",
                "Set a user-friendly display name",
                "warning",
            )

    def _check_validation_thresholds(self) -> None:
        """Check if validation thresholds are reasonable."""
        thresholds = {
            "email": self.profile.email_validation_threshold,
            "phone": self.profile.phone_validation_threshold,
            "website": self.profile.website_validation_threshold,
        }

        for field, threshold in thresholds.items():
            if not 0 <= threshold <= 1:
                self._add_diagnostic(
                    f"{field}_threshold",
                    False,
                    f"{field.capitalize()} validation threshold {threshold} is out of range [0, 1]",
                    f"Set {field}_validation_threshold to a value between 0 and 1 (e.g., 0.85)",
                    "error",
                )
            elif threshold < 0.5:
                self._add_diagnostic(
                    f"{field}_threshold",
                    True,
                    f"{field.capitalize()} threshold {threshold} is very low (< 50%)",
                    f"Consider increasing {field}_validation_threshold to at least 0.70 "
                    "for better quality",
                    "warning",
                )
            elif threshold > 0.95:
                self._add_diagnostic(
                    f"{field}_threshold",
                    True,
                    f"{field.capitalize()} threshold {threshold} is very high (> 95%)",
                    "High thresholds may cause many validation failures. Consider 0.85-0.90",
                    "warning",
                )
            else:
                self._add_diagnostic(
                    f"{field}_threshold",
                    True,
                    f"{field.capitalize()} threshold {threshold} is reasonable",
                )

    def _check_source_priorities(self) -> None:
        """Check if source priorities are configured."""
        if not self.profile.source_priorities:
            self._add_diagnostic(
                "source_priorities",
                False,
                "No source priorities configured",
                "Define source_priorities to control conflict resolution",
                "warning",
            )
        else:
            # Check for duplicate priorities
            priorities = list(self.profile.source_priorities.values())
            if len(priorities) != len(set(priorities)):
                self._add_diagnostic(
                    "source_priorities_unique",
                    False,
                    "Source priorities contain duplicate values",
                    "Assign unique priority values to each source for clear precedence",
                    "warning",
                )
            else:
                self._add_diagnostic(
                    "source_priorities",
                    True,
                    f"Source priorities configured for "
                    f"{len(self.profile.source_priorities)} sources",
                )

    def _check_column_synonyms(self) -> None:
        """Check if column synonyms are configured."""
        if not self.profile.column_synonyms:
            self._add_diagnostic(
                "column_synonyms",
                False,
                "No column synonyms configured",
                "Define column_synonyms for intelligent column mapping",
                "info",
            )
        else:
            # Check for common critical fields
            critical_fields = ["organization_name", "contact_email", "contact_phone"]
            missing_fields = [f for f in critical_fields if f not in self.profile.column_synonyms]

            if missing_fields:
                self._add_diagnostic(
                    "column_synonyms_critical",
                    False,
                    f"Missing synonyms for critical fields: {', '.join(missing_fields)}",
                    f"Add synonyms for: {', '.join(missing_fields)}",
                    "warning",
                )
            else:
                self._add_diagnostic(
                    "column_synonyms",
                    True,
                    f"Column synonyms configured for {len(self.profile.column_synonyms)} fields",
                )

    def _check_required_fields(self) -> None:
        """Check if required fields are configured."""
        if not self.profile.required_fields:
            self._add_diagnostic(
                "required_fields",
                False,
                "No required fields configured",
                "Define at least 'organization_name' as required",
                "warning",
            )
        elif "organization_name" not in self.profile.required_fields:
            self._add_diagnostic(
                "required_fields_org_name",
                False,
                "'organization_name' not in required fields",
                "Add 'organization_name' to required_fields",
                "warning",
            )
        else:
            self._add_diagnostic(
                "required_fields",
                True,
                f"{len(self.profile.required_fields)} required fields configured",
            )

    def get_summary(self) -> dict[str, Any]:
        """Get summary of diagnostic results."""
        if not self.diagnostics:
            self.diagnose()

        total = len(self.diagnostics)
        passed = sum(1 for d in self.diagnostics if d.passed)
        failed = total - passed

        by_severity: dict[str, int] = {}
        for d in self.diagnostics:
            if not d.passed:
                by_severity[d.severity] = by_severity.get(d.severity, 0) + 1

        return {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "by_severity": by_severity,
            "health_score": (passed / total * 100) if total > 0 else 0,
        }

    def print_report(self) -> None:
        """Print diagnostic report to console."""
        if not self.diagnostics:
            self.diagnose()

        print("\n" + "=" * 70)
        print("Configuration Health Check Report")
        print("=" * 70)

        summary = self.get_summary()
        print(f"\nOverall Health Score: {summary['health_score']:.1f}%")
        print(f"Total Checks: {summary['total_checks']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")

        if summary["by_severity"]:
            print("\nIssues by Severity:")
            for severity, count in sorted(summary["by_severity"].items()):
                print(f"  {severity.upper()}: {count}")

        print("\n" + "-" * 70)
        print("Detailed Results:")
        print("-" * 70)

        for d in self.diagnostics:
            icon = "✓" if d.passed else "✗"
            print(f"\n{icon} {d.check_name.replace('_', ' ').title()}")
            print(f"  {d.message}")
            if not d.passed and d.fix_suggestion:
                print(f"  💡 Fix: {d.fix_suggestion}")

        print("\n" + "=" * 70 + "\n")

    def autofix(self) -> bool:
        """Attempt to automatically fix common issues."""
        if not self.diagnostics:
            self.diagnose()

        fixed_count = 0

        # Autofix validation thresholds
        for d in self.diagnostics:
            if not d.passed and "threshold" in d.check_name:
                field = d.check_name.replace("_threshold", "")
                if field == "email":
                    self.profile.email_validation_threshold = 0.85
                    fixed_count += 1
                elif field == "phone":
                    self.profile.phone_validation_threshold = 0.85
                    fixed_count += 1
                elif field == "website":
                    self.profile.website_validation_threshold = 0.75
                    fixed_count += 1

        # Autofix required fields
        if "organization_name" not in self.profile.required_fields:
            self.profile.required_fields.append("organization_name")
            fixed_count += 1

        # Re-run diagnostics after fixes
        if fixed_count > 0:
            logger.info(f"Auto-fixed {fixed_count} configuration issues")
            self.diagnose()

        return fixed_count > 0


def doctor_command(profile_name: str = "generic", autofix: bool = False) -> None:
    """CLI command for configuration doctor."""
    profile = get_default_profile(profile_name)
    doctor = ConfigDoctor(profile=profile)

    if autofix:
        print("Running auto-fix...")
        fixed = doctor.autofix()
        if fixed:
            print("✓ Auto-fix completed")
        else:
            print("ℹ No fixable issues found")

    doctor.print_report()

    summary = doctor.get_summary()
    if summary["health_score"] < 80:
        print("\n⚠️  Configuration health is below 80%. Review and fix the issues above.")
    else:
        print("\n✓ Configuration looks healthy!")
