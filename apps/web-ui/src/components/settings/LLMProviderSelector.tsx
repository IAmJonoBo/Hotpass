import { Check, CircleAlert, PlugZap } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useLLMConfig, useSelectedLLMProvider } from '@/hooks/useLLMConfig'
import type { LLMProvider } from '@/types/llm'

function ProviderSummary({ provider }: { provider: LLMProvider }) {
  return (
    <div className="text-sm text-muted-foreground space-y-1">
      {provider.kind === 'ide' && (
        <div className="flex items-center gap-1 text-blue-600 dark:text-blue-400">
          <PlugZap className="h-4 w-4" />
          <span>IDE-native experience</span>
        </div>
      )}
      {provider.url && (
        <p>
          <span className="font-medium">Endpoint:</span> {provider.url}
        </p>
      )}
      {provider.model && (
        <p>
          <span className="font-medium">Model:</span> {provider.model}
        </p>
      )}
      {provider.max_calls_per_hour !== undefined && (
        <p>
          <span className="font-medium">Quota:</span> {provider.max_calls_per_hour} calls/hour
        </p>
      )}
      {provider.api_key_env && (
        <p>
          <span className="font-medium">API Key:</span> set <code>{provider.api_key_env}</code>
        </p>
      )}
      {provider.notes && <p>{provider.notes}</p>}
      {provider.documentation && (
        <a
          href={provider.documentation}
          target="_blank"
          rel="noreferrer"
          className="text-xs underline text-primary"
        >
          Provider docs
        </a>
      )}
    </div>
  )
}

export function LLMProviderSelector() {
  const { data: config, isLoading, isError, error } = useLLMConfig()
  const { selectedProvider, setProvider } = useSelectedLLMProvider(config)

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Assistant Model</CardTitle>
          <CardDescription>Loading provider catalogue…</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Fetching llm-providers.yaml…</p>
        </CardContent>
      </Card>
    )
  }

  if (isError || !config) {
    return (
      <Card className="border-red-500/20 bg-red-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CircleAlert className="h-5 w-5 text-red-600 dark:text-red-400" />
            Assistant Model
          </CardTitle>
          <CardDescription>Unable to load llm-providers.yaml</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-600 dark:text-red-400">
            {(error instanceof Error ? error.message : 'Unknown error') ?? 'Unknown error'}
          </p>
          <p className="text-xs text-muted-foreground mt-2">
            Ensure <code>apps/web-ui/public/config/llm-providers.yaml</code> is present in the build output.
          </p>
        </CardContent>
      </Card>
    )
  }

  const providers = [...config.providers].sort((a, b) => {
    if (a.name === 'copilot') return -1
    if (b.name === 'copilot') return 1
    return (a.label || a.name).localeCompare(b.label || b.name)
  })

  const handleSelect = (provider: LLMProvider) => {
    setProvider(provider.name)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Assistant Model</CardTitle>
        <CardDescription>
          Preferred: GitHub Copilot in VS Code. Select an alternate provider when operating from the web UI or Docker container.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <span className="font-medium">Fallback strategy:</span>
          <Badge variant="outline">{config.strategy}</Badge>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {providers.map(provider => {
            const isSelected = provider.name === selectedProvider
            return (
              <div
                key={provider.name}
                className={cn(
                  'border rounded-lg p-4 space-y-3 transition-shadow',
                  isSelected ? 'border-primary shadow-lg shadow-primary/20' : 'border-border'
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-base">{provider.label ?? provider.name}</h3>
                      {provider.name === 'copilot' && (
                        <Badge variant="default" className="bg-violet-600 text-white">
                          Recommended
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">
                      {provider.kind === 'ide' ? 'IDE' : provider.kind === 'local' ? 'Local runtime' : 'API'}
                    </p>
                  </div>

                  {isSelected && (
                    <Badge
                      variant="outline"
                      className="flex items-center gap-1 border-green-500 bg-green-500/10 text-green-700 dark:text-green-300"
                    >
                      <Check className="h-3 w-3" />
                      Active
                    </Badge>
                  )}
                </div>

                <ProviderSummary provider={provider} />

                <Button
                  variant={isSelected ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleSelect(provider)}
                  className="w-full"
                >
                  {isSelected ? 'Selected' : 'Use this provider'}
                </Button>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
