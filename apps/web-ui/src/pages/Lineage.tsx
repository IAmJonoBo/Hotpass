/**
 * Lineage Page
 *
 * Visualizes data lineage from Marquez/OpenLineage backend.
 * Shows jobs, datasets, and their relationships with filtering capabilities.
 *
 * ASSUMPTION: This is a simplified view. A production version would use a graph
 * visualization library like react-flow or d3 for better UX.
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, GitBranch, Database, Activity } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { marquezApi, mockMarquezData } from '@/api/marquez'
import { cn } from '@/lib/utils'

export function Lineage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedNamespace, setSelectedNamespace] = useState<string>('hotpass')

  // Fetch namespaces
  const { data: namespaces = [] } = useQuery({
    queryKey: ['namespaces'],
    queryFn: () => marquezApi.getNamespaces(),
    placeholderData: mockMarquezData.namespaces,
  })

  // Fetch jobs in selected namespace
  const { data: jobs = [], isLoading: isLoadingJobs } = useQuery({
    queryKey: ['jobs', selectedNamespace],
    queryFn: () => marquezApi.getJobs(selectedNamespace),
    placeholderData: mockMarquezData.jobs,
    enabled: !!selectedNamespace,
  })

  // Fetch datasets in selected namespace
  const { data: datasets = [], isLoading: isLoadingDatasets } = useQuery({
    queryKey: ['datasets', selectedNamespace],
    queryFn: () => marquezApi.getDatasets(selectedNamespace),
    placeholderData: [],
    enabled: !!selectedNamespace,
  })

  // Filter jobs and datasets by search term
  const filteredJobs = jobs.filter(job =>
    job.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    job.namespace.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const filteredDatasets = datasets.filter(dataset =>
    dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    dataset.namespace.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Data Lineage</h1>
        <p className="text-muted-foreground">
          Explore job and dataset relationships from OpenLineage events
        </p>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            {/* Namespace selector */}
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Namespace</label>
              <div className="flex gap-2">
                {namespaces.map((ns) => (
                  <Button
                    key={ns.name}
                    variant={selectedNamespace === ns.name ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedNamespace(ns.name)}
                  >
                    {ns.name}
                  </Button>
                ))}
              </div>
            </div>

            {/* Search */}
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Search</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search jobs or datasets..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobs.length}</div>
            <p className="text-xs text-muted-foreground">
              {filteredJobs.length} matching filters
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Datasets</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{datasets.length}</div>
            <p className="text-xs text-muted-foreground">
              {filteredDatasets.length} matching filters
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Namespaces</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{namespaces.length}</div>
            <p className="text-xs text-muted-foreground">Active environments</p>
          </CardContent>
        </Card>
      </div>

      {/* Jobs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Jobs</CardTitle>
          <CardDescription>
            Pipeline jobs tracked by OpenLineage
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingJobs ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-sm text-muted-foreground">Loading jobs...</div>
            </div>
          ) : filteredJobs.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-sm text-muted-foreground">
                No jobs found{searchTerm && ' matching your search'}
              </div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Job Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Namespace</TableHead>
                  <TableHead>Latest Run</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredJobs.map((job) => (
                  <TableRow key={`${job.namespace}:${job.name}`}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Activity className="h-4 w-4 text-muted-foreground" />
                        {job.name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{job.type}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{job.namespace}</Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {job.latestRun ? (
                        new Date(job.latestRun.updatedAt).toLocaleString()
                      ) : (
                        <span>No runs</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {job.latestRun ? (
                        <Badge
                          variant="outline"
                          className={cn(
                            job.latestRun.state === 'COMPLETED'
                              ? 'text-green-600 dark:text-green-400'
                              : job.latestRun.state === 'FAILED'
                              ? 'text-red-600 dark:text-red-400'
                              : job.latestRun.state === 'RUNNING'
                              ? 'text-blue-600 dark:text-blue-400'
                              : 'text-gray-600 dark:text-gray-400'
                          )}
                        >
                          {job.latestRun.state}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        View Lineage
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Datasets Table */}
      <Card>
        <CardHeader>
          <CardTitle>Datasets</CardTitle>
          <CardDescription>
            Data artifacts tracked across the pipeline
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingDatasets ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-sm text-muted-foreground">Loading datasets...</div>
            </div>
          ) : filteredDatasets.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-sm text-muted-foreground">
                No datasets found{searchTerm && ' matching your search'}
              </div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Dataset Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Namespace</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDatasets.map((dataset) => (
                  <TableRow key={`${dataset.namespace}:${dataset.name}`}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Database className="h-4 w-4 text-muted-foreground" />
                        {dataset.name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{dataset.type}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{dataset.namespace}</Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {dataset.sourceName}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        View Lineage
                      </Button>
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
