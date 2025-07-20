import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ValidationCard } from '@/components/validation/ValidationCard'
import type { Validation } from '@/lib/db/schema'

// Mock the lucide-react icons
vi.mock('lucide-react', () => ({
  Calendar: () => <div data-testid="calendar-icon" />,
  TrendingUp: () => <div data-testid="trending-up-icon" />,
  Users: () => <div data-testid="users-icon" />,
  MessageSquare: () => <div data-testid="message-square-icon" />,
}))

const mockValidation: Validation = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  userId: 'user-123',
  title: 'Test SaaS Idea',
  ideaText: 'This is a test idea for a SaaS product that solves a specific problem.',
  marketScore: '8.5',
  status: 'completed',
  createdAt: '2024-01-15T10:30:00Z',
  completedAt: '2024-01-15T11:00:00Z',
  competitorCount: 5,
  feedbackCount: 12,
  sourcesScraped: ['product-hunt', 'reddit'],
}

const mockProcessingValidation: Validation = {
  ...mockValidation,
  id: '123e4567-e89b-12d3-a456-426614174001',
  status: 'processing',
  marketScore: null,
  completedAt: null,
  competitorCount: 0,
  feedbackCount: 0,
}

const mockFailedValidation: Validation = {
  ...mockValidation,
  id: '123e4567-e89b-12d3-a456-426614174002',
  status: 'failed',
  marketScore: null,
  completedAt: null,
}

describe('ValidationCard', () => {
  it('renders completed validation correctly', () => {
    render(<ValidationCard validation={mockValidation} />)
    
    expect(screen.getByText('Test SaaS Idea')).toBeInTheDocument()
    expect(screen.getByText(/This is a test idea/)).toBeInTheDocument()
    expect(screen.getByText('completed')).toBeInTheDocument()
    expect(screen.getByText('Score: 8.5/10')).toBeInTheDocument()
    expect(screen.getByText('Jan 15, 2024')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument() // competitor count
    expect(screen.getByText('12')).toBeInTheDocument() // feedback count
    expect(screen.getByText('View Results')).toBeInTheDocument()
  })

  it('renders processing validation correctly', () => {
    render(<ValidationCard validation={mockProcessingValidation} />)
    
    expect(screen.getByText('Test SaaS Idea')).toBeInTheDocument()
    expect(screen.getByText('processing')).toBeInTheDocument()
    expect(screen.queryByText('Score:')).not.toBeInTheDocument()
    expect(screen.queryByText('View Results')).not.toBeInTheDocument()
    
    // Should show progress bar
    const progressBar = document.querySelector('.animate-pulse')
    expect(progressBar).toBeInTheDocument()
    expect(progressBar).toHaveClass('animate-pulse')
  })

  it('renders failed validation correctly', () => {
    render(<ValidationCard validation={mockFailedValidation} />)
    
    expect(screen.getByText('Test SaaS Idea')).toBeInTheDocument()
    expect(screen.getByText('failed')).toBeInTheDocument()
    expect(screen.queryByText('Score:')).not.toBeInTheDocument()
    expect(screen.queryByText('View Results')).not.toBeInTheDocument()
  })

  it('calls onClick when card is clicked', () => {
    const mockOnClick = vi.fn()
    render(<ValidationCard validation={mockValidation} onClick={mockOnClick} />)
    
    const card = document.querySelector('[data-slot="card"]')
    expect(card).toBeInTheDocument()
    fireEvent.click(card!)
    
    expect(mockOnClick).toHaveBeenCalledTimes(1)
  })

  it('displays correct market score colors', () => {
    const highScoreValidation = { ...mockValidation, marketScore: '9.0' }
    const mediumScoreValidation = { ...mockValidation, marketScore: '6.5' }
    const lowScoreValidation = { ...mockValidation, marketScore: '3.0' }

    const { rerender } = render(<ValidationCard validation={highScoreValidation} />)
    expect(screen.getByText('Score: 9.0/10')).toHaveClass('text-green-600')

    rerender(<ValidationCard validation={mediumScoreValidation} />)
    expect(screen.getByText('Score: 6.5/10')).toHaveClass('text-yellow-600')

    rerender(<ValidationCard validation={lowScoreValidation} />)
    expect(screen.getByText('Score: 3.0/10')).toHaveClass('text-red-600')
  })

  it('truncates long titles and descriptions', () => {
    const longTitleValidation = {
      ...mockValidation,
      title: 'This is a very long title that should be truncated when displayed in the card component',
      ideaText: 'This is a very long idea description that should also be truncated when displayed in the card component to maintain proper layout and readability.',
    }

    render(<ValidationCard validation={longTitleValidation} />)
    
    const titleElement = screen.getByText(/This is a very long title/)
    const descriptionElement = screen.getByText(/This is a very long idea/)
    
    expect(titleElement).toHaveClass('line-clamp-1')
    expect(descriptionElement).toHaveClass('line-clamp-2')
  })

  it('handles validation without market score', () => {
    const noScoreValidation = { ...mockValidation, marketScore: null }
    render(<ValidationCard validation={noScoreValidation} />)
    
    expect(screen.queryByText('Score:')).not.toBeInTheDocument()
  })

  it('formats date correctly', () => {
    render(<ValidationCard validation={mockValidation} />)
    
    expect(screen.getByText('Jan 15, 2024')).toBeInTheDocument()
  })

  it('shows competitor and feedback counts only for completed validations', () => {
    render(<ValidationCard validation={mockValidation} />)
    
    expect(screen.getByTestId('users-icon')).toBeInTheDocument()
    expect(screen.getByTestId('message-square-icon')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
  })

  it('does not show competitor and feedback counts for processing validations', () => {
    render(<ValidationCard validation={mockProcessingValidation} />)
    
    expect(screen.queryByTestId('users-icon')).not.toBeInTheDocument()
    expect(screen.queryByTestId('message-square-icon')).not.toBeInTheDocument()
  })
})