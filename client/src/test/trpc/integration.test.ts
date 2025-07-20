/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { TRPCError } from '@trpc/server'
import { appRouter } from '@/lib/trpc/root'
import { createTRPCContext } from '@/lib/trpc/server'

// Mock database
vi.mock('@/lib/db', () => ({
  db: {
    insert: vi.fn().mockReturnValue({
      values: vi.fn().mockImplementation((values) => ({
        returning: vi.fn().mockResolvedValue([{
          id: 'test-id',
          userId: values.userId || 'user-id',
          title: values.title || 'Test Validation',
          ideaText: values.ideaText || 'Test idea description',
          status: values.status || 'processing',
          createdAt: new Date(),
        }])
      }))
    }),
    select: vi.fn().mockReturnValue({
      from: vi.fn().mockReturnValue({
        where: vi.fn().mockReturnValue({
          orderBy: vi.fn().mockResolvedValue([]),
          limit: vi.fn().mockResolvedValue([])
        })
      })
    }),
    update: vi.fn().mockReturnValue({
      set: vi.fn().mockReturnValue({
        where: vi.fn().mockReturnValue({
          returning: vi.fn().mockResolvedValue([{
            id: 'test-id',
            status: 'completed',
          }])
        })
      })
    })
  }
}))

// Mock Supabase with different scenarios
vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getUser: vi.fn(),
      signOut: vi.fn().mockResolvedValue({ error: null })
    }
  }
}))

describe('tRPC Integration', () => {
  let mockSupabase: {
    auth: {
      getUser: ReturnType<typeof vi.fn>
      signOut: ReturnType<typeof vi.fn>
    }
  }

  beforeEach(async () => {
    vi.clearAllMocks()
    // Get the mocked supabase instance
    const { supabase } = await import('@/lib/supabase')
    mockSupabase = supabase
    
    // Reset mock implementations
    mockSupabase.auth.getUser.mockResolvedValue({
      data: { user: { id: 'user-id', email: 'test@example.com' } },
      error: null
    })
  })

  describe('Context Creation', () => {
    it('should create tRPC context with all required properties', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer test-token')
      
      const ctx = await createTRPCContext({ headers })
      
      expect(ctx).toHaveProperty('db')
      expect(ctx).toHaveProperty('supabase')
      expect(ctx).toHaveProperty('headers')
      expect(ctx.headers).toBe(headers)
    })

    it('should create context without authorization header', async () => {
      const headers = new Headers()
      
      const ctx = await createTRPCContext({ headers })
      
      expect(ctx).toHaveProperty('db')
      expect(ctx).toHaveProperty('supabase')
      expect(ctx).toHaveProperty('headers')
    })
  })

  describe('Authentication Middleware', () => {
    it('should allow public procedures without auth', async () => {
      const headers = new Headers()
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      const result = await caller.auth.getSession()
      
      expect(result).toHaveProperty('user')
      expect(result.user).toBeNull()
    })

    it('should return user session when valid token provided', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      mockSupabase.auth.getUser.mockResolvedValue({
        data: { user: { id: 'user-id', email: 'test@example.com' } },
        error: null
      })
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      const result = await caller.auth.getSession()
      
      expect(result).toHaveProperty('user')
      expect(result.user).toEqual({ id: 'user-id', email: 'test@example.com' })
    })

    it('should reject protected procedures without auth header', async () => {
      const headers = new Headers()
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      await expect(caller.validations.getAll()).rejects.toThrow(TRPCError)
      await expect(caller.validations.getAll()).rejects.toMatchObject({
        code: 'UNAUTHORIZED'
      })
    })

    it('should reject protected procedures with invalid token', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer invalid-token')
      
      mockSupabase.auth.getUser.mockResolvedValue({
        data: { user: null },
        error: { message: 'Invalid token' }
      })
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      await expect(caller.validations.getAll()).rejects.toThrow(TRPCError)
      await expect(caller.validations.getAll()).rejects.toMatchObject({
        code: 'UNAUTHORIZED'
      })
    })

    it('should allow protected procedures with valid auth', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      mockSupabase.auth.getUser.mockResolvedValue({
        data: { user: { id: 'user-id', email: 'test@example.com' } },
        error: null
      })
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      // Should not throw with valid auth
      const result = await caller.validations.getAll()
      expect(Array.isArray(result)).toBe(true)
    })

    it('should handle Bearer token extraction correctly', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer test-token-123')
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      try {
        await caller.validations.getAll()
      } catch {
        // Expected to fail, but should have called getUser with correct token
      }
      
      expect(mockSupabase.auth.getUser).toHaveBeenCalledWith('test-token-123')
    })
  })

  describe('Validation CRUD Operations', () => {
    beforeEach(() => {
      // Setup valid auth for validation tests
      mockSupabase.auth.getUser.mockResolvedValue({
        data: { user: { id: 'user-id', email: 'test@example.com' } },
        error: null
      })
    })

    it('should get validation by ID with related data', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      // Mock database responses for getById
      const { db } = await import('@/lib/db')
      
      // Mock validation query
      vi.mocked(db.select).mockReturnValueOnce({
        from: vi.fn().mockReturnValue({
          where: vi.fn().mockReturnValue({
            limit: vi.fn().mockResolvedValue([{
              id: '550e8400-e29b-41d4-a716-446655440000',
              userId: 'user-id',
              title: 'Test Validation',
              ideaText: 'Test idea description',
              status: 'completed',
              marketScore: '8.5',
              createdAt: new Date(),
              completedAt: new Date(),
              competitorCount: 3,
              feedbackCount: 5,
              sourcesScraped: ['product-hunt', 'reddit']
            }])
          })
        })
      } as any)

      // Mock competitors query
      vi.mocked(db.select).mockReturnValueOnce({
        from: vi.fn().mockReturnValue({
          where: vi.fn().mockResolvedValue([
            {
              id: '550e8400-e29b-41d4-a716-446655440001',
              validationId: '550e8400-e29b-41d4-a716-446655440000',
              name: 'Competitor 1',
              description: 'A competing product',
              website: 'https://competitor1.com',
              estimatedUsers: 1000,
              estimatedRevenue: '$10k/month',
              pricingModel: 'subscription',
              source: 'product-hunt',
              confidenceScore: '0.8'
            }
          ])
        })
      } as any)

      // Mock feedback query
      vi.mocked(db.select).mockReturnValueOnce({
        from: vi.fn().mockReturnValue({
          where: vi.fn().mockResolvedValue([
            {
              id: '550e8400-e29b-41d4-a716-446655440002',
              validationId: '550e8400-e29b-41d4-a716-446655440000',
              text: 'Great idea!',
              sentiment: 'positive',
              sentimentScore: '0.8',
              source: 'reddit',
              authorInfo: { username: 'user123' }
            }
          ])
        })
      } as any)

      // Mock AI analysis query
      vi.mocked(db.select).mockReturnValueOnce({
        from: vi.fn().mockReturnValue({
          where: vi.fn().mockReturnValue({
            limit: vi.fn().mockResolvedValue([{
              id: '550e8400-e29b-41d4-a716-446655440003',
              validationId: '550e8400-e29b-41d4-a716-446655440000',
              marketOpportunity: 'Strong market opportunity',
              competitiveAnalysis: 'Moderate competition',
              strategicRecommendations: 'Focus on differentiation',
              riskAssessment: 'Low to medium risk',
              gtmStrategy: 'Direct sales approach',
              featurePriorities: 'Core features first',
              executiveSummary: 'Promising opportunity'
            }])
          })
        })
      } as any)
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      const result = await caller.validations.getById({ id: '550e8400-e29b-41d4-a716-446655440000' })
      
      expect(result).toHaveProperty('validation')
      expect(result).toHaveProperty('competitors')
      expect(result).toHaveProperty('feedback')
      expect(result).toHaveProperty('aiAnalysis')
      
      expect(result.validation.id).toBe('550e8400-e29b-41d4-a716-446655440000')
      expect(result.competitors).toHaveLength(1)
      expect(result.feedback).toHaveLength(1)
      expect(result.aiAnalysis).toBeTruthy()
    })

    it('should reject getById for validation not owned by user', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      // Mock validation query returning validation owned by different user
      const { db } = await import('@/lib/db')
      vi.mocked(db.select).mockReturnValueOnce({
        from: vi.fn().mockReturnValue({
          where: vi.fn().mockReturnValue({
            limit: vi.fn().mockResolvedValue([{
              id: '550e8400-e29b-41d4-a716-446655440004',
              userId: 'different-user-id', // Different user
              title: 'Test Validation',
              ideaText: 'Test idea description',
              status: 'completed'
            }])
          })
        })
      } as any)
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      await expect(caller.validations.getById({ id: '550e8400-e29b-41d4-a716-446655440004' }))
        .rejects.toThrow('Validation not found')
    })

    it('should reject getById for non-existent validation', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      // Mock validation query returning empty result
      const { db } = await import('@/lib/db')
      vi.mocked(db.select).mockReturnValueOnce({
        from: vi.fn().mockReturnValue({
          where: vi.fn().mockReturnValue({
            limit: vi.fn().mockResolvedValue([]) // Empty result
          })
        })
      } as any)
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      await expect(caller.validations.getById({ id: '550e8400-e29b-41d4-a716-446655440005' }))
        .rejects.toThrow('Validation not found')
    })

    it('should update validation status', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      const result = await caller.validations.updateStatus({
        id: '550e8400-e29b-41d4-a716-446655440006',
        status: 'completed',
        marketScore: 8.5,
        completedAt: new Date()
      })
      
      expect(result).toHaveProperty('id', 'test-id')
      expect(result).toHaveProperty('status', 'completed')
    })
  })

  describe('Input Validation', () => {
    beforeEach(() => {
      // Setup valid auth for validation tests
      mockSupabase.auth.getUser.mockResolvedValue({
        data: { user: { id: 'user-id', email: 'test@example.com' } },
        error: null
      })
    })

    it('should validate validation creation input - title too short', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      await expect(caller.validations.create({
        title: '', // Invalid: too short
        ideaText: 'This is a valid idea description that is long enough'
      })).rejects.toThrow()
    })

    it('should validate validation creation input - title too long', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      const longTitle = 'a'.repeat(256) // 256 chars, exceeds 255 limit
      
      await expect(caller.validations.create({
        title: longTitle,
        ideaText: 'This is a valid idea description that is long enough'
      })).rejects.toThrow()
    })

    it('should validate validation creation input - idea text too short', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      await expect(caller.validations.create({
        title: 'Valid Title',
        ideaText: 'Short' // Invalid: too short (less than 10 chars)
      })).rejects.toThrow()
    })

    it('should validate validation creation input - idea text too long', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      const longIdeaText = 'a'.repeat(1001) // 1001 chars, exceeds 1000 limit
      
      await expect(caller.validations.create({
        title: 'Valid Title',
        ideaText: longIdeaText
      })).rejects.toThrow()
    })

    it('should accept valid validation creation input', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      const result = await caller.validations.create({
        title: 'Valid Title',
        ideaText: 'This is a valid idea description that meets all requirements'
      })
      
      expect(result).toHaveProperty('id')
      expect(result).toHaveProperty('title', 'Valid Title')
      expect(result).toHaveProperty('status', 'processing')
    })
  })

  describe('Auth Router', () => {
    it('should handle signOut successfully', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      mockSupabase.auth.getUser.mockResolvedValue({
        data: { user: { id: 'user-id', email: 'test@example.com' } },
        error: null
      })
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      const result = await caller.auth.signOut()
      
      expect(result).toEqual({ success: true })
      expect(mockSupabase.auth.signOut).toHaveBeenCalled()
    })

    it('should handle signOut failure', async () => {
      const headers = new Headers()
      headers.set('authorization', 'Bearer valid-token')
      
      mockSupabase.auth.getUser.mockResolvedValue({
        data: { user: { id: 'user-id', email: 'test@example.com' } },
        error: null
      })
      
      mockSupabase.auth.signOut.mockResolvedValue({
        error: { message: 'Sign out failed' }
      })
      
      const ctx = await createTRPCContext({ headers })
      const caller = appRouter.createCaller(ctx)
      
      await expect(caller.auth.signOut()).rejects.toThrow('Failed to sign out')
    })
  })
})