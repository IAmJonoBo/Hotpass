/**
 * Assistant Chat Console
 *
 * Interactive chat interface for the Hotpass assistant with tool execution capabilities.
 */

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { executeTool, type ToolResult, type ToolCall } from '@/agent/tools'
import { useQuery } from '@tanstack/react-query'
import { prefectApi } from '@/api/prefect'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  toolCall?: ToolCall
}

interface AssistantChatProps {
  className?: string
  initialMessage?: string
}

export function AssistantChat({ className, initialMessage }: AssistantChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I can help you with Hotpass operations. Try asking me to list flows, check lineage, or open a specific run.',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState(initialMessage || '')
  const [isProcessing, setIsProcessing] = useState(false)
  const [lastToolCall, setLastToolCall] = useState<ToolCall | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Fetch telemetry data
  const { data: flowRuns = [] } = useQuery({
    queryKey: ['flowRuns'],
    queryFn: async () => {
      try {
        return await prefectApi.getFlowRuns({ limit: 10 })
      } catch {
        return []
      }
    },
    refetchInterval: 15000, // Refresh every 15 seconds
  })

  const lastPollTime = new Date()
  const environment = import.meta.env.VITE_ENVIRONMENT || 'local'

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (initialMessage && messages.length === 1) {
      handleSendMessage(initialMessage)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialMessage])

  const handleSendMessage = async (messageText?: string) => {
    const text = messageText || input.trim()
    if (!text) return

    // Add user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsProcessing(true)

    // Simple command parsing and tool execution
    let toolResult: ToolResult | null = null
    let toolName = ''
    let toolArgs: Record<string, unknown> = {}

    try {
      const lowerText = text.toLowerCase()

      if (lowerText.includes('list flows') || lowerText.includes('show flows')) {
        toolName = 'listFlows'
        toolResult = await executeTool('listFlows')
      } else if (lowerText.includes('list lineage') || lowerText.includes('show lineage')) {
        toolName = 'listLineage'
        const namespaceMatch = text.match(/namespace[:\s]+(\w+)/i)
        toolArgs = namespaceMatch ? { namespace: namespaceMatch[1] } : {}
        toolResult = await executeTool('listLineage', toolArgs)
      } else if (lowerText.includes('open run') || lowerText.includes('show run')) {
        toolName = 'openRun'
        const runIdMatch = text.match(/run[:\s]+(\S+)/i)
        if (runIdMatch) {
          toolArgs = { runId: runIdMatch[1] }
          toolResult = await executeTool('openRun', toolArgs)
        }
      } else if (lowerText.includes('get runs') || lowerText.includes('flow runs')) {
        toolName = 'getFlowRuns'
        toolResult = await executeTool('getFlowRuns')
      }

      // Create tool call record
      const toolCall: ToolCall | undefined = toolResult
        ? {
            id: `tool-${Date.now()}`,
            tool: toolName,
            timestamp: new Date(),
            result: toolResult,
          }
        : undefined

      if (toolCall) {
        setLastToolCall(toolCall)
      }

      // Generate assistant response
      let responseContent = ''
      if (toolResult) {
        if (toolResult.success) {
          responseContent = `✓ ${toolResult.message}`
          if (toolName === 'listFlows' && toolResult.data) {
            const flows = toolResult.data as { name: string }[]
            responseContent += `\n\nAvailable flows:\n${flows.map(f => `• ${f.name}`).join('\n')}`
          } else if (toolName === 'listLineage' && toolResult.data) {
            const jobs = toolResult.data as { name: string }[]
            responseContent += `\n\nJobs:\n${jobs.slice(0, 5).map(j => `• ${j.name}`).join('\n')}`
          } else if (toolName === 'openRun' && toolResult.data) {
            const { runId } = toolResult.data as { runId: string }
            responseContent += `\n\nNavigating to run ${runId}...`
          } else if (toolName === 'getFlowRuns' && toolResult.data) {
            const runs = toolResult.data as { name: string; state_name: string }[]
            responseContent += `\n\nRecent runs:\n${runs.slice(0, 5).map(r => `• ${r.name} - ${r.state_name}`).join('\n')}`
          }
        } else {
          responseContent = `✗ ${toolResult.message}`
          if (toolResult.error) {
            responseContent += `\n\nError: ${toolResult.error}`
          }
        }
      } else {
        responseContent = "I understand you want help, but I didn't recognize a specific command. Try:\n• 'list flows'\n• 'list lineage'\n• 'open run [id]'\n• 'get runs'"
      }

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: responseContent,
        timestamp: new Date(),
        toolCall,
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsProcessing(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <Card className={cn('flex flex-col', className)}>
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          Hotpass Assistant
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4" style={{ maxHeight: '500px' }}>
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex gap-3',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
              </div>
            )}
            <div
              className={cn(
                'flex flex-col gap-1 max-w-[80%]',
                message.role === 'user' ? 'items-end' : 'items-start'
              )}
            >
              <div
                className={cn(
                  'rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                )}
              >
                {message.content}
              </div>
              <span className="text-xs text-muted-foreground">
                {formatDistanceToNow(message.timestamp, { addSuffix: true })}
              </span>
              {message.toolCall && (
                <Badge variant="outline" className="text-xs">
                  Tool: {message.toolCall.tool}
                </Badge>
              )}
            </div>
            {message.role === 'user' && (
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-accent flex items-center justify-center">
                  <User className="h-4 w-4" />
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </CardContent>

      <CardFooter className="border-t p-4 flex-col gap-3">
        {/* Tool call indicator */}
        {lastToolCall && (
          <div className="w-full text-xs text-muted-foreground bg-muted rounded-lg p-2">
            <div className="font-medium">Last action:</div>
            <div className="mt-1">
              Tool <code className="bg-background px-1 py-0.5 rounded">{lastToolCall.tool}</code> executed{' '}
              {formatDistanceToNow(lastToolCall.timestamp, { addSuffix: true })}
              {lastToolCall.result && (
                <span className={cn(lastToolCall.result.success ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400')}>
                  {' '}• {lastToolCall.result.success ? 'Success' : 'Failed'}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Telemetry footer */}
        <div className="w-full text-xs text-muted-foreground border-t pt-2 space-y-1">
          <div className="flex justify-between">
            <span>Last poll from Prefect: {formatDistanceToNow(lastPollTime, { addSuffix: true })}</span>
            <Badge variant="outline" className="text-xs">{flowRuns.length} recent runs</Badge>
          </div>
          <div className="flex justify-between">
            <span>Lineage source: Marquez (namespace: hotpass)</span>
            <span>Environment: <Badge variant="outline" className="text-xs">{environment}</Badge></span>
          </div>
        </div>

        {/* Input */}
        <div className="flex gap-2 w-full">
          <Input
            placeholder="Ask me about flows, lineage, or runs..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isProcessing}
            className="flex-1"
          />
          <Button
            onClick={() => handleSendMessage()}
            disabled={isProcessing || !input.trim()}
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  )
}
