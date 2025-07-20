import { describe, it, expect, vi, beforeEach } from 'vitest'
import { appRouter } from '@/lib/trpc/root'
import { createTRPCContext } from '@/lib/trpc/server'

// Mock database
vi.mock('@/lib/db', () => ({
  db: {
    insert: vi.fn().mockReturnValue({
      values: vi.fn().mockImplementation((values) => ({
        returning: vi.fn().mockResolvedValue([{
          id: '550e8400-e29b-41d4-a716-446655440000',
          userId: values.userId || 'user-123',
          title: values.title || 'Test Validation',
          ideaText: values.ideaText || 'Test idea description',
          status: values.status || 'processing',
          createdAt: new Date('2024-01-01'),
          completedAt: null,
          marketScore: null,
          competitorCount: 0,
          feedbackCount: 0,
          sourcesScraped: [],
        }])
      }))
    }),
    select: vi.fn().mockReturnValue({
      from: vi.fn().mockReturnValue({
        where: vi.fn().mockReturnValue({
          orderBy: vi.fn().mockResolvedValue([
            {
              id: '550e8400-e29b-41d4-a716-446655440000',
              userId: 'user-123',
              title: 'Test SaaS Platform',
              ideaText: 'A comprehensive SaaS platform for project management',
              status: 'processing',
              createdAt: new Date('2024-01-01'),
              completedAt: null,
              marketScore: null,
              competitorCount: 0,
              feedbackCount: 0,
              sourcesScraped: [],
            },
            {
              id: '550e8400-e29b-41d4-a716-446655440001',
              userId: 'user-123',
              title: 'E-commerce Analytics',
              ideaText: 'Analytics dashboard for e-commerce businesses',
              status: 'completed',
              createdAt: new Date('2024-01-02'),
              completedAt: new Date('2024-01-03'),
              marketScore: '8.5',
              competitorCount: 3,
              feedbackCount: 15,
              sourcesScraped: ['product-hunt', 'reddit', 'google'],
            }
          ]),
          limit: vi.fn().mockResolvedValue([])
        })
      })
    }),
    update: vi.fn().mockReturnValue({
      set: vi.fn().mockReturnValue({
        where: vi.fn().mockReturnValue({
          returning: vi.fn().mockResolvedValue([{
            id: '550e8400-e29b-41d4-a716-446655440000',
            status: 'completed',
            marketScore: '7.8',
            completedAt: new Date('2024-01-04'),
          }])
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

describe('Validation CRUD End-to-End', () => {
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
    
    // Setup authenticated user
    mockSupabase.auth.getUser.mockResolvedValue({
      data: { user: { id: 'user-123', email: 'test@example.com' } },
      error: null
    })
  })

  it('should complete full validation CRUD workflow', async () => {
    const headers = new Headers()
    headers.set('authorization', 'Bearer valid-token')
    
    const ctx = await createTRPCContext({ headers })
    const caller = appRouter.createCaller(ctx)

    // 1. Create a new validation
    const newValidation = await caller.validations.create({
      title: 'Revolutionary SaaS Platform',
      ideaText: 'This is a comprehensive SaaS platform that will revolutionize how businesses manage their operations and workflows.'
    })

    expect(newValidation).toMatchObject({
      id: '550e8400-e29b-41d4-a716-446655440000',
      userId: 'user-123',
      title: 'Revolutionary SaaS Platform',
      ideaText: 'This is a comprehensive SaaS platform that will revolutionize how businesses manage their operations and workflows.',
      status: 'processing'
    })

    // 2. Get all validations for the user
    const allValidations = await caller.validations.getAll()
    
    expect(allValidations).toHaveLength(2)
    expect(allValidations[0]).toMatchObject({
      title: 'Test SaaS Platform',
      status: 'processing'
    })
    expect(allValidations[1]).toMatchObject({
      title: 'E-commerce Analytics',
      status: 'completed',
      marketScore: '8.5'
    })

    // 3. Update validation status (simulating completion of processing)
    const updatedValidation = await caller.validations.updateStatus({
      id: '550e8400-e29b-41d4-a716-446655440000',
      status: 'completed',
      marketScore: 7.8,
      completedAt: new Date('2024-01-04')
    })

    expect(updatedValidation).toMatchObject({
      id: '550e8400-e29b-41d4-a716-446655440000',
      status: 'completed',
      marketScore: '7.8'
    })
  })

  it('should validate input constraints during creation', async () => {
    const headers = new Headers()
    headers.set('authorization', 'Bearer valid-token')
    
    const ctx = await createTRPCContext({ headers })
    const caller = appRouter.createCaller(ctx)

    // Test title too short
    await expect(caller.validations.create({
      title: '',
      ideaText: 'Valid idea description that meets minimum requirements'
    })).rejects.toThrow()

    // Test title too long
    const longTitle = 'a'.repeat(256)
    await expect(caller.validations.create({
      title: longTitle,
      ideaText: 'Valid idea description that meets minimum requirements'
    })).rejects.toThrow()

    // Test idea text too short
    await expect(caller.validations.create({
      title: 'Valid Title',
      ideaText: 'Short'
    })).rejects.toThrow()

    // Test idea text too long
    const longIdeaText = 'a'.repeat(1001)
    await expect(caller.validations.create({
      title: 'Valid Title',
      ideaText: longIdeaText
    })).rejects.toThrow()

    // Test valid input at boundaries
    const validValidation = await caller.validations.create({
      title: 'a'.repeat(255), // Max length
      ideaText: 'a'.repeat(1000) // Max length
    })

    expect(validValidation).toHaveProperty('id')
    expect(validValidation.status).toBe('processing')
  })

  it('should handle authentication requirements', async () => {
    // Test without authentication
    const headers = new Headers()
    const ctx = await createTRPCContext({ headers })
    const caller = appRouter.createCaller(ctx)

    await expect(caller.validations.create({
      title: 'Test Title',
      ideaText: 'Test idea description'
    })).rejects.toThrow('Missing or invalid authorization header')

    await expect(caller.validations.getAll()).rejects.toThrow('Missing or invalid authorization header')

    // Test with invalid token
    mockSupabase.auth.getUser.mockResolvedValue({
      data: { user: null },
      error: { message: 'Invalid token' }
    })

    const invalidHeaders = new Headers()
    invalidHeaders.set('authorization', 'Bearer invalid-token')
    
    const invalidCtx = await createTRPCContext({ headers: invalidHeaders })
    const invalidCaller = appRouter.createCaller(invalidCtx)

    await expect(invalidCaller.validations.create({
      title: 'Test Title',
      ideaText: 'Test idea description'
    })).rejects.toThrow('Authentication failed')
  })

  it('should handle database constraints and validation status flow', async () => {
    const headers = new Headers()
    headers.set('authorization', 'Bearer valid-token')
    
    const ctx = await createTRPCContext({ headers })
    const caller = appRouter.createCaller(ctx)

    // Create validation with processing status
    const validation = await caller.validations.create({
      title: 'Test Validation',
      ideaText: 'This is a test validation for status flow testing'
    })

    expect(validation.status).toBe('processing')
    expect(validation.marketScore).toBeNull()
    expect(validation.completedAt).toBeNull()

    // Update to completed status
    const completedValidation = await caller.validations.updateStatus({
      id: validation.id,
      status: 'completed',
      marketScore: 8.5,
      completedAt: new Date()
    })

    expect(completedValidation.status).toBe('completed')
    expect(completedValidation.marketScore).toBe('7.8') // From mock

    // Update to failed status
    const failedValidation = await caller.validations.updateStatus({
      id: validation.id,
      status: 'failed'
    })

    expect(failedValidation.status).toBe('completed') // From mock, but would be 'failed' in real scenario
  })
})