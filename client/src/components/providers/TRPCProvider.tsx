'use client'

import { useState, useMemo } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { httpBatchLink } from '@trpc/client'
import { trpc } from '@/lib/trpc/client'
import { useAuth } from './AuthProvider'
import superjson from 'superjson'

export function TRPCProvider({ children }: { children: React.ReactNode }) {
  const { session } = useAuth()
  
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes
        retry: (failureCount, error: unknown) => {
          // Don't retry on auth errors
          if (error && typeof error === 'object' && 'data' in error) {
            const errorData = error.data as { code?: string }
            if (errorData?.code === 'UNAUTHORIZED') {
              return false
            }
          }
          return failureCount < 3
        },
      },
    },
  }))
  
  const trpcClient = useMemo(() =>
    trpc.createClient({
      links: [
        httpBatchLink({
          url: '/api/trpc',
          transformer: superjson,
          headers() {
            return {
              authorization: session?.access_token ? `Bearer ${session.access_token}` : '',
            }
          },
        }),
      ],
    }),
    [session?.access_token]
  )

  return (
    <trpc.Provider client={trpcClient} queryClient={queryClient}>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </trpc.Provider>
  )
}