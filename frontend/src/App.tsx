/**
 * App.tsx - Roteamento principal da aplicacao.
 */
import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from './store/authStore'
import { tenantApi } from './api/endpoints'

import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import AgendaPage from './pages/AgendaPage'
import KanbanPage from './pages/KanbanPage'
import LiderDashboardPage from './pages/LiderDashboardPage'
import RelatoriosPage from './pages/RelatoriosPage'
import AdminPage from './pages/AdminPage'
import Layout from './components/Layout'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s: any) => s.isAuthenticated)
  if (!isAuthenticated()) return <Navigate to="/login" replace />
  return <>{children}</>
}

function App() {
  const setTenant = useAuthStore((s: any) => s.setTenant)

  useEffect(() => {
    tenantApi.config().then(({ data }: { data: any }) => setTenant(data)).catch(() => {})
  }, [setTenant])

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="agenda" element={<AgendaPage />} />
            <Route path="kanban" element={<KanbanPage />} />
            <Route path="lider" element={<LiderDashboardPage />} />
            <Route path="relatorios" element={<RelatoriosPage />} />
            <Route path="admin" element={<AdminPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
