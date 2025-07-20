/**
 * HTTP client configuration for frontend-backend communication
 */

interface ProcessValidationRequest {
  validation_id: string
}

interface ProcessValidationResponse {
  message: string
  validation_id: string
  status: string
}

interface ApiError {
  detail: string
  status?: number
}

class BackendApiError extends Error {
  public status: number
  public detail: string

  constructor(message: string, status: number = 500, detail?: string) {
    super(message)
    this.name = 'BackendApiError'
    this.status = status
    this.detail = detail || message
  }
}

/**
 * HTTP client for communicating with FastAPI backend
 */
export class BackendApiClient {
  private baseUrl: string

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_FASTAPI_URL || process.env.FASTAPI_URL || 'http://localhost:8000'
  }

  /**
   * Make HTTP request with error handling
   */
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      if (!response.ok) {
        let errorDetail = `HTTP ${response.status}: ${response.statusText}`
        
        try {
          const errorData: ApiError = await response.json()
          errorDetail = errorData.detail || errorDetail
        } catch {
          // If we can't parse error JSON, use the status text
        }

        throw new BackendApiError(
          `Backend API request failed: ${errorDetail}`,
          response.status,
          errorDetail
        )
      }

      return await response.json()
    } catch (error) {
      if (error instanceof BackendApiError) {
        throw error
      }

      // Handle network errors, timeout, etc.
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new BackendApiError(
          'Unable to connect to backend service. Please check if the backend is running.',
          0,
          'Network connection failed'
        )
      }

      throw new BackendApiError(
        `Unexpected error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        500
      )
    }
  }

  /**
   * Trigger validation processing
   */
  async processValidation(validationId: string): Promise<ProcessValidationResponse> {
    return this.makeRequest<ProcessValidationResponse>('/api/process-validation', {
      method: 'POST',
      body: JSON.stringify({
        validation_id: validationId,
      }),
    })
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.makeRequest<{ status: string; timestamp: string }>('/api/health')
  }
}

// Export singleton instance
export const backendApi = new BackendApiClient()

// Export error class for error handling
export { BackendApiError }
export type { ProcessValidationRequest, ProcessValidationResponse, ApiError }