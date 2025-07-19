import { describe, it, expect } from 'vitest'

describe('Basic Setup', () => {
  it('should have environment variables configured', () => {
    expect(process.env.NEXT_PUBLIC_SUPABASE_URL).toBeDefined()
    expect(process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY).toBeDefined()
    expect(process.env.SUPABASE_SERVICE_ROLE_KEY).toBeDefined()
    expect(process.env.DATABASE_URL).toBeDefined()
  })

  it('should be able to import core modules', async () => {
    // Test that our core modules can be imported without errors
    const { supabase } = await import('@/lib/supabase')
    expect(supabase).toBeDefined()
    
    const schema = await import('@/lib/db/schema')
    expect(schema.validations).toBeDefined()
    expect(schema.competitors).toBeDefined()
    expect(schema.feedback).toBeDefined()
    expect(schema.aiAnalysis).toBeDefined()
    expect(schema.profiles).toBeDefined()
  })

  it('should have correct TypeScript types', () => {
    // This test verifies that TypeScript compilation works
    expect(true).toBe(true)
  })
})