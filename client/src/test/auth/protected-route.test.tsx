import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider } from '@/components/providers/AuthProvider'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

// Mock Next.js router
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

// Mock Supabase
vi.mock('@/lib/supabase', () => {
  const mockSupabase = {
    auth: {
      getSession: vi.fn(),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } }
      }),
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
    }
  }
  
  return {
    supabase: mockSupabase
  }
})

// Get the mocked supabase for test assertions
const { supabase: mockSupabase } = await import('@/lib/supabase')

const TestProtectedContent = () => <div>Protected Content</div>

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should show loading spinner initially', () => {
    mockSupabase.auth.getSession.mockResolvedValue({ data: { session: null } })

    render(
      <AuthProvider>
        <ProtectedRoute>
          <TestProtectedContent />
        </ProtectedRoute>
      </AuthProvider>
    )

    // Check for loading spinner
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })

  it('should render protected content when user is authenticated', async () => {
    const mockUser = { 
      id: '123', 
      email: 'test@example.com',
      user_metadata: { first_name: 'Test' }
    }
    const mockSession = { user: mockUser, access_token: 'token' }
    
    mockSupabase.auth.getSession.mockResolvedValue({ 
      data: { session: mockSession } 
    })

    // Simulate auth state change with authenticated user
    const authStateCallback = vi.fn()
    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      authStateCallback.mockImplementation(callback)
      // Immediately call with authenticated session
      setTimeout(() => callback('SIGNED_IN', mockSession), 0)
      return { data: { subscription: { unsubscribe: vi.fn() } } }
    })

    render(
      <AuthProvider>
        <ProtectedRoute>
          <TestProtectedContent />
        </ProtectedRoute>
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })

    expect(mockPush).not.toHaveBeenCalled()
  })

  it('should redirect to login when user is not authenticated', async () => {
    mockSupabase.auth.getSession.mockResolvedValue({ data: { session: null } })

    // Simulate auth state change with no user
    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      setTimeout(() => callback('SIGNED_OUT', null), 0)
      return { data: { subscription: { unsubscribe: vi.fn() } } }
    })

    render(
      <AuthProvider>
        <ProtectedRoute>
          <TestProtectedContent />
        </ProtectedRoute>
      </AuthProvider>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should not redirect if still loading', () => {
    mockSupabase.auth.getSession.mockImplementation(() => 
      new Promise(() => {}) // Never resolves to simulate loading
    )

    render(
      <AuthProvider>
        <ProtectedRoute>
          <TestProtectedContent />
        </ProtectedRoute>
      </AuthProvider>
    )

    expect(mockPush).not.toHaveBeenCalled()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should handle auth state changes correctly', async () => {
    const mockUser = { 
      id: '123', 
      email: 'test@example.com' 
    }
    
    mockSupabase.auth.getSession.mockResolvedValue({ data: { session: null } })

    let authCallback: ((event: string, session: unknown) => void) | null = null
    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      authCallback = callback
      return { data: { subscription: { unsubscribe: vi.fn() } } }
    })

    render(
      <AuthProvider>
        <ProtectedRoute>
          <TestProtectedContent />
        </ProtectedRoute>
      </AuthProvider>
    )

    // Initially should redirect to login
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    // Simulate user signing in
    if (authCallback) {
      authCallback('SIGNED_IN', { user: mockUser })
    }

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })
  })
})