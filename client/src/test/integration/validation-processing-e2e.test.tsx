/**
 * End-to-end integration tests for validation creation and processing flow
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CreateValidationForm } from '@/components/validation/CreateValidationForm'
import { TRPCProvider } from '@/components/providers/TRPCProvider'
import { AuthProvider } from '@/components/providers/AuthProvider'

// Mock next/navigation
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

// Mock tRPC client
const mockCreateMutation = vi.fn()
vi.mock('@/lib/trpc/client', () => ({
  trpc: {
    validations: {
      create: {
        useMutation: () => ({
          mutateAsync: mockCreateMutation,
          isPending: false,
        }),
      },
    },
  },
}))

// Mock backend API
const mockProcessValidation = vi.fn()
const mockHealthCheck = vi.fn()
vi.mock('@/lib/api', () => ({
  backendApi: {
    processValidation: mockProcessValidation,
    healthCheck: mockHealthCheck,
  },
  BackendApiError: class extends Error {
    constructor(message: string, public status: number = 500, public detail?: string) {
      super(message)
      this.name = 'BackendApiError'
      this.detail = detail || message
    }
  },
}))

// Mock Supabase
vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: {
          session: {
            user: { id: 'test-user-id', email: 'test@example.com' },
            access_token: 'test-token',
          },
        },
        error: null,
      }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } },
      }),
    },
  },
}))

// Test wrapper component
function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <TRPCProvider>
        {children}
      </TRPCProvider>
    </AuthProvider>
  )
}

describe('Validation Processing E2E', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    mockPush.mockClear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should complete full validation creation and processing flow', async () => {
    // Mock successful validation creation
    const mockValidation = {
      id: 'test-validation-id',
      title: 'Test SaaS Idea',
      ideaText: 'A revolutionary SaaS platform for testing',
      status: 'processing',
    }
    mockCreateMutation.mockResolvedValueOnce(mockValidation)

    // Mock successful backend processing
    const mockProcessingResponse = {
      message: 'Validation processing started',
      validation_id: 'test-validation-id',
      status: 'processing',
    }
    mockProcessValidation.mockResolvedValueOnce(mockProcessingResponse)

    render(
      <TestWrapper>
        <CreateValidationForm />
      </TestWrapper>
    )

    // Fill out the form
    const titleInput = screen.getByLabelText(/idea title/i)
    const ideaTextarea = screen.getByLabelText(/idea description/i)
    const submitButton = screen.getByRole('button', { name: /create validation/i })

    await user.type(titleInput, 'Test SaaS Idea')
    await user.type(ideaTextarea, 'A revolutionary SaaS platform for testing and validation')

    // Submit the form
    await user.click(submitButton)

    // Wait for processing states
    await waitFor(() => {
      expect(screen.getByText(/creating validation/i)).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText(/starting processing/i)).toBeInTheDocument()
    })

    // Verify API calls
    await waitFor(() => {
      expect(mockCreateMutation).toHaveBeenCalledWith({
        title: 'Test SaaS Idea',
        ideaText: 'A revolutionary SaaS platform for testing and validation',
      })
    })

    await waitFor(() => {
      expect(mockProcessValidation).toHaveBeenCalledWith('test-validation-id')
    })

    // Verify redirect to dashboard
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('should handle backend processing failures gracefully', async () => {
    // Mock successful validation creation
    const mockValidation = {
      id: 'test-validation-id',
      title: 'Test SaaS Idea',
      ideaText: 'A revolutionary SaaS platform for testing',
      status: 'processing',
    }
    mockCreateMutation.mockResolvedValueOnce(mockValidation)

    // Mock backend processing failure
    const { BackendApiError } = await import('@/lib/api')
    const processingError = new BackendApiError('Connection failed', 0, 'Network connection failed')
    mockProcessValidation.mockRejectedValueOnce(processingError)

    render(
      <TestWrapper>
        <CreateValidationForm />
      </TestWrapper>
    )

    // Fill out and submit form
    const titleInput = screen.getByLabelText(/idea title/i)
    const ideaTextarea = screen.getByLabelText(/idea description/i)
    const submitButton = screen.getByRole('button', { name: /create validation/i })

    await user.type(titleInput, 'Test SaaS Idea')
    await user.type(ideaTextarea, 'A revolutionary SaaS platform for testing and validation')
    await user.click(submitButton)

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/unable to connect to processing service/i)).toBeInTheDocument()
    })

    // Should still redirect to dashboard after delay
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    }, { timeout: 4000 })
  })

  it('should handle validation creation failures', async () => {
    // Mock validation creation failure
    mockCreateMutation.mockRejectedValueOnce(new Error('Database connection failed'))

    render(
      <TestWrapper>
        <CreateValidationForm />
      </TestWrapper>
    )

    // Fill out and submit form
    const titleInput = screen.getByLabelText(/idea title/i)
    const ideaTextarea = screen.getByLabelText(/idea description/i)
    const submitButton = screen.getByRole('button', { name: /create validation/i })

    await user.type(titleInput, 'Test SaaS Idea')
    await user.type(ideaTextarea, 'A revolutionary SaaS platform for testing and validation')
    await user.click(submitButton)

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/failed to create validation/i)).toBeInTheDocument()
    })

    // Should not call backend processing
    expect(mockProcessValidation).not.toHaveBeenCalled()

    // Should not redirect
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('should show backend connection status', async () => {
    render(
      <TestWrapper>
        <CreateValidationForm />
      </TestWrapper>
    )

    // Initially no connection status shown
    expect(screen.queryByText(/backend processing service/i)).not.toBeInTheDocument()

    // Mock a failed backend call to trigger connection status
    const mockValidation = {
      id: 'test-validation-id',
      title: 'Test SaaS Idea',
      ideaText: 'A revolutionary SaaS platform for testing',
      status: 'processing',
    }
    mockCreateMutation.mockResolvedValueOnce(mockValidation)

    const { BackendApiError } = await import('@/lib/api')
    const connectionError = new BackendApiError('Connection failed', 0)
    mockProcessValidation.mockRejectedValueOnce(connectionError)

    // Fill out and submit form
    const titleInput = screen.getByLabelText(/idea title/i)
    const ideaTextarea = screen.getByLabelText(/idea description/i)
    const submitButton = screen.getByRole('button', { name: /create validation/i })

    await user.type(titleInput, 'Test SaaS Idea')
    await user.type(ideaTextarea, 'A revolutionary SaaS platform for testing and validation')
    await user.click(submitButton)

    // Wait for connection status to appear
    await waitFor(() => {
      expect(screen.getByText(/backend processing service is not available/i)).toBeInTheDocument()
    })
  })

  it('should validate form inputs', async () => {
    render(
      <TestWrapper>
        <CreateValidationForm />
      </TestWrapper>
    )

    const submitButton = screen.getByRole('button', { name: /create validation/i })

    // Try to submit empty form
    await user.click(submitButton)

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/string must contain at least 1 character/i)).toBeInTheDocument()
    })

    // Should not call any APIs
    expect(mockCreateMutation).not.toHaveBeenCalled()
    expect(mockProcessValidation).not.toHaveBeenCalled()
  })

  it('should show character counts', async () => {
    render(
      <TestWrapper>
        <CreateValidationForm />
      </TestWrapper>
    )

    const titleInput = screen.getByLabelText(/idea title/i)
    const ideaTextarea = screen.getByLabelText(/idea description/i)

    // Initially should show 0 counts
    expect(screen.getByText('0/255')).toBeInTheDocument()
    expect(screen.getByText('0/1000')).toBeInTheDocument()

    // Type some text
    await user.type(titleInput, 'Test Title')
    await user.type(ideaTextarea, 'Test description')

    // Should update counts
    expect(screen.getByText('10/255')).toBeInTheDocument()
    expect(screen.getByText('16/1000')).toBeInTheDocument()
  })
})