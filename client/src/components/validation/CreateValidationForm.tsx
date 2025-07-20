'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { trpc } from '@/lib/trpc/client'
import { createValidationSchema, type CreateValidationFormData } from '@/lib/validations/validation'
import { useBackendApi } from '@/hooks/useBackendApi'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

export function CreateValidationForm() {
  const router = useRouter()
  const [formError, setFormError] = useState<string | null>(null)
  const backendApi = useBackendApi()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
  } = useForm<CreateValidationFormData>({
    resolver: zodResolver(createValidationSchema),
  })

  const createValidation = trpc.validations.create.useMutation({
    onError: (error) => {
      setFormError(error.message || 'Failed to create validation')
    },
  })

  const onSubmit = async (data: CreateValidationFormData) => {
    try {
      setFormError(null)
      backendApi.clearError()
      
      // Step 1: Create validation in database
      const validation = await createValidation.mutateAsync(data)
      
      // Step 2: Trigger backend processing
      const processingResult = await backendApi.processValidation(validation.id)
      
      if (processingResult) {
        // Success - redirect to dashboard
        router.push(`/dashboard`)
      } else {
        // Backend processing failed, but validation was created
        // Show error but still redirect after delay
        setTimeout(() => {
          router.push(`/dashboard`)
        }, 3000)
      }
    } catch {
      // Error is handled by onError callback
    }
  }

  const titleLength = watch('title')?.length || 0
  const ideaTextLength = watch('ideaText')?.length || 0

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Create New Validation</CardTitle>
        <CardDescription>
          Submit your SaaS idea for comprehensive market analysis and validation
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {(formError || backendApi.error) && (
            <Alert variant="destructive">
              <AlertDescription>
                {formError || backendApi.error}
                {backendApi.error && formError === null && (
                  <div className="mt-2 text-sm">
                    Your validation was created successfully. You can view it in your dashboard.
                  </div>
                )}
              </AlertDescription>
            </Alert>
          )}
          
          {backendApi.isConnected === false && (
            <Alert>
              <AlertDescription>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span>Backend processing service is not available</span>
                </div>
              </AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="title">
              Idea Title <span className="text-red-500">*</span>
            </Label>
            <Input
              id="title"
              type="text"
              placeholder="Enter your SaaS idea title"
              {...register('title')}
              className={errors.title ? 'border-red-500' : ''}
            />
            <div className="flex justify-between text-sm text-gray-500">
              <span>{errors.title?.message}</span>
              <span>{titleLength}/255</span>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="ideaText">
              Idea Description <span className="text-red-500">*</span>
            </Label>
            <textarea
              id="ideaText"
              rows={6}
              placeholder="Describe your SaaS idea in detail. What problem does it solve? Who is your target audience? What features would it have?"
              {...register('ideaText')}
              className={`w-full px-3 py-2 border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.ideaText ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            <div className="flex justify-between text-sm text-gray-500">
              <span>{errors.ideaText?.message}</span>
              <span>{ideaTextLength}/1000</span>
            </div>
          </div>

          <Button
            type="submit"
            disabled={isSubmitting || createValidation.isPending || backendApi.isLoading}
            className="w-full"
          >
            {isSubmitting || createValidation.isPending
              ? 'Creating Validation...'
              : backendApi.isLoading
              ? 'Starting Processing...'
              : 'Create Validation'}
          </Button>
          
          {backendApi.isLoading && (
            <div className="text-sm text-gray-600 text-center">
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                <span>Connecting to processing service...</span>
              </div>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  )
}