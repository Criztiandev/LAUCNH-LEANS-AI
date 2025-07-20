/**
 * Custom hook for managing backend API calls with loading states and error handling
 */

import { useState, useCallback } from 'react'
import { backendApi, BackendApiError, type ProcessValidationResponse } from '@/lib/api'

interface UseBackendApiState {
  isLoading: boolean
  error: string | null
  isConnected: boolean | null
}

interface UseBackendApiReturn extends UseBackendApiState {
  processValidation: (validationId: string) => Promise<ProcessValidationResponse | null>
  checkHealth: () => Promise<boolean>
  clearError: () => void
  reset: () => void
}

export function useBackendApi(): UseBackendApiReturn {
  const [state, setState] = useState<UseBackendApiState>({
    isLoading: false,
    error: null,
    isConnected: null,
  })

  const updateState = useCallback((updates: Partial<UseBackendApiState>) => {
    setState(prev => ({ ...prev, ...updates }))
  }, [])

  const clearError = useCallback(() => {
    updateState({ error: null })
  }, [updateState])

  const reset = useCallback(() => {
    setState({
      isLoading: false,
      error: null,
      isConnected: null,
    })
  }, [])

  const processValidation = useCallback(async (validationId: string): Promise<ProcessValidationResponse | null> => {
    try {
      updateState({ isLoading: true, error: null })
      
      const response = await backendApi.processValidation(validationId)
      
      updateState({ 
        isLoading: false, 
        isConnected: true 
      })
      
      return response
    } catch (error) {
      let errorMessage = 'Failed to start validation processing'
      
      if (error instanceof BackendApiError) {
        if (error.status === 0) {
          errorMessage = 'Unable to connect to processing service. Please check if the backend is running.'
          updateState({ isConnected: false })
        } else if (error.status === 400) {
          errorMessage = `Processing error: ${error.detail}`
          updateState({ isConnected: true })
        } else if (error.status === 404) {
          errorMessage = 'Validation not found'
          updateState({ isConnected: true })
        } else {
          errorMessage = `Processing service error: ${error.detail}`
          updateState({ isConnected: true })
        }
      }
      
      updateState({ 
        isLoading: false, 
        error: errorMessage 
      })
      
      return null
    }
  }, [updateState])

  const checkHealth = useCallback(async (): Promise<boolean> => {
    try {
      updateState({ isLoading: true, error: null })
      
      await backendApi.healthCheck()
      
      updateState({ 
        isLoading: false, 
        isConnected: true 
      })
      
      return true
    } catch (error) {
      let errorMessage = 'Backend health check failed'
      
      if (error instanceof BackendApiError && error.status === 0) {
        errorMessage = 'Unable to connect to backend service'
      }
      
      updateState({ 
        isLoading: false, 
        error: errorMessage,
        isConnected: false 
      })
      
      return false
    }
  }, [updateState])

  return {
    ...state,
    processValidation,
    checkHealth,
    clearError,
    reset,
  }
}