'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, useEffect } from 'react'

// Suppress unhandled runtime errors thrown by external browser extensions
if (typeof window !== 'undefined') {
  window.addEventListener(
    'error',
    (event) => {
      const filename = event.filename || ''
      const msg = typeof event.message === 'string' ? event.message : ''
      if (
        filename.includes('chrome-extension://') ||
        msg.includes('chrome-extension://') ||
        msg.includes('Window message') ||
        msg.includes('call method')
      ) {
        event.stopImmediatePropagation()
        event.preventDefault()
      }
    },
    true
  )

  window.addEventListener(
    'unhandledrejection',
    (event) => {
      const reason = event.reason
      const msg = (reason && reason.message) || String(reason || '')
      const stack = (reason && reason.stack) || ''
      if (
        msg.includes('chrome-extension://') ||
        stack.includes('chrome-extension://') ||
        msg.includes('Window message') ||
        msg.includes('call method')
      ) {
        event.stopImmediatePropagation()
        event.preventDefault()
      }
    },
    true
  )
}

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30000,
            retry: 1,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
