"""Hotpass data refinement pipeline."""

from . import benchmarks
from .artifacts import create_refined_archive
from .column_mapping import ColumnMapper, infer_column_types, profile_dataframe
from .config import IndustryProfile, get_default_profile, load_industry_profile
from .config_doctor import ConfigDoctor, DiagnosticResult, doctor_command
from .contacts import Contact, OrganizationContacts, consolidate_contacts_from_rows
from .error_handling import ErrorHandler, ErrorReport, ErrorSeverity
from .formatting import OutputFormat, apply_excel_formatting, export_to_multiple_formats
from .pipeline import PipelineConfig, PipelineResult, QualityReport, run_pipeline

__all__ = [
    "benchmarks",
    "create_refined_archive",
    "PipelineConfig",
    "PipelineResult",
    "QualityReport",
    "run_pipeline",
    "ColumnMapper",
    "infer_column_types",
    "profile_dataframe",
    "IndustryProfile",
    "get_default_profile",
    "load_industry_profile",
    "ConfigDoctor",
    "DiagnosticResult",
    "doctor_command",
    "Contact",
    "OrganizationContacts",
    "consolidate_contacts_from_rows",
    "ErrorHandler",
    "ErrorReport",
    "ErrorSeverity",
    "OutputFormat",
    "apply_excel_formatting",
    "export_to_multiple_formats",
]
