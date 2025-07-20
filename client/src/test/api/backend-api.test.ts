/**
 * Integration tests for backend API client
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { BackendApiClient, BackendApiError } from '@/lib/api'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('BackendApiClient', () => {
  let apiClient: BackendApiClient
  
  beforeEach(() => {
    apiClient = new BackendApiClient()
    mockFetch.mockClear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('processValidation', () => {
    it('should successfully trigger validation processing', async () => {
      const mockResponse = {
        message: 'Validation processing started',
        validation_id: 'test-validation-id',
        status: 'processing'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await apiClient.processValidation('test-validation-id')

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/process-validation',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            validation_id: 'test-validation-id',
          }),
        }
      )

      expect(result).toEqual(mockResponse)
    })

    it('should handle 400 Bad Request errors', async () => {
      const errorResponse = {
        detail: 'Validation test-validation-id is already being processed'
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => errorResponse,
      })

      await expect(apiClient.processValidation('test-validation-id'))
        .rejects.toThrow(BackendApiError)

      try {
        await apiClient.processValidation('test-validation-id')
      } catch (error) {
        expect(error).toBeInstanceOf(BackendApiError)
        expect((error as BackendApiError).status).toBe(400)
        expect((error as BackendApiError).detail).toBe(errorResponse.detail)
      }
    })

    it('should handle 404 Not Found errors', async () => {
      const errorResponse = {
        detail: 'Validation test-validation-id not found'
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => errorResponse,
      })

      await expect(apiClient.processValidation('test-validation-id'))
        .rejects.toThrow(BackendApiError)

      try {
        await apiClient.processValidation('test-validation-id')
      } catch (error) {
        expect(error).toBeInstanceOf(BackendApiError)
        expect((error as BackendApiError).status).toBe(404)
        expect((error as BackendApiError).detail).toBe(errorResponse.detail)
      }
    })

    it('should handle network connection errors', async () => {
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      await expect(apiClient.processValidation('test-validation-id'))
        .rejects.toThrow(BackendApiError)

      try {
        await apiClient.processValidation('test-validation-id')
      } catch (error) {
        expect(error).toBeInstanceOf(BackendApiError)
        expect((error as BackendApiError).status).toBe(0)
        expect((error as BackendApiError).detail).toBe('Network connection failed')
      }
    })

    it('should handle server errors without JSON response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      await expect(apiClient.processValidation('test-validation-id'))
        .rejects.toThrow(BackendApiError)

      try {
        await apiClient.processValidation('test-validation-id')
      } catch (error) {
        expect(error).toBeInstanceOf(BackendApiError)
        expect((error as BackendApiError).status).toBe(500)
        expect((error as BackendApiError).detail).toBe('HTTP 500: Internal Server Error')
      }
    })
  })

  describe('healthCheck', () => {
    it('should successfully check backend health', async () => {
      const mockResponse = {
        status: 'healthy',
        timestamp: '2024-01-01T00:00:00Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await apiClient.healthCheck()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/health',
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )

      expect(result).toEqual(mockResponse)
    })

    it('should handle health check failures', async () => {
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      await expect(apiClient.healthCheck())
        .rejects.toThrow(BackendApiError)
    })
  })

  describe('constructor', () => {
    it('should use NEXT_PUBLIC_FASTAPI_URL when available', () => {
      const originalEnv = process.env.NEXT_PUBLIC_FASTAPI_URL
      process.env.NEXT_PUBLIC_FASTAPI_URL = 'https://api.example.com'
      
      const client = new BackendApiClient()
      
      // Access private baseUrl through type assertion for testing
      expect((client as any).baseUrl).toBe('https://api.example.com')
      
      process.env.NEXT_PUBLIC_FASTAPI_URL = originalEnv
    })

    it('should fallback to FASTAPI_URL when NEXT_PUBLIC_FASTAPI_URL is not available', () => {
      const originalPublicEnv = process.env.NEXT_PUBLIC_FASTAPI_URL
      const originalEnv = process.env.FASTAPI_URL
      
      delete process.env.NEXT_PUBLIC_FASTAPI_URL
      process.env.FASTAPI_URL = 'https://backend.example.com'
      
      const client = new BackendApiClient()
      
      expect((client as any).baseUrl).toBe('https://backend.example.com')
      
      process.env.NEXT_PUBLIC_FASTAPI_URL = originalPublicEnv
      process.env.FASTAPI_URL = originalEnv
    })

    it('should use default localhost URL when no environment variables are set', () => {
      const originalPublicEnv = process.env.NEXT_PUBLIC_FASTAPI_URL
      const originalEnv = process.env.FASTAPI_URL
      
      delete process.env.NEXT_PUBLIC_FASTAPI_URL
      delete process.env.FASTAPI_URL
      
      const client = new BackendApiClient()
      
      expect((client as any).baseUrl).toBe('http://localhost:8000')
      
      process.env.NEXT_PUBLIC_FASTAPI_URL = originalPublicEnv
      process.env.FASTAPI_URL = originalEnv
    })
  })
})