import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ValidationList } from '@/components/validation/ValidationList'
import type { Validation } from '@/lib/db/schema'

// Mock Next.js router
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

// Mock the lucide-react icons
vi.mock('lucide-react', () => ({
  Plus: () => <div data-testid="plus-icon" />,
  Loader2: () => <div data-testid="loader-icon" />,
  Calendar: () => <div data-testid="calendar-icon" />,
  TrendingUp: () => <div data-testid="trending-up-icon" />,
  Users: () => <div data-testid="users-icon" />,
  MessageSquare: () => <div data-testid="message-square-icon" />,
}))

const mockValidations: Validation[] = [
  {
    id: '123e4567-e89b-12d3-a456-426614174000',
    userId: 'user-123',
    title: 'First SaaS Idea',
    ideaText: 'This is the first test idea.',
    marketScore: '8.5',
    status: 'completed',
    createdAt: '2024-01-15T10:30:00Z',
    completedAt: '2024-01-15T11:00:00Z',
    competitorCount: 5,
    feedbackCount: 12,
    sourcesScraped: ['product-hunt', 'reddit'],
  },
  {
    id: '123e4567-e89b-12d3-a456-426614174001',
    userId: 'user-123',
    title: 'Second SaaS Idea',
    ideaText: 'This is the second test idea.',
    marketScore: null,
    status: 'processing',
    createdAt: '2024-01-14T09:15:00Z',
    completedAt: null,
    competitorCount: 0,
    feedbackCount: 0,
    sourcesScraped: [],
  },
  {
    id: '123e4567-e89b-12d3-a456-426614174002',
    userId: 'user-123',
    title: 'Third SaaS Idea',
    ideaText: 'This is the third test idea.',
    marketScore: null,
    status: 'failed',
    createdAt: '2024-01-13T14:45:00Z',
    completedAt: null,
    competitorCount: 0,
    feedbackCount: 0,
    sourcesScraped: [],
  },
]

describe('ValidationList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state correctly', () => {
    render(<ValidationList validations={undefined} isLoading={true} />)
    
    expect(screen.getByTestId('loader-icon')).toBeInTheDocument()
    expect(screen.getByText('Loading validations...')).toBeInTheDocument()
  })

  it('renders empty state correctly', () => {
    render(<ValidationList validations={[]} isLoading={false} />)
    
    expect(screen.getByText('No validations yet')).toBeInTheDocument()
    expect(screen.getByText(/Get started by creating your first/)).toBeInTheDocument()
    expect(screen.getByText('Create Your First Validation')).toBeInTheDocument()
  })

  it('renders validations list correctly', () => {
    render(<ValidationList validations={mockValidations} isLoading={false} />)
    
    expect(screen.getByText('Your Validations')).toBeInTheDocument()
    expect(screen.getByText('Manage and track your SaaS idea validations')).toBeInTheDocument()
    expect(screen.getByText('New Validation')).toBeInTheDocument()
    
    // Check that all validations are rendered
    expect(screen.getByText('First SaaS Idea')).toBeInTheDocument()
    expect(screen.getByText('Second SaaS Idea')).toBeInTheDocument()
    expect(screen.getByText('Third SaaS Idea')).toBeInTheDocument()
  })

  it('renders error state correctly', () => {
    const error = new Error('Failed to fetch')
    render(<ValidationList validations={undefined} isLoading={false} error={error} />)
    
    expect(screen.getByText('Failed to load validations')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('navigates to create validation when New Validation button is clicked', async () => {
    render(<ValidationList validations={mockValidations} isLoading={false} />)
    
    const newValidationButton = screen.getByText('New Validation')
    fireEvent.click(newValidationButton)
    
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/create-validation')
    })
  })

  it('navigates to create validation when Create Your First Validation button is clicked', async () => {
    render(<ValidationList validations={[]} isLoading={false} />)
    
    const createFirstButton = screen.getByText('Create Your First Validation')
    fireEvent.click(createFirstButton)
    
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/create-validation')
    })
  })

  it('navigates to validation results when completed validation is clicked', async () => {
    render(<ValidationList validations={mockValidations} isLoading={false} />)
    
    // Find the completed validation card and click it
    const completedValidationCard = screen.getByText('First SaaS Idea').closest('[data-slot="card"]')
    expect(completedValidationCard).toBeInTheDocument()
    
    if (completedValidationCard) {
      fireEvent.click(completedValidationCard)
      
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/validation/123e4567-e89b-12d3-a456-426614174000')
      })
    }
  })

  it('does not navigate when processing validation is clicked', async () => {
    render(<ValidationList validations={mockValidations} isLoading={false} />)
    
    // Find the processing validation card and click it
    const processingValidationCard = screen.getByText('Second SaaS Idea').closest('[data-slot="card"]')
    expect(processingValidationCard).toBeInTheDocument()
    
    if (processingValidationCard) {
      fireEvent.click(processingValidationCard)
      
      // Should not navigate for processing validations
      await waitFor(() => {
        expect(mockPush).not.toHaveBeenCalledWith('/validation/123e4567-e89b-12d3-a456-426614174001')
      })
    }
  })

  it('reloads page when Try Again button is clicked in error state', () => {
    // Mock window.location.reload
    const mockReload = vi.fn()
    Object.defineProperty(window, 'location', {
      value: {
        reload: mockReload,
      },
      writable: true,
    })
    
    const error = new Error('Failed to fetch')
    render(<ValidationList validations={undefined} isLoading={false} error={error} />)
    
    const tryAgainButton = screen.getByText('Try Again')
    fireEvent.click(tryAgainButton)
    
    expect(mockReload).toHaveBeenCalled()
  })

  it('displays correct header with New Validation button when validations exist', () => {
    render(<ValidationList validations={mockValidations} isLoading={false} />)
    
    expect(screen.getByText('Your Validations')).toBeInTheDocument()
    expect(screen.getByText('New Validation')).toBeInTheDocument()
    expect(screen.getByTestId('plus-icon')).toBeInTheDocument()
  })

  it('handles undefined validations gracefully', () => {
    render(<ValidationList validations={undefined} isLoading={false} />)
    
    expect(screen.getByText('No validations yet')).toBeInTheDocument()
  })

  it('renders validations in chronological order', () => {
    render(<ValidationList validations={mockValidations} isLoading={false} />)
    
    const validationTitles = screen.getAllByText(/SaaS Idea/)
    expect(validationTitles).toHaveLength(3)
    
    // The validations should be displayed in the order they appear in the array
    // (assuming they're already sorted by the backend)
    expect(validationTitles[0]).toHaveTextContent('First SaaS Idea')
    expect(validationTitles[1]).toHaveTextContent('Second SaaS Idea')
    expect(validationTitles[2]).toHaveTextContent('Third SaaS Idea')
  })
})