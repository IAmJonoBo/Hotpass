/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_PREFECT_API_URL?: string
  readonly VITE_MARQUEZ_API_URL?: string
  readonly VITE_ENVIRONMENT?: string
  readonly PREFECT_API_URL?: string
  readonly OPENLINEAGE_URL?: string
  readonly HOTPASS_ENVIRONMENT?: string
  readonly ARC_STATUS_URL?: string
  readonly VITE_ARC_STATUS_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
