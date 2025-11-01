import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, Loader2, ShieldAlert, ExternalLink } from 'lucide-react'
import { prefectApi } from '@/api/prefect'
import { marquezApi } from '@/api/marquez'
import { fetchArcStatus } from '@/api/arc'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface StatusCardProps {
  title: string
  description: string
  healthy?: boolean | null
  loading?: boolean
  href?: string
  hint?: string
  lastChecked?: string
  extra?: React.ReactNode
}

function StatusCard({ title, description, healthy, loading, href, hint, lastChecked, extra }: StatusCardProps) {
  const Icon = loading ? Loader2 : healthy ? CheckCircle2 : AlertTriangle
  const color = loading ? 'text-muted-foreground' : healthy ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Icon className={`h-5 w-5 ${loading ? 'animate-spin' : color}`} />
            {title}
            {href && (
              <a
                href={href}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs font-normal text-muted-foreground hover:text-primary"
              >
                View <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
        {healthy != null && !loading && (
          <Badge variant={healthy ? 'outline' : 'destructive'}>
            {healthy ? 'Healthy' : 'Unreachable'}
          </Badge>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {hint && (
          <div className="rounded-lg bg-muted p-3 text-xs text-muted-foreground">
            <ShieldAlert className="mr-2 inline h-3 w-3" />
            {hint}
          </div>
        )}
        {lastChecked && (
          <p className="text-xs text-muted-foreground">Last checked {new Date(lastChecked).toLocaleString()}</p>
        )}
        {extra}
      </CardContent>
    </Card>
  )
}

export function Health() {
  const {
    data: prefectHealthy,
    isLoading: prefectLoading,
    dataUpdatedAt: prefectChecked,
  } = useQuery({
    queryKey: ['prefect-health'],
    queryFn: () => prefectApi.checkHealth(),
    refetchInterval: 60000,
  })

  const {
    data: marquezHealthy,
    isLoading: marquezLoading,
    dataUpdatedAt: marquezChecked,
  } = useQuery({
    queryKey: ['marquez-health'],
    queryFn: () => marquezApi.checkHealth(),
    refetchInterval: 60000,
  })

  const {
    data: arcStatus,
    isLoading: arcLoading,
    dataUpdatedAt: arcChecked,
  } = useQuery({
    queryKey: ['arc-status'],
    queryFn: () => fetchArcStatus(),
    refetchInterval: 120000,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Platform Health</h1>
        <p className="text-muted-foreground">
          Quick probes against Prefect, Marquez, and ARC runner lifecycle endpoints.
          If a service is unreachable, confirm your VPN or bastion tunnel before retrying.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <StatusCard
          title="Prefect API"
          description="Workflow orchestration surface"
          healthy={prefectHealthy}
          loading={prefectLoading}
          href={`${import.meta.env.PREFECT_API_URL || import.meta.env.VITE_PREFECT_API_URL || '/api/prefect'}`}
          hint={!prefectHealthy ? 'Prefect requires tunnel access. If you are off-network, run hotpass net up first.' : undefined}
          lastChecked={prefectChecked ? new Date(prefectChecked).toISOString() : undefined}
        />
        <StatusCard
          title="Marquez / OpenLineage"
          description="Lineage metadata service"
          healthy={marquezHealthy}
          loading={marquezLoading}
          href={`${import.meta.env.OPENLINEAGE_URL || import.meta.env.VITE_MARQUEZ_API_URL || '/api/marquez'}`}
          hint={!marquezHealthy ? 'Verify bastion forwards for port 5000 and ensure the Marquez stack is running.' : undefined}
          lastChecked={marquezChecked ? new Date(marquezChecked).toISOString() : undefined}
        />
        <StatusCard
          title="ARC Runner Lifecycle"
          description="GitHub ARC controller + runner scale set"
          healthy={arcStatus?.success ?? null}
          loading={arcLoading}
          lastChecked={arcChecked ? new Date(arcChecked).toISOString() : undefined}
          hint={!arcStatus?.success ? 'Run `uv run hotpass arc status --store-summary` to refresh the lifecycle snapshot.' : undefined}
          extra={arcStatus ? (
            <div className="space-y-2 text-xs text-muted-foreground">
              {arcStatus.identityArn && (
                <div>
                  <span className="font-medium text-foreground">OIDC Identity:</span> {arcStatus.identityArn}
                </div>
              )}
              {arcStatus.identityAccount && (
                <div>
                  <span className="font-medium text-foreground">AWS Account:</span> {arcStatus.identityAccount}
                  {arcStatus.identitySource && ` · via ${arcStatus.identitySource}`}
                </div>
              )}
              <div><span className="font-medium text-foreground">Verified:</span> {new Date(arcStatus.verifiedAt).toLocaleString()}</div>
              {arcStatus.notes && <div>{arcStatus.notes}</div>}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">No lifecycle snapshot available yet.</p>
          )}
        />
      </div>
    </div>
  )
}
