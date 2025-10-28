workspace "Hotpass Architecture" "C4 views capturing the Hotpass platform, deployment boundaries, and security considerations." {
    !version 1.0
    !identifiers canonical

    model {
        person data_steward "Data Steward" "Prepares industry spreadsheets and triggers Hotpass runs." {
            tags "Human"
        }

        person data_consumer "Data Consumer" "Uses refined exports, quality reports, and dashboards to make decisions." {
            tags "Human"
        }

        person observability_analyst "Observability Analyst" "Monitors telemetry emitted by the platform." {
            tags "Human"
        }

        softwareSystem hotpass "Hotpass Platform" "Normalises spreadsheets into a governed single source of truth." {
            tags "SoftwareSystem"
        }

        softwareSystem prefectorion "Prefect Orion / Cloud" "Schedules, triggers, and tracks Prefect flow runs." {
            tags "ExternalSystem"
        }

        softwareSystem external_registries "External Registries" "Optional enrichment sources such as CIPC or SACAA datasets." {
            tags "ExternalSystem"
        }

        softwareSystem observability_stack "Observability Stack" "OpenTelemetry collector, metrics store, and dashboards." {
            tags "ExternalSystem"
        }

        data_steward -> hotpass "Supplies raw spreadsheets, configures runs" {
            tags "Ingestion"
        }
        data_consumer <- hotpass "Retrieves refined datasets, dashboards, and reports" {
            tags "Distribution"
        }
        observability_analyst -> observability_stack "Reviews traces, metrics, and alerts" {
            tags "Observability"
        }

        hotpass -> prefectorion "Publishes flows, receives schedules and run parameters"
        prefectorion -> hotpass "Triggers flow execution via workers"

        hotpass -> external_registries "Calls enrichment adapters (HTTP, API connectors)" {
            tags "Optional"
        }
        hotpass -> observability_stack "Streams OpenTelemetry traces and metrics" {
            tags "Observability"
        }

        container boundary runner_boundary "Execution boundary — CLI host, Prefect work pool, or CI runner" {
            container cli "CLI & Prefect Flow" "Python Typer CLI / Prefect flow" "Entry point triggered by users or Prefect." {
                tags "Container"
            }

            container pipeline_engine "Pipeline Engine" "Python" "Coordinates ingestion, validation, enrichment, and export." {
                tags "Container"
            }

            container observability_adapter "Observability Adapter" "Python (OpenTelemetry SDK)" "Initialises OpenTelemetry exporters and guards console handlers." {
                tags "Container"
            }

            containerDataStore input_store "Input File Store" "File system" "Raw spreadsheets and enrichment caches." {
                tags "DataStore", "CriticalAsset"
            }

            containerDataStore refined_store "Refined Output Store" "File system" "Excel workbooks, CSV extracts, and packaged archives." {
                tags "DataStore", "CriticalAsset"
            }

            containerDataStore quality_store "Quality & Audit Log" "File system" "JSON/Markdown quality reports and audit trail." {
                tags "DataStore", "CriticalAsset"
            }

            container redis_cache "Redis Cache (optional)" "Redis" "Optional caching tier for enrichment and geocoding lookups." {
                tags "Optional", "Container"
            }

            cli -> pipeline_engine "Passes pipeline configuration" {
                tags "Internal"
            }
            cli -> input_store "Reads spreadsheets" {
                tags "Ingestion"
            }
            pipeline_engine -> input_store "Loads staged datasets" {
                tags "Ingestion"
            }
            pipeline_engine -> refined_store "Writes SSOT exports and packaged archives" {
                tags "Distribution"
            }
            pipeline_engine -> quality_store "Persists audit events and expectation outcomes" {
                tags "Distribution"
            }
            pipeline_engine -> observability_adapter "Emits trace/span events" {
                tags "Observability"
            }
            pipeline_engine -> redis_cache "Caches registry/enrichment responses" {
                tags "Optional"
            }
            pipeline_engine -> external_registries "Invokes HTTP connectors" {
                tags "Optional"
            }
            observability_adapter -> observability_stack "Ships telemetry via OTLP" {
                tags "Observability"
            }
        }

        container boundary dashboard_boundary "Dashboard boundary — Streamlit host" {
            container dashboard "Streamlit Dashboard" "Streamlit" "Interactive UI for triggering runs, reviewing history, and inspecting quality metrics." {
                tags "Container"
            }
            dashboard -> pipeline_engine "Invokes run_pipeline through local imports" {
                tags "Internal"
            }
            dashboard -> quality_store "Reads pipeline history and quality reports" {
                tags "Distribution"
            }
            dashboard -> refined_store "Previews refined datasets" {
                tags "Distribution"
            }
        }

        hotpass -> dashboard "Exposes dashboard module for operators"
        dashboard -> data_steward "Guides manual run oversight" {
            tags "Distribution"
        }
    }

    views {
        systemContext hotpass "Context view" {
            include *
            autoLayout lr
            animationStep 1 {
                include data_steward
                include hotpass
                include data_consumer
            }
            animationStep 2 {
                include prefectorion
                include external_registries
                include observability_stack
            }
            animationStep 3 {
                include observability_analyst
            }
            description "System context showing users and adjacent systems."
        }

        container hotpass "Container view" {
            include hotpass
            include runner_boundary
            include dashboard_boundary
            include prefectorion
            include external_registries
            include observability_stack
            include data_steward
            include data_consumer
            autoLayout lr
            description "Containers, trust boundaries, and persistent stores."
        }

        component pipeline_engine "Component view — Pipeline engine" {
            include pipeline_engine
            include cli
            include input_store
            include refined_store
            include quality_store
            include redis_cache
            include external_registries
            include observability_adapter

            component ingestion "Data ingestion" "data_sources.py" "Loads spreadsheets, normalises schemas, tracks provenance." {
                tags "Component"
            }
            component mapping "Column & entity mapping" "column_mapping.py" "Aligns fields and deduplicates records using Splink." {
                tags "Component"
            }
            component validation "Quality & compliance" "quality.py / compliance.py" "Runs Great Expectations suites and POPIA checks." {
                tags "Component"
            }
            component enrichment "Enrichment connectors" "enrichment.py" "Fetches supplementary data and enriches records." {
                tags "Component", "Optional"
            }
            component formatter "Formatter & reporting" "formatting.py / artifacts.py" "Builds Excel/Parquet exports and archives." {
                tags "Component"
            }
            component observability_hooks "Observability hooks" "observability.py" "Initialises metrics, traces, and safe console exporters." {
                tags "Component"
            }
            component orchestration_glue "Orchestration adapter" "orchestration.py" "Wraps Prefect flow/task definitions." {
                tags "Component"
            }

            pipeline_engine -> ingestion "Delegates source loading"
            ingestion -> input_store "Reads raw inputs"
            pipeline_engine -> mapping "Resolves canonical entities"
            mapping -> validation "Feeds validated SSOT"
            validation -> enrichment "Hands off to optional connectors" {
                tags "Optional"
            }
            enrichment -> redis_cache "Caches HTTP responses" {
                tags "Optional"
            }
            enrichment -> external_registries "Calls external APIs" {
                tags "Optional"
            }
            validation -> formatter "Provides audited dataset"
            formatter -> refined_store "Writes outputs"
            formatter -> quality_store "Writes quality reports"
            observability_hooks -> observability_adapter "Registers exporters"
            orchestration_glue -> cli "Exposes Prefect deployment triggers"
            observability_hooks -> quality_store "Appends audit trail"
            validation -> quality_store "Records expectation outcomes"
        }
    }

    styles {
        element "Human" {
            shape person
            background "#08427b"
            color "#ffffff"
        }
        element "SoftwareSystem" {
            background "#1168bd"
            color "#ffffff"
        }
        element "ExternalSystem" {
            background "#999999"
            color "#ffffff"
        }
        element "Container" {
            background "#438dd5"
            color "#ffffff"
        }
        element "Component" {
            background "#85bbf0"
            color "#000000"
        }
        element "DataStore" {
            shape cylinder
            background "#2f95b5"
            color "#ffffff"
        }
        element "CriticalAsset" {
            stroke "#d13438"
            strokeWidth 3
        }
        element "Optional" {
            border dashed
        }
        element "Observability" {
            stroke "#7a52aa"
        }
        element "Ingestion" {
            stroke "#2f855a"
        }
        element "Distribution" {
            stroke "#b7791f"
        }
        element "Internal" {
            stroke "#2d3748"
        }
    }
}
