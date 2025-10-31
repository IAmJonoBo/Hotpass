/**
 * Agent Tools - Wrappers for Prefect and Marquez API operations
 *
 * These tools are invoked by the assistant to interact with the Hotpass platform.
 */

import { prefectApi } from '@/api/prefect'
import { marquezApi } from '@/api/marquez'

export interface ToolResult {
  success: boolean
  data?: unknown
  error?: string
  message: string
}

export interface ToolCall {
  id: string
  tool: string
  timestamp: Date
  result?: ToolResult
}

/**
 * List all available Prefect flows
 */
export async function listFlows(): Promise<ToolResult> {
  try {
    const flows = await prefectApi.getFlows(50)
    return {
      success: true,
      data: flows,
      message: `Found ${flows.length} flows`,
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      message: 'Failed to list flows',
    }
  }
}

/**
 * List lineage for a given namespace from Marquez
 */
export async function listLineage(namespace: string = 'hotpass'): Promise<ToolResult> {
  try {
    const jobs = await marquezApi.getJobs(namespace)
    return {
      success: true,
      data: jobs,
      message: `Found ${jobs.length} jobs in namespace '${namespace}'`,
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      message: `Failed to list lineage for namespace '${namespace}'`,
    }
  }
}

/**
 * Navigate to a specific run details page
 * @returns Navigation intent rather than actual navigation
 */
export function openRun(runId: string): ToolResult {
  return {
    success: true,
    data: { runId, path: `/runs/${runId}` },
    message: `Navigate to run ${runId}`,
  }
}

/**
 * Get flow runs from Prefect
 */
export async function getFlowRuns(limit: number = 50): Promise<ToolResult> {
  try {
    const runs = await prefectApi.getFlowRuns({ limit })
    return {
      success: true,
      data: runs,
      message: `Retrieved ${runs.length} flow runs`,
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      message: 'Failed to get flow runs',
    }
  }
}

/**
 * Execute a tool by name with arguments
 */
export async function executeTool(
  toolName: string,
  args: Record<string, unknown> = {}
): Promise<ToolResult> {
  switch (toolName) {
    case 'listFlows':
      return listFlows()
    case 'listLineage':
      return listLineage(args.namespace as string)
    case 'openRun':
      return openRun(args.runId as string)
    case 'getFlowRuns':
      return getFlowRuns(args.limit as number)
    default:
      return {
        success: false,
        error: `Unknown tool: ${toolName}`,
        message: 'Tool not found',
      }
  }
}
