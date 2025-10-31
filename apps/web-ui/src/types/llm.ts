export interface LLMProvider {
  name: string
  label: string
  kind: 'ide' | 'api' | 'local' | string
  url?: string
  model?: string
  documentation?: string
  notes?: string
  api_key_env?: string
  max_calls_per_hour?: number
  cost_per_call_usd?: number
}

export interface LLMConfig {
  strategy: string
  default: string
  providers: LLMProvider[]
}
