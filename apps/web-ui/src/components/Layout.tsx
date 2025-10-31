import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'

export function Layout() {
  // Get environment from env var or localStorage config
  const environment = import.meta.env.VITE_ENVIRONMENT ||
    (typeof window !== 'undefined' && localStorage.getItem('hotpass_environment')) ||
    'local'

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar environment={environment} />
      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto p-6 max-w-7xl">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
