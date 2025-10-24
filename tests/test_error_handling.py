"""Tests for enhanced error handling."""

import pytest

from hotpass.error_handling import (
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorReport,
    ErrorSeverity,
    HotpassError,
    ValidationError,
)


def test_error_context_to_dict():
    """Test error context serialization."""
    context = ErrorContext(
        category=ErrorCategory.VALIDATION_FAILURE,
        severity=ErrorSeverity.WARNING,
        message="Test error",
        details={"field": "email"},
        suggested_fix="Check email format",
    )

    data = context.to_dict()

    assert data["category"] == "validation_failure"
    assert data["severity"] == "warning"
    assert data["message"] == "Test error"
    assert data["details"]["field"] == "email"


def test_validation_error_create():
    """Test creating a validation error."""
    error = ValidationError.create(
        field="email",
        value="invalid",
        expected="valid email address",
        row=5,
    )

    assert error.context.category == ErrorCategory.VALIDATION_FAILURE
    assert error.context.source_row == 5
    assert "email" in error.context.message


def test_error_report_add_error():
    """Test adding errors to report."""
    report = ErrorReport()

    error_ctx = ErrorContext(
        category=ErrorCategory.VALIDATION_FAILURE,
        severity=ErrorSeverity.ERROR,
        message="Error message",
    )
    warning_ctx = ErrorContext(
        category=ErrorCategory.DATA_QUALITY,
        severity=ErrorSeverity.WARNING,
        message="Warning message",
    )

    report.add_error(error_ctx)
    report.add_error(warning_ctx)

    assert len(report.errors) == 1
    assert len(report.warnings) == 1


def test_error_report_has_critical_errors():
    """Test detecting critical errors."""
    report = ErrorReport()

    critical_ctx = ErrorContext(
        category=ErrorCategory.FILE_NOT_FOUND,
        severity=ErrorSeverity.CRITICAL,
        message="Critical error",
    )

    report.add_error(critical_ctx)

    assert report.has_critical_errors()
    assert report.has_errors()


def test_error_report_get_summary():
    """Test error report summary."""
    report = ErrorReport()

    report.add_error(
        ErrorContext(
            category=ErrorCategory.VALIDATION_FAILURE,
            severity=ErrorSeverity.ERROR,
            message="Error 1",
        )
    )
    report.add_error(
        ErrorContext(
            category=ErrorCategory.VALIDATION_FAILURE,
            severity=ErrorSeverity.WARNING,
            message="Warning 1",
        )
    )

    summary = report.get_summary()

    assert summary["total_errors"] == 1
    assert summary["total_warnings"] == 1
    assert "validation_failure" in summary["errors_by_category"]


def test_error_report_to_markdown():
    """Test markdown export."""
    report = ErrorReport()

    report.add_error(
        ErrorContext(
            category=ErrorCategory.VALIDATION_FAILURE,
            severity=ErrorSeverity.ERROR,
            message="Test error",
            suggested_fix="Fix it this way",
        )
    )

    markdown = report.to_markdown()

    assert "# Error Report" in markdown
    assert "Test error" in markdown
    assert "Fix it this way" in markdown


def test_error_handler_fail_fast():
    """Test fail-fast mode."""
    handler = ErrorHandler(fail_fast=True)

    error_ctx = ErrorContext(
        category=ErrorCategory.VALIDATION_FAILURE,
        severity=ErrorSeverity.ERROR,
        message="Error",
    )

    with pytest.raises(HotpassError):
        handler.handle_error(error_ctx)


def test_error_handler_accumulate():
    """Test error accumulation mode."""
    handler = ErrorHandler(fail_fast=False)

    error_ctx = ErrorContext(
        category=ErrorCategory.VALIDATION_FAILURE,
        severity=ErrorSeverity.ERROR,
        message="Error",
        recoverable=True,
    )

    handler.handle_error(error_ctx)

    report = handler.get_report()
    assert report.has_errors()
    assert len(report.errors) == 1
