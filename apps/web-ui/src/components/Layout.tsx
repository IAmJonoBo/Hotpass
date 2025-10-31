import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { AssistantDrawer } from './assistant/AssistantDrawer'

export function Layout() {
  const [assistantOpen, setAssistantOpen] = useState(false)
  const [assistantMessage, setAssistantMessage] = useState<string>()

  // Get environment from env var or localStorage config
  const environment = import.meta.env.VITE_ENVIRONMENT ||
    (typeof window !== 'undefined' && localStorage.getItem('hotpass_environment')) ||
    'local'

  const openAssistant = (message?: string) => {
    setAssistantMessage(message)
    setAssistantOpen(true)
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar
        environment={environment}
        onOpenAssistant={openAssistant}
      />
      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto p-6 max-w-7xl">
          <Outlet context={{ openAssistant }} />
        </div>
      </main>
      <AssistantDrawer
        open={assistantOpen}
        onOpenChange={setAssistantOpen}
        initialMessage={assistantMessage}
      />
    </div>
  )
}
