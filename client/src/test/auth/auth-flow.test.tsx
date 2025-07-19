import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '@/components/providers/AuthProvider'
import { LoginForm } from '@/components/auth/LoginForm'
import { SignupForm } from '@/components/auth/SignupForm'

// Mock Supabase
vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } }
      }),
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
    }
  }
}))

// Test component to access auth context
function TestAuthComponent() {
  const { user, loading, signIn, signUp, signOut } = useAuth()
  
  return (
    <div>
      <div data-testid="user">{user ? 'authenticated' : 'not authenticated'}</div>
      <div data-testid="loading">{loading ? 'loading' : 'loaded'}</div>
      <button onClick={() => signIn('test@example.com', 'password')}>
        Sign In
      </button>
      <button onClick={() => signUp('test@example.com', 'password', 'Test')}>
        Sign Up
      </button>
      <button onClick={signOut}>Sign Out</button>
    </div>
  )
}

describe('Authentication Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should provide auth context', () => {
    render(
      <AuthProvider>
        <TestAuthComponent />
      </AuthProvider>
    )

    expect(screen.getByTestId('user')).toHaveTextContent('not authenticated')
    expect(screen.getByTestId('loading')).toHaveTextContent('loaded')
  })

  it('should render login form with validation', async () => {
    render(
      <AuthProvider>
        <LoginForm />
      </AuthProvider>
    )

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()

    // Test form validation
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/invalid email address/i)).toBeInTheDocument()
    })
  })

  it('should render signup form with validation', async () => {
    render(
      <AuthProvider>
        <SignupForm />
      </AuthProvider>
    )

    expect(screen.getByLabelText(/first name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign up/i })).toBeInTheDocument()

    // Test password confirmation validation
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const submitButton = screen.getByRole('button', { name: /sign up/i })

    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.change(confirmPasswordInput, { target: { value: 'different' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/passwords don't match/i)).toBeInTheDocument()
    })
  })

  it('should handle form submission', async () => {
    const mockSignIn = vi.fn().mockResolvedValue({ error: null })
    
    vi.doMock('@/lib/supabase', () => ({
      supabase: {
        auth: {
          getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
          onAuthStateChange: vi.fn().mockReturnValue({
            data: { subscription: { unsubscribe: vi.fn() } }
          }),
          signInWithPassword: mockSignIn,
        }
      }
    }))

    render(
      <AuthProvider>
        <LoginForm />
      </AuthProvider>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/signing in/i)).toBeInTheDocument()
    })
  })
})