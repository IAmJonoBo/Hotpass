/**
 * Assistant Page
 *
 * Full-page view of the Hotpass assistant chat console.
 */

import { AssistantChat } from '@/components/assistant/AssistantChat'

export function Assistant() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Assistant</h1>
        <p className="text-muted-foreground">
          Chat with the Hotpass assistant to explore flows, lineage, and runs
        </p>
      </div>

      <div className="max-w-4xl mx-auto">
        <AssistantChat className="h-[calc(100vh-200px)]" />
      </div>
    </div>
  )
}
