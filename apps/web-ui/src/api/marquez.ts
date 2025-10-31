/**
 * Marquez/OpenLineage API client
 *
 * Fetches lineage data from the Marquez backend.
 * Base URL configured via VITE_MARQUEZ_API_URL env variable.
 *
 * ASSUMPTION: Marquez is available at the configured URL (default: http://localhost:5000)
 * ASSUMPTION: API follows standard Marquez v1 endpoints
 */

import type {
  MarquezNamespace,
  MarquezJob,
  MarquezDataset,
  MarquezRun,
  MarquezLineageGraph,
} from '@/types'

const getBaseUrl = (): string => {
  // In production, use proxy path; in dev, vite.config.ts handles the proxy
  return import.meta.env.VITE_MARQUEZ_API_URL || '/api/marquez'
}

export const marquezApi = {
  // List all namespaces
  async getNamespaces(): Promise<MarquezNamespace[]> {
    const url = `${getBaseUrl()}/api/v1/namespaces`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch namespaces: ${response.statusText}`)
    }
    const data = await response.json()
    return data.namespaces || []
  },

  // Get jobs in a namespace
  async getJobs(namespace: string, limit = 100, offset = 0): Promise<MarquezJob[]> {
    const url = `${getBaseUrl()}/api/v1/namespaces/${encodeURIComponent(namespace)}/jobs?limit=${limit}&offset=${offset}`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch jobs: ${response.statusText}`)
    }
    const data = await response.json()
    return data.jobs || []
  },

  // Get a specific job
  async getJob(namespace: string, jobName: string): Promise<MarquezJob> {
    const url = `${getBaseUrl()}/api/v1/namespaces/${encodeURIComponent(namespace)}/jobs/${encodeURIComponent(jobName)}`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch job: ${response.statusText}`)
    }
    return response.json()
  },

  // Get runs for a job
  async getJobRuns(namespace: string, jobName: string, limit = 100, offset = 0): Promise<MarquezRun[]> {
    const url = `${getBaseUrl()}/api/v1/namespaces/${encodeURIComponent(namespace)}/jobs/${encodeURIComponent(jobName)}/runs?limit=${limit}&offset=${offset}`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch job runs: ${response.statusText}`)
    }
    const data = await response.json()
    return data.runs || []
  },

  // Get a specific run
  async getRun(runId: string): Promise<MarquezRun> {
    const url = `${getBaseUrl()}/api/v1/runs/${encodeURIComponent(runId)}`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch run: ${response.statusText}`)
    }
    return response.json()
  },

  // Get datasets in a namespace
  async getDatasets(namespace: string, limit = 100, offset = 0): Promise<MarquezDataset[]> {
    const url = `${getBaseUrl()}/api/v1/namespaces/${encodeURIComponent(namespace)}/datasets?limit=${limit}&offset=${offset}`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch datasets: ${response.statusText}`)
    }
    const data = await response.json()
    return data.datasets || []
  },

  // Get lineage for a dataset
  async getDatasetLineage(namespace: string, datasetName: string, depth = 20): Promise<MarquezLineageGraph> {
    const url = `${getBaseUrl()}/api/v1/lineage?nodeId=${encodeURIComponent(namespace)}:${encodeURIComponent(datasetName)}&depth=${depth}`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch lineage: ${response.statusText}`)
    }
    return response.json()
  },

  // Get lineage for a job
  async getJobLineage(namespace: string, jobName: string, depth = 20): Promise<MarquezLineageGraph> {
    const url = `${getBaseUrl()}/api/v1/lineage?nodeId=${encodeURIComponent(namespace)}:${encodeURIComponent(jobName)}&depth=${depth}`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch lineage: ${response.statusText}`)
    }
    return response.json()
  },
}

// Mock data for development when Marquez is not available
export const mockMarquezData = {
  namespaces: [
    { name: 'hotpass', createdAt: '2024-01-01T00:00:00Z', updatedAt: '2024-01-15T00:00:00Z' },
    { name: 'default', createdAt: '2024-01-01T00:00:00Z', updatedAt: '2024-01-15T00:00:00Z' },
  ] as MarquezNamespace[],

  jobs: [
    {
      id: { namespace: 'hotpass', name: 'refine_pipeline' },
      type: 'BATCH',
      name: 'refine_pipeline',
      namespace: 'hotpass',
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-15T12:30:00Z',
      latestRun: {
        id: 'run-001',
        createdAt: '2024-01-15T12:00:00Z',
        updatedAt: '2024-01-15T12:30:00Z',
        state: 'COMPLETED',
        startedAt: '2024-01-15T12:00:00Z',
        endedAt: '2024-01-15T12:30:00Z',
        durationMs: 1800000,
      },
    },
    {
      id: { namespace: 'hotpass', name: 'enrich_pipeline' },
      type: 'BATCH',
      name: 'enrich_pipeline',
      namespace: 'hotpass',
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-15T13:45:00Z',
      latestRun: {
        id: 'run-002',
        createdAt: '2024-01-15T13:00:00Z',
        updatedAt: '2024-01-15T13:45:00Z',
        state: 'COMPLETED',
        startedAt: '2024-01-15T13:00:00Z',
        endedAt: '2024-01-15T13:45:00Z',
        durationMs: 2700000,
      },
    },
  ] as MarquezJob[],
}
