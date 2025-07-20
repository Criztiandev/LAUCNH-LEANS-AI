import { describe, it, expect, vi, beforeEach } from 'vitest'
import { appRouter } from '@/lib/trpc/root'
import { createTRPCContext } from '@/lib/trpc/server'

// Mock database
vi.mock('@/lib/db', () => ({
  db: {
    select: vi.fn().mockReturnValue({
      from: vi.fn().mockReturnValue({
        where: vi.fn().mockReturnValue({
          orderBy: vi.fn().mockResolvedValue([
            {
              id: 'test-validation-1',
              userId: 'user-123',
              title: 'Test Validation 1',
              ideaText: 'This is a test validation idea',
              status: 'completed',
              marketScore: '8.5',
              createdAt: new Date('2024-01-01'),
              completedAt: new Date('2024-01-02'),
              competitorCount: 5,
              feedbackCount: 12,
              sourcesScraped: ['product-hunt', 'reddit']
            },
            {
              id: 'test-validation-2',
              userId: 'user-123',
              title: 'Test Validation 2',
              ideaText: 'Another test validation idea',
              status: 'processing',
              marketScore: null,
              createdAt: new Date('2024-01-03'),
              completedAt: null,
              competitorCount: 0,
              feedbackCount: 0,
              sourcesScraped: []
            }
          ])
        })
      })
    })
  }
}))

// Mock Supabase
vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getUser: vi.fn(),
      signOut: vi.fn().mockResolvedValue({ error: null })
    }
  }
}))

describe('tRPC End-to-End', () => {
  let mockSupabase: {
    auth: {
      getUser: ReturnType<typeof vi.fn>
      signOut: ReturnType<typeof vi.fn>
    }
  }

  beforeEach(async () => {
    vi.clearAllMocks()
    const { supabase } = await import('@/lib/supabase')
    mockSupabase = supabase
  })

  it('should handle complete validation workflow', async () => {
    // Setup authenticated user
    mockSupabase.auth.getUser.mockResolvedValue({
      data: { user: { id: 'user-123', email: 'test@example.com' } },
      error: null
    })

    const headers = new Headers()
    headers.set('authorization', 'Bearer valid-token')
    
    const ctx = await createTRPCContext({ headers })
    const caller = appRouter.createCaller(ctx)

    // Test getting user's validations
    const validations = await caller.validations.getAll()
    
    expect(validations).toHaveLength(2)
    expect(validations[0]).toMatchObject({
      id: 'test-validation-1',
      title: 'Test Validation 1',
      status: 'completed',
      marketScore: '8.5'
    })
    expect(validations[1]).toMatchObject({
      id: 'test-validation-2',
      title: 'Test Validation 2',
      status: 'processing',
      marketScore: null
    })
  })

  it('should handle authentication flow', async () => {
    // Test unauthenticated session
    const headers = new Headers()
    const ctx = await createTRPCContext({ headers })
    const caller = appRouter.createCaller(ctx)

    const session = await caller.auth.getSession()
    expect(session.user).toBeNull()

    // Test authenticated session
    mockSupabase.auth.getUser.mockResolvedValue({
      data: { user: { id: 'user-123', email: 'test@example.com' } },
      error: null
    })

    const authHeaders = new Headers()
    authHeaders.set('authorization', 'Bearer valid-token')
    
    const authCtx = await createTRPCContext({ headers: authHeaders })
    const authCaller = appRouter.createCaller(authCtx)

    const authSession = await authCaller.auth.getSession()
    expect(authSession.user).toEqual({
      id: 'user-123',
      email: 'test@example.com'
    })
  })

  it('should handle sign out', async () => {
    mockSupabase.auth.getUser.mockResolvedValue({
      data: { user: { id: 'user-123', email: 'test@example.com' } },
      error: null
    })

    const headers = new Headers()
    headers.set('authorization', 'Bearer valid-token')
    
    const ctx = await createTRPCContext({ headers })
    const caller = appRouter.createCaller(ctx)

    const result = await caller.auth.signOut()
    expect(result).toEqual({ success: true })
    expect(mockSupabase.auth.signOut).toHaveBeenCalled()
  })
})