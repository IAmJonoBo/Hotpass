import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Lineage } from './pages/Lineage'
import { RunDetails } from './pages/RunDetails'
import { Admin } from './pages/Admin'
import { Health } from './pages/Health'
import { Assistant } from './pages/Assistant'
import './index.css'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000, // 30 seconds
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/lineage" element={<Lineage />} />
            <Route path="/assistant" element={<Assistant />} />
            <Route path="/health" element={<Health />} />
            <Route path="/runs/:runId" element={<RunDetails />} />
            <Route path="/admin" element={<Admin />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
