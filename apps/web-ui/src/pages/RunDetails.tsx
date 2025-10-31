/**
 * Run Details Page
 *
 * Shows detailed information about a specific pipeline run including:
 * - Raw OpenLineage event
 * - Related datasets
 * - QA results from dist/data-docs/ or Prefect
 * - Run parameters and metadata
 */

import { useParams, Link, useOutletContext } from 'react-router-dom'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, CheckCircle2, XCircle, AlertTriangle, Clock, Tag, UserCheck } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { prefectApi, mockPrefectData } from '@/api/prefect'
import { cn, formatDuration, getStatusColor } from '@/lib/utils'
import { ApprovalPanel } from '@/components/hil/ApprovalPanel'
import type { QAResult } from '@/types'

interface OutletContext {
  openAssistant: (message?: string) => void
}

export function RunDetails() {
  const { runId } = useParams<{ runId: string }>()
  const { openAssistant } = useOutletContext<OutletContext>()
  const [approvalPanelOpen, setApprovalPanelOpen] = useState(false)

  // Fetch run details
  const { data: run, isLoading } = useQuery({
    queryKey: ['flowRun', runId],
    queryFn: () => prefectApi.getFlowRun(runId!),
    placeholderData: mockPrefectData.flowRuns.find(r => r.id === runId),
    enabled: !!runId,
  })

  // Mock QA results (in production, these would come from dist/data-docs or the run artifacts)
  const mockQAResults: QAResult[] = [
    {
      check: 'Schema Validation',
      status: 'passed',
      message: 'All required columns present',
      details: { columns: 45, validated: 45 },
    },
    {
      check: 'Data Quality',
      status: 'passed',
      message: 'No duplicate records found',
      details: { total_rows: 1234, duplicates: 0 },
    },
    {
      check: 'Completeness',
      status: 'warning',
      message: '2% of records have missing phone numbers',
      details: { total: 1234, missing: 25 },
    },
    {
      check: 'Provenance',
      status: 'passed',
      message: 'All records have provenance metadata',
      details: { tracked: 1234 },
    },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-lg font-semibold">Loading run details...</div>
          <p className="text-sm text-muted-foreground mt-2">Please wait</p>
        </div>
      </div>
    )
  }

  if (!run) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-lg font-semibold">Run not found</div>
          <p className="text-sm text-muted-foreground mt-2">
            The requested run could not be found.
          </p>
          <Link to="/" className="mt-4 inline-block">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link to="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
            </Link>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">{run.name}</h1>
          <p className="text-muted-foreground">Run ID: {run.id}</p>
        </div>
        <Badge
          variant="outline"
          className={cn('text-base px-4 py-2', getStatusColor(run.state_type))}
        >
          {run.state_name}
        </Badge>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Duration</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {run.total_run_time ? formatDuration(run.total_run_time) : '-'}
            </div>
            <p className="text-xs text-muted-foreground">
              {run.start_time ? new Date(run.start_time).toLocaleString() : 'Not started'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Flow</CardTitle>
            <Tag className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium truncate">{run.flow_id}</div>
            <p className="text-xs text-muted-foreground">Flow ID</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tags</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-1">
              {run.tags && run.tags.length > 0 ? (
                run.tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))
              ) : (
                <span className="text-xs text-muted-foreground">No tags</span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">QA Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockQAResults.filter(r => r.status === 'passed').length}/{mockQAResults.length}
            </div>
            <p className="text-xs text-muted-foreground">Checks passed</p>
          </CardContent>
        </Card>
      </div>

      {/* QA Results */}
      <Card>
        <CardHeader>
          <CardTitle>Quality Assurance Results</CardTitle>
          <CardDescription>
            Validation checks from the pipeline execution
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Check</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Message</TableHead>
                <TableHead className="text-right">Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockQAResults.map((result, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{result.check}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {result.status === 'passed' && (
                        <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
                      )}
                      {result.status === 'failed' && (
                        <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
                      )}
                      {result.status === 'warning' && (
                        <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
                      )}
                      <Badge
                        variant="outline"
                        className={cn(
                          result.status === 'passed'
                            ? 'text-green-600 dark:text-green-400'
                            : result.status === 'failed'
                            ? 'text-red-600 dark:text-red-400'
                            : 'text-yellow-600 dark:text-yellow-400'
                        )}
                      >
                        {result.status}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell>{result.message}</TableCell>
                  <TableCell className="text-right text-sm text-muted-foreground">
                    {result.details && (
                      <code className="text-xs">
                        {JSON.stringify(result.details).slice(0, 50)}...
                      </code>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Run Parameters */}
      <Card>
        <CardHeader>
          <CardTitle>Run Parameters</CardTitle>
          <CardDescription>
            Configuration and inputs for this execution
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg bg-muted p-4">
            <pre className="text-sm overflow-x-auto">
              {JSON.stringify(run.parameters || {}, null, 2)}
            </pre>
          </div>
        </CardContent>
      </Card>

      {/* Raw Event Data */}
      <Card>
        <CardHeader>
          <CardTitle>Raw Event Data</CardTitle>
          <CardDescription>
            Complete run metadata from Prefect
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg bg-muted p-4">
            <pre className="text-sm overflow-x-auto">
              {JSON.stringify(run, null, 2)}
            </pre>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-between gap-2">
        <Button
          variant="default"
          onClick={() => setApprovalPanelOpen(true)}
        >
          <UserCheck className="mr-2 h-4 w-4" />
          Review & Approve
        </Button>
        <div className="flex gap-2">
          <Link to="/lineage">
            <Button variant="outline">View Lineage</Button>
          </Link>
          <Button>Rerun Pipeline</Button>
        </div>
      </div>

      {/* Approval Panel */}
      {run && (
        <ApprovalPanel
          open={approvalPanelOpen}
          onOpenChange={setApprovalPanelOpen}
          run={run}
          qaResults={mockQAResults}
          onOpenAssistant={openAssistant}
        />
      )}
    </div>
  )
}
