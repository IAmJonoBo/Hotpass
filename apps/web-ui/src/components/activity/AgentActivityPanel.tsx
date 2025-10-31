/**
 * Agent Activity Panel
 *
 * Side panel showing recent agent actions and tool calls.
 */

import { formatDistanceToNow } from 'date-fns'
import { Activity, Wrench, MessageSquare, CheckCircle, XCircle } from 'lucide-react'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetBody } from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface AgentAction {
  id: string
  type: 'tool_call' | 'approval' | 'chat' | 'navigation'
  tool?: string
  message?: string
  success: boolean
  timestamp: Date
  operator?: string
}

interface AgentActivityPanelProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

// Mock data - in production this would come from a store
const mockActions: AgentAction[] = [
  {
    id: '1',
    type: 'tool_call',
    tool: 'listFlows',
    success: true,
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
  },
  {
    id: '2',
    type: 'approval',
    message: 'Approved run-001',
    success: true,
    timestamp: new Date(Date.now() - 10 * 60 * 1000),
    operator: 'current-user',
  },
  {
    id: '3',
    type: 'chat',
    message: 'Asked about flow runs',
    success: true,
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
  },
  {
    id: '4',
    type: 'tool_call',
    tool: 'getFlowRuns',
    success: true,
    timestamp: new Date(Date.now() - 20 * 60 * 1000),
  },
  {
    id: '5',
    type: 'navigation',
    message: 'Navigated to run details',
    success: true,
    timestamp: new Date(Date.now() - 25 * 60 * 1000),
  },
  {
    id: '6',
    type: 'tool_call',
    tool: 'listLineage',
    success: false,
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
  },
  {
    id: '7',
    type: 'approval',
    message: 'Rejected run-002',
    success: true,
    timestamp: new Date(Date.now() - 35 * 60 * 1000),
    operator: 'current-user',
  },
  {
    id: '8',
    type: 'chat',
    message: 'Listed all flows',
    success: true,
    timestamp: new Date(Date.now() - 40 * 60 * 1000),
  },
  {
    id: '9',
    type: 'tool_call',
    tool: 'openRun',
    success: true,
    timestamp: new Date(Date.now() - 45 * 60 * 1000),
  },
  {
    id: '10',
    type: 'navigation',
    message: 'Opened lineage page',
    success: true,
    timestamp: new Date(Date.now() - 50 * 60 * 1000),
  },
]

export function AgentActivityPanel({ open, onOpenChange }: AgentActivityPanelProps) {
  const getActionIcon = (type: string) => {
    switch (type) {
      case 'tool_call':
        return Wrench
      case 'approval':
        return CheckCircle
      case 'chat':
        return MessageSquare
      case 'navigation':
        return Activity
      default:
        return Activity
    }
  }

  const getActionLabel = (action: AgentAction) => {
    if (action.tool) return `Tool: ${action.tool}`
    if (action.message) return action.message
    return action.type
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent>
        <SheetHeader onClose={() => onOpenChange(false)}>
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            <SheetTitle>Agent Activity</SheetTitle>
          </div>
        </SheetHeader>
        <SheetBody>
          <div className="space-y-1">
            {mockActions.map((action) => {
              const Icon = getActionIcon(action.type)

              return (
                <div
                  key={action.id}
                  className="border-l-2 border-muted pl-4 py-3 hover:bg-accent/50 transition-colors rounded-r"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-3 flex-1">
                      <div
                        className={cn(
                          'p-1.5 rounded-lg',
                          action.success
                            ? 'bg-green-500/10 text-green-600 dark:text-green-400'
                            : 'bg-red-500/10 text-red-600 dark:text-red-400'
                        )}
                      >
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">
                            {getActionLabel(action)}
                          </span>
                          {action.success ? (
                            <CheckCircle className="h-3 w-3 text-green-600 dark:text-green-400" />
                          ) : (
                            <XCircle className="h-3 w-3 text-red-600 dark:text-red-400" />
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Badge variant="outline" className="text-xs capitalize">
                            {action.type.replace('_', ' ')}
                          </Badge>
                          {action.operator && (
                            <>
                              <span>•</span>
                              <span>{action.operator}</span>
                            </>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {formatDistanceToNow(action.timestamp, { addSuffix: true })}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {mockActions.length === 0 && (
            <div className="flex items-center justify-center py-12 text-center">
              <div>
                <Activity className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No recent activity</p>
              </div>
            </div>
          )}
        </SheetBody>
      </SheetContent>
    </Sheet>
  )
}
