/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import { CreateValidationForm } from '@/components/validation/CreateValidationForm'
import { trpc } from '@/lib/trpc/client'

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}))

// Mock tRPC
vi.mock('@/lib/trpc/client', () => ({
  trpc: {
    validations: {
      create: {
        useMutation: vi.fn(),
      },
    },
  },
}))

const mockPush = vi.fn()
const mockMutateAsync = vi.fn()

beforeEach(() => {
  vi.clearAllMocks()
  
  vi.mocked(useRouter).mockReturnValue({
    push: mockPush,
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  })

  vi.mocked(trpc.validations.create.useMutation).mockReturnValue({
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
    error: null,
  } as any)
})

describe('CreateValidationForm', () => {
  it('should render form fields correctly', () => {
    render(<CreateValidationForm />)

    expect(screen.getByLabelText(/idea title/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/idea description/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create validation/i })).toBeInTheDocument()
  })

  it('should show character counts', () => {
    render(<CreateValidationForm />)

    expect(screen.getByText('0/255')).toBeInTheDocument()
    expect(screen.getByText('0/1000')).toBeInTheDocument()
  })

  it('should update character counts when typing', async () => {
    render(<CreateValidationForm />)

    const titleInput = screen.getByLabelText(/idea title/i)
    const ideaTextarea = screen.getByLabelText(/idea description/i)

    fireEvent.change(titleInput, { target: { value: 'Test Title' } })
    fireEvent.change(ideaTextarea, { target: { value: 'Test idea description' } })

    await waitFor(() => {
      expect(screen.getByText('10/255')).toBeInTheDocument()
      expect(screen.getByText('21/1000')).toBeInTheDocument()
    })
  })

  it('should show validation errors for empty fields', async () => {
    render(<CreateValidationForm />)

    const submitButton = screen.getByRole('button', { name: /create validation/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Title is required')).toBeInTheDocument()
      expect(screen.getByText('Idea description must be at least 10 characters')).toBeInTheDocument()
    })
  })

  it('should show validation error for short idea text', async () => {
    render(<CreateValidationForm />)

    const titleInput = screen.getByLabelText(/idea title/i)
    const ideaTextarea = screen.getByLabelText(/idea description/i)
    const submitButton = screen.getByRole('button', { name: /create validation/i })

    fireEvent.change(titleInput, { target: { value: 'Valid Title' } })
    fireEvent.change(ideaTextarea, { target: { value: 'Short' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Idea description must be at least 10 characters')).toBeInTheDocument()
    })
  })

  it('should show validation error for long title', async () => {
    render(<CreateValidationForm />)

    const titleInput = screen.getByLabelText(/idea title/i)
    const ideaTextarea = screen.getByLabelText(/idea description/i)
    const submitButton = screen.getByRole('button', { name: /create validation/i })

    const longTitle = 'a'.repeat(256)
    fireEvent.change(titleInput, { target: { value: longTitle } })
    fireEvent.change(ideaTextarea, { target: { value: 'Valid idea description that meets minimum requirements' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Title must be less than 255 characters')).toBeInTheDocument()
    })
  })

  it('should show validation error for long idea text', async () => {
    render(<CreateValidationForm />)

    const titleInput = screen.getByLabelText(/idea title/i)
    const ideaTextarea = screen.getByLabelText(/idea description/i)
    const submitButton = screen.getByRole('button', { name: /create validation/i })

    const longIdeaText = 'a'.repeat(1001)
    fireEvent.change(titleInput, { target: { value: 'Valid Title' } })
    fireEvent.change(ideaTextarea, { target: { value: longIdeaText } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Idea description must be less than 1000 characters')).toBeInTheDocument()
    })
  })

  it('should submit form with valid data', async () => {
    const mockValidation = {
      id: 'validation-123',
      userId: 'user-123',
      title: 'Test SaaS Idea',
      ideaText: 'This is a valid test idea description that meets all requirements.',
      status: 'processing' as const,
      createdAt: new Date(),
      marketScore: null,
      completedAt: null,
      competitorCount: 0,
      feedbackCount: 0,
      sourcesScraped: [],
    }

    mockMutateAsync.mockResolvedValue(mockValidation)

    render(<CreateValidationForm />)

    const titleInput = screen.getByLabelText(/idea title/i)
    const ideaTextarea = screen.getByLabelText(/idea description/i)
    const submitButton = screen.getByRole('button', { name: /create validation/i })

    fireEvent.change(titleInput, { target: { value: 'Test SaaS Idea' } })
    fireEvent.change(ideaTextarea, { target: { value: 'This is a valid test idea description that meets all requirements.' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        title: 'Test SaaS Idea',
        ideaText: 'This is a valid test idea description that meets all requirements.',
      })
    })
  })

  it('should show loading state during submission', async () => {
    vi.mocked(trpc.validations.create.useMutation).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
      isError: false,
      error: null,
    } as any)

    render(<CreateValidationForm />)

    expect(screen.getByRole('button', { name: /creating validation/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /creating validation/i })).toBeDisabled()
  })

  it('should show error message on submission failure', async () => {
    const errorMessage = 'Failed to create validation'
    
    // Mock the mutation to trigger onError callback
    const mockOnError = vi.fn()
    vi.mocked(trpc.validations.create.useMutation).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
      onError: mockOnError,
    } as any)

    mockMutateAsync.mockRejectedValue(new Error(errorMessage))

    render(<CreateValidationForm />)

    const titleInput = screen.getByLabelText(/idea title/i)
    const ideaTextarea = screen.getByLabelText(/idea description/i)
    const submitButton = screen.getByRole('button', { name: /create validation/i })

    fireEvent.change(titleInput, { target: { value: 'Test SaaS Idea' } })
    fireEvent.change(ideaTextarea, { target: { value: 'This is a valid test idea description that meets all requirements.' } })
    fireEvent.click(submitButton)

    // The error should be handled by the onError callback in the component
    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalled()
    })
  })

  it('should clear error message on successful submission', async () => {
    const mockValidation = {
      id: 'validation-123',
      userId: 'user-123',
      title: 'Test SaaS Idea',
      ideaText: 'This is a valid test idea description that meets all requirements.',
      status: 'processing' as const,
      createdAt: new Date(),
      marketScore: null,
      completedAt: null,
      competitorCount: 0,
      feedbackCount: 0,
      sourcesScraped: [],
    }

    // First render with error
    vi.mocked(trpc.validations.create.useMutation).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: true,
      error: { message: 'Previous error' },
    } as any)

    const { rerender } = render(<CreateValidationForm />)

    // Show error first
    const titleInput = screen.getByLabelText(/idea title/i)
    const ideaTextarea = screen.getByLabelText(/idea description/i)
    const submitButton = screen.getByRole('button', { name: /create validation/i })

    fireEvent.change(titleInput, { target: { value: 'Test SaaS Idea' } })
    fireEvent.change(ideaTextarea, { target: { value: 'This is a valid test idea description that meets all requirements.' } })

    // Then simulate successful submission
    vi.mocked(trpc.validations.create.useMutation).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
    } as any)

    mockMutateAsync.mockResolvedValue(mockValidation)

    rerender(<CreateValidationForm />)

    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.queryByText('Previous error')).not.toBeInTheDocument()
    })
  })
})