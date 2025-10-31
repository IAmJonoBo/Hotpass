/**
 * Telemetry Strip Component
 *
 * Compact status bar showing environment, agent activity, API health, and failed runs.
 */

import { useQuery } from '@tanstack/react-query'
import { formatDistanceToNow } from 'date-fns'
import { Activity, AlertTriangle, CheckCircle, Server, Clock } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { prefectApi } from '@/api/prefect'
import { marquezApi } from '@/api/marquez'

interface TelemetryStripProps {
  className?: string
}

export function TelemetryStrip({ className }: TelemetryStripProps) {
  const environment = import.meta.env.VITE_ENVIRONMENT || 'local'

  // Check if telemetry is enabled (from localStorage/Admin)
  const telemetryEnabled =
    typeof window !== 'undefined' &&
    localStorage.getItem('hotpass_telemetry_enabled') !== 'false'

  // Fetch recent flow runs to check for failures
  const { data: flowRuns = [] } = useQuery({
    queryKey: ['telemetry-flow-runs'],
    queryFn: async () => {
      try {
        return await prefectApi.getFlowRuns({ limit: 100 })
      } catch (error) {
        console.warn('Telemetry: Failed to fetch flow runs:', error)
        return []
      }
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    enabled: telemetryEnabled,
  })

  // Check Prefect API health
  const { data: prefectHealth, isLoading: prefectLoading } = useQuery({
    queryKey: ['telemetry-prefect-health'],
    queryFn: async () => {
      try {
        await prefectApi.getFlows(1)
        return { status: 'healthy', timestamp: new Date() }
      } catch (error) {
        console.warn('Telemetry: Prefect health check failed:', error)
        return { status: 'error', timestamp: new Date() }
      }
    },
    refetchInterval: 60000, // Check every minute
    enabled: telemetryEnabled,
  })

  // Check Marquez API health
  const { data: marquezHealth, isLoading: marquezLoading } = useQuery({
    queryKey: ['telemetry-marquez-health'],
    queryFn: async () => {
      try {
        await marquezApi.getNamespaces()
        return { status: 'healthy', timestamp: new Date() }
      } catch (error) {
        console.warn('Telemetry: Marquez health check failed:', error)
        return { status: 'error', timestamp: new Date() }
      }
    },
    refetchInterval: 60000, // Check every minute
    enabled: telemetryEnabled,
  })

  if (!telemetryEnabled) {
    return null
  }

  // Calculate failed runs in last 30 minutes
  const thirtyMinutesAgo = Date.now() - 30 * 60 * 1000
  const recentFailedRuns = flowRuns.filter(run => {
    const runTime = new Date(run.created).getTime()
    return runTime >= thirtyMinutesAgo && run.state_type === 'FAILED'
  }).length

  const hasIssues = recentFailedRuns > 0 ||
    prefectHealth?.status === 'error' ||
    marquezHealth?.status === 'error'

  return (
    <div
      className={cn(
        'border-b bg-muted/30 px-6 py-2 text-xs flex items-center justify-between',
        className
      )}
    >
      {/* Left side - Status indicators */}
      <div className="flex items-center gap-4">
        {/* Environment */}
        <div className="flex items-center gap-2">
          <Server className="h-3 w-3 text-muted-foreground" />
          <span className="text-muted-foreground">Environment:</span>
          <Badge variant="outline" className="text-xs">
            {environment}
          </Badge>
        </div>

        {/* Prefect Status */}
        <div className="flex items-center gap-2">
          {prefectLoading ? (
            <Clock className="h-3 w-3 text-muted-foreground animate-spin" />
          ) : prefectHealth?.status === 'healthy' ? (
            <CheckCircle className="h-3 w-3 text-green-600 dark:text-green-400" />
          ) : (
            <AlertTriangle className="h-3 w-3 text-red-600 dark:text-red-400" />
          )}
          <span className="text-muted-foreground">Prefect:</span>
          <span className={cn(
            prefectHealth?.status === 'healthy'
              ? 'text-green-600 dark:text-green-400'
              : 'text-red-600 dark:text-red-400'
          )}>
            {prefectHealth?.status || 'checking...'}
          </span>
        </div>

        {/* Marquez Status */}
        <div className="flex items-center gap-2">
          {marquezLoading ? (
            <Clock className="h-3 w-3 text-muted-foreground animate-spin" />
          ) : marquezHealth?.status === 'healthy' ? (
            <CheckCircle className="h-3 w-3 text-green-600 dark:text-green-400" />
          ) : (
            <AlertTriangle className="h-3 w-3 text-red-600 dark:text-red-400" />
          )}
          <span className="text-muted-foreground">Marquez:</span>
          <span className={cn(
            marquezHealth?.status === 'healthy'
              ? 'text-green-600 dark:text-green-400'
              : 'text-red-600 dark:text-red-400'
          )}>
            {marquezHealth?.status || 'checking...'}
          </span>
        </div>

        {/* Failed Runs */}
        {recentFailedRuns > 0 && (
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-3 w-3 text-yellow-600 dark:text-yellow-400" />
            <span className="text-yellow-600 dark:text-yellow-400 font-medium">
              {recentFailedRuns} failed run{recentFailedRuns > 1 ? 's' : ''} (30m)
            </span>
          </div>
        )}
      </div>

      {/* Right side - Last update */}
      <div className="flex items-center gap-2">
        {hasIssues && (
          <Badge variant="outline" className="text-xs bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20">
            <Activity className="h-3 w-3 mr-1" />
            Action Required
          </Badge>
        )}
        <span className="text-muted-foreground">
          Last poll:{' '}
          {prefectHealth?.timestamp
            ? formatDistanceToNow(prefectHealth.timestamp, { addSuffix: true })
            : 'never'}
        </span>
      </div>
    </div>
  )
}
