"""DuckDB schema definitions for the canonical party store."""

from __future__ import annotations

from textwrap import dedent

import duckdb

PARTY_TABLE_DDL = dedent(
    """
    CREATE TABLE IF NOT EXISTS party (
        party_id UUID PRIMARY KEY,
        kind VARCHAR NOT NULL,
        display_name VARCHAR NOT NULL,
        normalized_name VARCHAR,
        country_code VARCHAR,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        provenance_source VARCHAR,
        provenance_record_id VARCHAR,
        provenance_captured_at TIMESTAMP WITH TIME ZONE,
        provenance_selection_priority INTEGER,
        provenance_quality_score DOUBLE
    );
    """
).strip()


PARTY_ALIAS_TABLE_DDL = dedent(
    """
    CREATE TABLE IF NOT EXISTS party_alias (
        alias_id UUID PRIMARY KEY,
        party_id UUID NOT NULL REFERENCES party(party_id),
        alias VARCHAR NOT NULL,
        alias_type VARCHAR NOT NULL,
        confidence DOUBLE NOT NULL,
        confidence_band VARCHAR NOT NULL,
        valid_start TIMESTAMP WITH TIME ZONE NOT NULL,
        valid_end TIMESTAMP WITH TIME ZONE,
        provenance_source VARCHAR,
        provenance_record_id VARCHAR,
        provenance_captured_at TIMESTAMP WITH TIME ZONE,
        provenance_selection_priority INTEGER,
        provenance_quality_score DOUBLE
    );
    """
).strip()


PARTY_ROLE_TABLE_DDL = dedent(
    """
    CREATE TABLE IF NOT EXISTS party_role (
        role_id UUID PRIMARY KEY,
        subject_party_id UUID NOT NULL REFERENCES party(party_id),
        object_party_id UUID NOT NULL REFERENCES party(party_id),
        role_name VARCHAR NOT NULL,
        role_category VARCHAR,
        is_primary BOOLEAN NOT NULL,
        valid_start TIMESTAMP WITH TIME ZONE NOT NULL,
        valid_end TIMESTAMP WITH TIME ZONE,
        provenance_source VARCHAR,
        provenance_record_id VARCHAR,
        provenance_captured_at TIMESTAMP WITH TIME ZONE,
        provenance_selection_priority INTEGER,
        provenance_quality_score DOUBLE
    );
    """
).strip()


CONTACT_METHOD_TABLE_DDL = dedent(
    """
    CREATE TABLE IF NOT EXISTS contact_method (
        contact_method_id UUID PRIMARY KEY,
        party_id UUID NOT NULL REFERENCES party(party_id),
        method_type VARCHAR NOT NULL,
        value VARCHAR NOT NULL,
        is_primary BOOLEAN NOT NULL,
        confidence DOUBLE NOT NULL,
        valid_start TIMESTAMP WITH TIME ZONE NOT NULL,
        valid_end TIMESTAMP WITH TIME ZONE,
        provenance_source VARCHAR,
        provenance_record_id VARCHAR,
        provenance_captured_at TIMESTAMP WITH TIME ZONE,
        provenance_selection_priority INTEGER,
        provenance_quality_score DOUBLE
    );
    """
).strip()


ALL_DDL = (
    PARTY_TABLE_DDL,
    PARTY_ALIAS_TABLE_DDL,
    PARTY_ROLE_TABLE_DDL,
    CONTACT_METHOD_TABLE_DDL,
)


def install_tables(connection: duckdb.DuckDBPyConnection) -> None:
    """Create the canonical party tables within an existing DuckDB connection."""

    for statement in ALL_DDL:
        connection.execute(statement)
