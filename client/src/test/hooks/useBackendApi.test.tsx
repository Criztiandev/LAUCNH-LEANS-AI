/**
 * Tests for useBackendApi hook
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useBackendApi } from '@/hooks/useBackendApi'
import { BackendApiError } from '@/lib/api'

// Mock the api module
vi.mock('@/lib/api', () => ({
  backendApi: {
    processValidation: vi.fn(),
    healthCheck: vi.fn(),
  },
  BackendApiError: class extends Error {
    constructor(message: string, public status: number = 500, public detail?: string) {
      super(message)
      this.name = 'BackendApiError'
      this.detail = detail || message
    }
  },
}))

import { backendApi } from '@/lib/api'

const mockBackendApi = vi.mocked(backendApi)

describe('useBackendApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useBackendApi())

    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBe(null)
    expect(result.current.isConnected).toBe(null)
  })

  describe('processValidation', () => {
    it('should handle successful validation processing', async () => {
      const mockResponse = {
        message: 'Validation processing started',
        validation_id: 'test-id',
        status: 'processing'
      }

      mockBackendApi.processValidation.mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useBackendApi())

      let response: any
      await act(async () => {
        response = await result.current.processValidation('test-id')
      })

      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBe(null)
      expect(result.current.isConnected).toBe(true)
      expect(response).toEqual(mockResponse)
      expect(mockBackendApi.processValidation).toHaveBeenCalledWith('test-id')
    })

    it('should handle network connection errors', async () => {
      const networkError = new BackendApiError('Network error', 0, 'Network connection failed')
      mockBackendApi.processValidation.mockRejectedValueOnce(networkError)

      const { result } = renderHook(() => useBackendApi())

      let response: any
      await act(async () => {
        response = await result.current.processValidation('test-id')
      })

      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBe('Unable to connect to processing service. Please check if the backend is running.')
      expect(result.current.isConnected).toBe(false)
      expect(response).toBe(null)
    })

    it('should handle 400 Bad Request errors', async () => {
      const badRequestError = new BackendApiError('Bad request', 400, 'Validation already processing')
      mockBackendApi.processValidation.mockRejectedValueOnce(badRequestError)

      const { result } = renderHook(() => useBackendApi())

      let response: any
      await act(async () => {
        response = await result.current.processValidation('test-id')
      })

      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBe('Processing error: Validation already processing')
      expect(result.current.isConnected).toBe(true)
      expect(response).toBe(null)
    })

    it('should handle 404 Not Found errors', async () => {
      const notFoundError = new BackendApiError('Not found', 404, 'Validation not found')
      mockBackendApi.processValidation.mockRejectedValueOnce(notFoundError)

      const { result } = renderHook(() => useBackendApi())

      let response: any
      await act(async () => {
        response = await result.current.processValidation('test-id')
      })

      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBe('Validation not found')
      expect(result.current.isConnected).toBe(true)
      expect(response).toBe(null)
    })

    it('should handle generic server errors', async () => {
      const serverError = new BackendApiError('Server error', 500, 'Internal server error')
      mockBackendApi.processValidation.mockRejectedValueOnce(serverError)

      const { result } = renderHook(() => useBackendApi())

      let response: any
      await act(async () => {
        response = await result.current.processValidation('test-id')
      })

      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBe('Processing service error: Internal server error')
      expect(result.current.isConnected).toBe(true)
      expect(response).toBe(null)
    })

    it('should handle non-BackendApiError exceptions', async () => {
      const genericError = new Error('Generic error')
      mockBackendApi.processValidation.mockRejectedValueOnce(genericError)

      const { result } = renderHook(() => useBackendApi())

      let response: any
      await act(async () => {
        response = await result.current.processValidation('test-id')
      })

      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBe('Failed to start validation processing')
      expect(response).toBe(null)
    })
  })

  describe('checkHealth', () => {
    it('should handle successful health check', async () => {
      const mockResponse = { status: 'healthy', timestamp: '2024-01-01T00:00:00Z' }
      mockBackendApi.healthCheck.mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useBackendApi())

      let isHealthy: boolean
      await act(async () => {
        isHealthy = await result.current.checkHealth()
      })

      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBe(null)
      expect(result.current.isConnected).toBe(true)
      expect(isHealthy!).toBe(true)
    })

    it('should handle health check failures', async () => {
      const networkError = new BackendApiError('Network error', 0)
      mockBackendApi.healthCheck.mockRejectedValueOnce(networkError)

      const { result } = renderHook(() => useBackendApi())

      let isHealthy: boolean
      await act(async () => {
        isHealthy = await result.current.checkHealth()
      })

      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBe('Unable to connect to backend service')
      expect(result.current.isConnected).toBe(false)
      expect(isHealthy!).toBe(false)
    })
  })

  describe('utility functions', () => {
    it('should clear error', async () => {
      const networkError = new BackendApiError('Network error', 0)
      mockBackendApi.processValidation.mockRejectedValueOnce(networkError)

      const { result } = renderHook(() => useBackendApi())

      // First cause an error
      await act(async () => {
        await result.current.processValidation('test-id')
      })

      expect(result.current.error).toBeTruthy()

      // Then clear it
      act(() => {
        result.current.clearError()
      })

      expect(result.current.error).toBe(null)
    })

    it('should reset state', async () => {
      const networkError = new BackendApiError('Network error', 0)
      mockBackendApi.processValidation.mockRejectedValueOnce(networkError)

      const { result } = renderHook(() => useBackendApi())

      // First cause an error
      await act(async () => {
        await result.current.processValidation('test-id')
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.isConnected).toBe(false)

      // Then reset
      act(() => {
        result.current.reset()
      })

      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBe(null)
      expect(result.current.isConnected).toBe(null)
    })
  })
})