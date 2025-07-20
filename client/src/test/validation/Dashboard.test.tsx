import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Validation } from '@/lib/db/schema'

// Mock data
const mockValidations: Validation[] = [
  {
    id: '123e4567-e89b-12d3-a456-426614174000',
    userId: 'user-123',
    title: 'Test SaaS Idea',
    ideaText: 'This is a test idea for a SaaS product.',
    marketScore: '8.5',
    status: 'completed',
    createdAt: '2024-01-15T10:30:00Z',
    completedAt: '2024-01-15T11:00:00Z',
    competitorCount: 5,
    feedbackCount: 12,
    sourcesScraped: ['product-hunt', 'reddit'],
  },
]

// Mock functions
const mockSignOut = vi.fn()
const mockPush = vi.fn()
const mockValidationsQuery = vi.fn()

const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  user_metadata: {
    first_name: 'John',
  },
}

// Mock the auth provider
vi.mock('@/components/providers/AuthProvider', () => ({
  useAuth: () => ({
    user: mockUser,
    signOut: mockSignOut,
  }),
}))

// Mock the tRPC client
vi.mock('@/lib/trpc/client', () => ({
  trpc: {
    validations: {
      getAll: {
        useQuery: () => mockValidationsQuery(),
      },
    },
  },
}))

// Mock the ProtectedRoute component
vi.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

// Mock Next.js router
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

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard header correctly', async () => {
    mockValidationsQuery.mockReturnValue({
      data: mockValidations,
      isLoading: false,
      error: null,
    })

    const DashboardPage = (await import('@/app/dashboard/page')).default
    render(<DashboardPage />)
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Welcome back, John')).toBeInTheDocument()
    expect(screen.getByText('Sign Out')).toBeInTheDocument()
  })

  it('calls signOut when Sign Out button is clicked', async () => {
    mockValidationsQuery.mockReturnValue({
      data: mockValidations,
      isLoading: false,
      error: null,
    })

    const DashboardPage = (await import('@/app/dashboard/page')).default
    render(<DashboardPage />)
    
    const signOutButton = screen.getByText('Sign Out')
    fireEvent.click(signOutButton)
    
    await waitFor(() => {
      expect(mockSignOut).toHaveBeenCalledTimes(1)
    })
  })

  it('renders ValidationList component with correct props', async () => {
    mockValidationsQuery.mockReturnValue({
      data: mockValidations,
      isLoading: false,
      error: null,
    })

    const DashboardPage = (await import('@/app/dashboard/page')).default
    render(<DashboardPage />)
    
    // Check that ValidationList is rendered with validations
    expect(screen.getByText('Your Validations')).toBeInTheDocument()
    expect(screen.getByText('Test SaaS Idea')).toBeInTheDocument()
  })

  it('passes loading state to ValidationList', async () => {
    mockValidationsQuery.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    })

    const DashboardPage = (await import('@/app/dashboard/page')).default
    render(<DashboardPage />)
    
    expect(screen.getByTestId('loader-icon')).toBeInTheDocument()
    expect(screen.getByText('Loading validations...')).toBeInTheDocument()
  })

  it('passes error state to ValidationList', async () => {
    const mockError = new Error('Failed to fetch validations')
    
    mockValidationsQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: mockError,
    })

    const DashboardPage = (await import('@/app/dashboard/page')).default
    render(<DashboardPage />)
    
    expect(screen.getByText('Failed to load validations')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('passes empty state to ValidationList', async () => {
    mockValidationsQuery.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    })

    const DashboardPage = (await import('@/app/dashboard/page')).default
    render(<DashboardPage />)
    
    expect(screen.getByText('No validations yet')).toBeInTheDocument()
    expect(screen.getByText('Create Your First Validation')).toBeInTheDocument()
  })

  it('has responsive layout structure', async () => {
    mockValidationsQuery.mockReturnValue({
      data: mockValidations,
      isLoading: false,
      error: null,
    })

    const DashboardPage = (await import('@/app/dashboard/page')).default
    render(<DashboardPage />)
    
    // Check that the dashboard renders with proper structure
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Welcome back, John')).toBeInTheDocument()
    expect(screen.getByText('Sign Out')).toBeInTheDocument()
  })

  it('renders with proper container max-width', async () => {
    mockValidationsQuery.mockReturnValue({
      data: mockValidations,
      isLoading: false,
      error: null,
    })

    const DashboardPage = (await import('@/app/dashboard/page')).default
    render(<DashboardPage />)
    
    const containers = document.querySelectorAll('.max-w-7xl')
    expect(containers.length).toBeGreaterThan(0)
  })
})