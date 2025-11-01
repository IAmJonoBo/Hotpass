export interface ToolDefinition {
  name: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  path: string
  description?: string
}

const DEFAULT_CONTRACT: ToolDefinition[] = [
  { name: 'list_prefect_flows', method: 'GET', path: '/api/prefect/flows' },
  { name: 'get_marquez_lineage', method: 'GET', path: '/api/marquez/lineage?ns={namespace}' },
  { name: 'run_hotpass_refine', method: 'POST', path: '/api/hotpass/refine' },
]

let cachedContract: ToolDefinition[] = DEFAULT_CONTRACT
let pending: Promise<ToolDefinition[]> | null = null

const CONTRACT_URL = `${import.meta.env.BASE_URL || '/'}tools.json`

export function getCachedToolContract(): ToolDefinition[] {
  return cachedContract
}

export async function loadToolContract(): Promise<ToolDefinition[]> {
  if (pending) {
    return pending
  }
  pending = fetch(CONTRACT_URL, { headers: { Accept: 'application/json' } })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`Failed to load tools.json: ${response.status}`)
      }
      const data = (await response.json()) as ToolDefinition[]
      if (Array.isArray(data) && data.every((entry) => entry?.name && entry?.path && entry?.method)) {
        cachedContract = data
      }
      return cachedContract
    })
    .catch((error) => {
      console.warn('Falling back to default tool contract', error)
      return cachedContract
    })
    .finally(() => {
      pending = null
    })
  return pending
}

export { DEFAULT_CONTRACT }
