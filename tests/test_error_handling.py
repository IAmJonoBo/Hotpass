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


def test_error_context_with_location():
    """Test error context with source location."""
    context = ErrorContext(
        category=ErrorCategory.VALIDATION_FAILURE,
        severity=ErrorSeverity.ERROR,
        message="Test error",
        source_file="test.xlsx",
        source_row=10,
        source_column="email",
    )

    assert context.source_file == "test.xlsx"
    assert context.source_row == 10
    assert context.source_column == "email"


def test_error_report_to_json():
    """Test JSON export of error report using get_summary."""
    import json

    report = ErrorReport()
    report.add_error(
        ErrorContext(
            category=ErrorCategory.VALIDATION_FAILURE,
            severity=ErrorSeverity.ERROR,
            message="Test error",
        )
    )

    summary = report.get_summary()
    json_str = json.dumps(summary)
    data = json.loads(json_str)

    assert "total_errors" in data
    assert "total_warnings" in data
    assert data["total_errors"] == 1


def test_error_report_empty():
    """Test empty error report."""
    report = ErrorReport()

    assert not report.has_errors()
    assert not report.has_critical_errors()
    assert len(report.errors) == 0
    assert len(report.warnings) == 0


def test_hotpass_error_with_context():
    """Test HotpassError initialization with context."""
    context = ErrorContext(
        category=ErrorCategory.FILE_NOT_FOUND,
        severity=ErrorSeverity.CRITICAL,
        message="File not found",
    )

    error = HotpassError(context)

    assert error.context == context
    assert "File not found" in str(error)


def test_error_report_info_not_counted_as_error():
    """Test that INFO severity is not counted as error."""
    report = ErrorReport()

    info_ctx = ErrorContext(
        category=ErrorCategory.DATA_QUALITY,
        severity=ErrorSeverity.INFO,
        message="Info message",
    )

    report.add_error(info_ctx)

    assert not report.has_errors()
    # INFO goes to warnings
    assert len(report.warnings) == 1


def test_error_handler_with_warning():
    """Test handling warnings doesn't raise in fail-fast mode."""
    handler = ErrorHandler(fail_fast=True)

    warning_ctx = ErrorContext(
        category=ErrorCategory.DATA_QUALITY,
        severity=ErrorSeverity.WARNING,
        message="Warning",
    )

    # Should not raise
    handler.handle_error(warning_ctx)

    report = handler.get_report()
    assert len(report.warnings) == 1


def test_error_handler_with_critical_not_recoverable_raises():
    """Test that critical non-recoverable errors always raise."""
    handler = ErrorHandler(fail_fast=False)

    critical_ctx = ErrorContext(
        category=ErrorCategory.FILE_NOT_FOUND,
        severity=ErrorSeverity.CRITICAL,
        message="Critical error",
        recoverable=False,  # Not recoverable
    )

    with pytest.raises(HotpassError):
        handler.handle_error(critical_ctx)


def test_error_handler_with_critical_recoverable_no_raise():
    """Test that critical recoverable errors don't raise in accumulate mode."""
    handler = ErrorHandler(fail_fast=False)

    critical_ctx = ErrorContext(
        category=ErrorCategory.FILE_NOT_FOUND,
        severity=ErrorSeverity.CRITICAL,
        message="Critical error",
        recoverable=True,  # Recoverable
    )

    # Should not raise in accumulate mode
    handler.handle_error(critical_ctx)
    
    report = handler.get_report()
    assert report.has_critical_errors()


def test_error_report_get_by_category():
    """Test getting errors by category."""
    report = ErrorReport()

    report.add_error(
        ErrorContext(
            category=ErrorCategory.VALIDATION_FAILURE,
            severity=ErrorSeverity.ERROR,
            message="Validation error",
        )
    )
    report.add_error(
        ErrorContext(
            category=ErrorCategory.FILE_NOT_FOUND,
            severity=ErrorSeverity.ERROR,
            message="File error",
        )
    )

    summary = report.get_summary()
    assert summary["errors_by_category"][ErrorCategory.VALIDATION_FAILURE.value] == 1
    assert summary["errors_by_category"][ErrorCategory.FILE_NOT_FOUND.value] == 1


def test_error_context_all_fields():
    """Test error context with all optional fields."""
    context = ErrorContext(
        category=ErrorCategory.VALIDATION_FAILURE,
        severity=ErrorSeverity.ERROR,
        message="Complete error",
        details={"key": "value"},
        suggested_fix="Fix suggestion",
        source_file="data.xlsx",
        source_row=100,
        source_column="email",
        recoverable=True,
    )

    data = context.to_dict()

    assert data["category"] == ErrorCategory.VALIDATION_FAILURE.value
    assert data["severity"] == ErrorSeverity.ERROR.value
    assert data["message"] == "Complete error"
    assert data["details"]["key"] == "value"
    assert data["suggested_fix"] == "Fix suggestion"
    assert data["source_file"] == "data.xlsx"
    assert data["source_row"] == 100
    assert data["source_column"] == "email"
    assert data["recoverable"] is True
