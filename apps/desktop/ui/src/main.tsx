import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'
import { router } from './app/router'
import { LanguageGate } from '@/shared/ui/LanguageGate'
import { BackendGuard } from '@/shared/ui/BackendGuard'
import { ErrorBoundary } from '@/shared/ui/ErrorBoundary'
import { ToastContainer } from '@/shared/ui/ErrorToast'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <LanguageGate>
          <BackendGuard>
            <RouterProvider router={router} />
          </BackendGuard>
        </LanguageGate>
        <ToastContainer />
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>,
)
