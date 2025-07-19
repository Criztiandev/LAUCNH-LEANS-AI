import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '@/components/providers/AuthProvider'
import { LoginForm } from '@/components/auth/LoginForm'
import { SignupForm } from '@/components/auth/SignupForm'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

// Mock Next.js router
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: '',
  },
  writable: true,
})

// Mock Supabase
vi.mock('@/lib/supabase', () => {
  const mockSupabase = {
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
  
  return {
    supabase: mockSupabase
  }
})

// Get the mocked supabase for test assertions
const { supabase: mockSupabase } = await import('@/lib/supabase')

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
    mockSupabase.auth.getSession.mockResolvedValue({ data: { session: null } })
    mockSupabase.auth.signInWithPassword.mockResolvedValue({ error: null })
    mockSupabase.auth.signUp.mockResolvedValue({ error: null })
    window.location.href = ''
  })

  describe('AuthProvider', () => {
    it('should provide auth context with initial state', async () => {
      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      expect(screen.getByTestId('user')).toHaveTextContent('not authenticated')
      
      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('loaded')
      })
    })

    it('should handle sign in', async () => {
      mockSupabase.auth.signInWithPassword.mockResolvedValue({ error: null })

      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      const signInButton = screen.getByText('Sign In')
      fireEvent.click(signInButton)

      await waitFor(() => {
        expect(mockSupabase.auth.signInWithPassword).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password',
        })
      })
    })

    it('should handle sign up', async () => {
      mockSupabase.auth.signUp.mockResolvedValue({ error: null })

      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      const signUpButton = screen.getByText('Sign Up')
      fireEvent.click(signUpButton)

      await waitFor(() => {
        expect(mockSupabase.auth.signUp).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password',
          options: {
            data: {
              first_name: 'Test',
            },
          },
        })
      })
    })

    it('should handle sign out', async () => {
      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      const signOutButton = screen.getByText('Sign Out')
      fireEvent.click(signOutButton)

      await waitFor(() => {
        expect(mockSupabase.auth.signOut).toHaveBeenCalled()
      })
    })
  })

  describe('LoginForm', () => {
    it('should render login form with all fields', () => {
      render(
        <AuthProvider>
          <LoginForm />
        </AuthProvider>
      )

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('should validate email field with Zod', async () => {
      render(
        <AuthProvider>
          <LoginForm />
        </AuthProvider>
      )

      const emailInput = screen.getByLabelText(/email/i)

      // Test empty email
      fireEvent.blur(emailInput)
      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      })

      // Test invalid email
      fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
      fireEvent.blur(emailInput)
      await waitFor(() => {
        expect(screen.getByText(/invalid email address/i)).toBeInTheDocument()
      })
    })

    it('should validate password field with Zod', async () => {
      render(
        <AuthProvider>
          <LoginForm />
        </AuthProvider>
      )

      const passwordInput = screen.getByLabelText(/password/i)

      // Test short password
      fireEvent.change(passwordInput, { target: { value: '123' } })
      fireEvent.blur(passwordInput)
      await waitFor(() => {
        expect(screen.getByText(/password must be at least 6 characters/i)).toBeInTheDocument()
      })
    })

    it('should handle successful login', async () => {
      mockSupabase.auth.signInWithPassword.mockResolvedValue({ error: null })

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
        expect(mockSupabase.auth.signInWithPassword).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        })
      })

      expect(window.location.href).toBe('/dashboard')
    })

    it('should handle login error', async () => {
      const errorMessage = 'Invalid credentials'
      mockSupabase.auth.signInWithPassword.mockResolvedValue({ 
        error: new Error(errorMessage) 
      })

      render(
        <AuthProvider>
          <LoginForm />
        </AuthProvider>
      )

      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument()
      })
    })
  })

  describe('SignupForm', () => {
    it('should render signup form with all fields', () => {
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
    })

    it('should validate all fields with Zod', async () => {
      render(
        <AuthProvider>
          <SignupForm />
        </AuthProvider>
      )

      const firstNameInput = screen.getByLabelText(/first name/i)
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/^password$/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      // Test required fields
      fireEvent.blur(firstNameInput)
      fireEvent.blur(emailInput)
      fireEvent.blur(passwordInput)
      fireEvent.blur(confirmPasswordInput)

      await waitFor(() => {
        expect(screen.getByText(/first name is required/i)).toBeInTheDocument()
        expect(screen.getByText(/email is required/i)).toBeInTheDocument()
        expect(screen.getByText(/password must be at least 6 characters/i)).toBeInTheDocument()
        expect(screen.getByText(/please confirm your password/i)).toBeInTheDocument()
      })
    })

    it('should validate password confirmation with Zod', async () => {
      render(
        <AuthProvider>
          <SignupForm />
        </AuthProvider>
      )

      const passwordInput = screen.getByLabelText(/^password$/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'different123' } })
      fireEvent.blur(confirmPasswordInput)

      await waitFor(() => {
        expect(screen.getByText(/passwords don't match/i)).toBeInTheDocument()
      })
    })

    it('should handle successful signup', async () => {
      mockSupabase.auth.signUp.mockResolvedValue({ error: null })

      render(
        <AuthProvider>
          <SignupForm />
        </AuthProvider>
      )

      const firstNameInput = screen.getByLabelText(/first name/i)
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/^password$/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
      const submitButton = screen.getByRole('button', { name: /sign up/i })

      fireEvent.change(firstNameInput, { target: { value: 'John' } })
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockSupabase.auth.signUp).toHaveBeenCalledWith({
          email: 'john@example.com',
          password: 'password123',
          options: {
            data: {
              first_name: 'John',
            },
          },
        })
      })

      await waitFor(() => {
        expect(screen.getByText(/check your email for a confirmation link/i)).toBeInTheDocument()
      })
    })

    it('should handle signup error', async () => {
      const errorMessage = 'Email already registered'
      mockSupabase.auth.signUp.mockResolvedValue({ 
        error: new Error(errorMessage) 
      })

      render(
        <AuthProvider>
          <SignupForm />
        </AuthProvider>
      )

      const firstNameInput = screen.getByLabelText(/first name/i)
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/^password$/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
      const submitButton = screen.getByRole('button', { name: /sign up/i })

      fireEvent.change(firstNameInput, { target: { value: 'John' } })
      fireEvent.change(emailInput, { target: { value: 'existing@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument()
      })
    })
  })

  describe('ProtectedRoute', () => {
    it('should render children when user is authenticated', async () => {
      const mockUser = { id: '123', email: 'test@example.com' }
      const mockSession = { user: mockUser, access_token: 'token' }
      
      mockSupabase.auth.getSession.mockResolvedValue({ 
        data: { session: mockSession } 
      })

      // Mock the auth state change to immediately call with authenticated session
      mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
        setTimeout(() => callback('SIGNED_IN', mockSession), 0)
        return { data: { subscription: { unsubscribe: vi.fn() } } }
      })

      render(
        <AuthProvider>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      })
    })

    it('should show loading spinner when loading', () => {
      render(
        <AuthProvider>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </AuthProvider>
      )

      // Should show loading initially - check for the spinner element
      const spinner = document.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })

    it('should redirect to login when user is not authenticated', async () => {
      mockSupabase.auth.getSession.mockResolvedValue({ data: { session: null } })

      render(
        <AuthProvider>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </AuthProvider>
      )

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })
    })
  })
})