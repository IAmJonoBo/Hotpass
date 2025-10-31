// Marquez/OpenLineage API Types

export interface MarquezNamespace {
  name: string
  createdAt: string
  updatedAt: string
  ownerName?: string
  description?: string
}

export interface MarquezJob {
  id: {
    namespace: string
    name: string
  }
  type: string
  name: string
  createdAt: string
  updatedAt: string
  namespace: string
  inputs?: MarquezDataset[]
  outputs?: MarquezDataset[]
  location?: string
  context?: Record<string, unknown>
  description?: string
  latestRun?: MarquezRun
}

export interface MarquezDataset {
  id: {
    namespace: string
    name: string
  }
  type: string
  name: string
  physicalName: string
  createdAt: string
  updatedAt: string
  namespace: string
  sourceName: string
  fields?: MarquezField[]
  tags?: string[]
  description?: string
}

export interface MarquezField {
  name: string
  type: string
  tags?: string[]
  description?: string
}

export interface MarquezRun {
  id: string
  createdAt: string
  updatedAt: string
  nominalStartTime?: string
  nominalEndTime?: string
  state: 'NEW' | 'RUNNING' | 'COMPLETED' | 'ABORTED' | 'FAILED'
  startedAt?: string
  endedAt?: string
  durationMs?: number
  args?: Record<string, unknown>
  context?: Record<string, unknown>
  facets?: Record<string, unknown>
}

export interface MarquezLineageNode {
  id: string
  type: 'DATASET' | 'JOB'
  data: MarquezDataset | MarquezJob
  inEdges?: MarquezLineageEdge[]
  outEdges?: MarquezLineageEdge[]
}

export interface MarquezLineageEdge {
  origin: string
  destination: string
}

export interface MarquezLineageGraph {
  graph: MarquezLineageNode[]
}

// Prefect API Types

export interface PrefectFlow {
  id: string
  name: string
  created: string
  updated: string
  tags?: string[]
}

export interface PrefectFlowRun {
  id: string
  name: string
  flow_id: string
  deployment_id?: string
  state_type: 'SCHEDULED' | 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'CRASHED'
  state_name: string
  start_time?: string
  end_time?: string
  expected_start_time?: string
  total_run_time?: number
  created: string
  updated: string
  tags?: string[]
  parameters?: Record<string, unknown>
}

export interface PrefectDeployment {
  id: string
  name: string
  flow_id: string
  created: string
  updated: string
  tags?: string[]
  parameters?: Record<string, unknown>
}

// Hotpass-specific types

export interface HotpassRun {
  id: string
  timestamp: string
  status: 'completed' | 'failed' | 'running' | 'pending'
  duration?: number
  profile: string
  inputPath: string
  outputPath?: string
  qaResults?: QAResult[]
  lineageUrl?: string
  prefectRunId?: string
}

export interface QAResult {
  check: string
  status: 'passed' | 'failed' | 'warning'
  message?: string
  details?: Record<string, unknown>
}

// Configuration types

export interface AppConfig {
  prefectApiUrl: string
  marquezApiUrl: string
  environment: 'local' | 'staging' | 'prod'
}
