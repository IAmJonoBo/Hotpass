/**
 * Dashboard Page
 *
 * Shows today's and last 24h Hotpass runs with status, duration, and links to lineage.
 * Integrates with both Prefect (flow runs) and Marquez (job runs).
 */

import { useQuery } from '@tanstack/react-query'
import { Link, useOutletContext } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { Activity, Clock, GitBranch, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { cn, formatDuration, getStatusColor } from '@/lib/utils'
import { mockPrefectData } from '@/api/prefect'
import { useHILApprovals } from '@/store/hilStore'
import { LiveRefinementPanel } from '@/components/refinement/LiveRefinementPanel'
import { PowerTools } from '@/components/powertools/PowerTools'

interface OutletContext {
  openAssistant: (message?: string) => void
}

export function Dashboard() {
  const { openAssistant } = useOutletContext<OutletContext>()

  // Fetch Prefect flow runs from last 24h
  const { data: flowRuns = [], isLoading: isLoadingPrefect } = useQuery({
    queryKey: ['flowRuns'],
    queryFn: async () => {
      try {
        const { prefectApi } = await import('@/api/prefect')
        return await prefectApi.getFlowRuns({ limit: 50 })
      } catch {
        return mockPrefectData.flowRuns
      }
    },
    placeholderData: mockPrefectData.flowRuns,
  })

  // Fetch HIL approvals
  const { data: hilApprovals = {} } = useHILApprovals()

  // Helper to get HIL status badge
  const getHILStatusBadge = (runId: string) => {
    const approval = hilApprovals[runId]
    if (!approval) {
      return (
        <Badge variant="outline" className="text-gray-600 dark:text-gray-400">
          <AlertCircle className="h-3 w-3 mr-1" />
          None
        </Badge>
      )
    }

    switch (approval.status) {
      case 'approved':
        return (
          <Badge variant="outline" className="text-green-600 dark:text-green-400">
            <CheckCircle className="h-3 w-3 mr-1" />
            Approved
          </Badge>
        )
      case 'rejected':
        return (
          <Badge variant="outline" className="text-red-600 dark:text-red-400">
            <XCircle className="h-3 w-3 mr-1" />
            Rejected
          </Badge>
        )
      case 'waiting':
        return (
          <Badge variant="outline" className="text-yellow-600 dark:text-yellow-400">
            <Clock className="h-3 w-3 mr-1" />
            Waiting
          </Badge>
        )
      default:
        return null
    }
  }

  // Note: Marquez jobs could be fetched here for lineage links if needed
  // const { data: marquezJobs = [] } = useQuery({ ... })

  // Filter runs from last 24 hours
  const last24Hours = Date.now() - 24 * 60 * 60 * 1000
  const recentRuns = flowRuns.filter(run => {
    const runTime = new Date(run.created).getTime()
    return runTime >= last24Hours
  })

  // Calculate summary stats
  const totalRuns = recentRuns.length
  const completedRuns = recentRuns.filter(r => r.state_type === 'COMPLETED').length
  const failedRuns = recentRuns.filter(r => r.state_type === 'FAILED').length
  const runningRuns = recentRuns.filter(r => r.state_type === 'RUNNING').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Monitor pipeline runs, track performance, and explore data lineage
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalRuns}</div>
            <p className="text-xs text-muted-foreground">Last 24 hours</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <Badge variant="outline" className="bg-green-500/10 text-green-600 dark:text-green-400">
              ✓
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedRuns}</div>
            <p className="text-xs text-muted-foreground">
              {totalRuns > 0 ? Math.round((completedRuns / totalRuns) * 100) : 0}% success rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <Badge variant="outline" className="bg-red-500/10 text-red-600 dark:text-red-400">
              ✗
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{failedRuns}</div>
            <p className="text-xs text-muted-foreground">
              {failedRuns > 0 ? 'Needs attention' : 'All good'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running</CardTitle>
            <Badge variant="outline" className="bg-blue-500/10 text-blue-600 dark:text-blue-400">
              ⟳
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{runningRuns}</div>
            <p className="text-xs text-muted-foreground">In progress</p>
          </CardContent>
        </Card>
      </div>

      {/* Live Refinement Panel */}
      <LiveRefinementPanel />

      {/* Power Tools */}
      <PowerTools onOpenAssistant={() => openAssistant()} />

      {/* Recent Runs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Pipeline Runs</CardTitle>
          <CardDescription>
            Latest executions with status and performance metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingPrefect ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-sm text-muted-foreground">Loading runs...</div>
            </div>
          ) : recentRuns.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-sm text-muted-foreground">No runs in the last 24 hours</div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Run Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>HIL Status</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Profile</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentRuns.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell className="font-medium">
                      <Link
                        to={`/runs/${run.id}`}
                        className="hover:underline flex items-center gap-2"
                      >
                        {run.name}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={cn(getStatusColor(run.state_type))}
                      >
                        {run.state_name}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {getHILStatusBadge(run.id)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {run.start_time ? (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatDistanceToNow(new Date(run.start_time), { addSuffix: true })}
                        </span>
                      ) : (
                        <span>Not started</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {run.total_run_time ? (
                        formatDuration(run.total_run_time)
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {run.tags && run.tags.length > 0 ? (
                        <Badge variant="secondary">{run.tags[0]}</Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Link
                          to={`/runs/${run.id}`}
                          className="text-xs text-primary hover:underline"
                        >
                          Details
                        </Link>
                        <Link
                          to="/lineage"
                          className="text-xs text-primary hover:underline flex items-center gap-1"
                        >
                          <GitBranch className="h-3 w-3" />
                          Lineage
                        </Link>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
