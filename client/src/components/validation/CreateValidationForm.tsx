'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { trpc } from '@/lib/trpc/client'
import { createValidationSchema, type CreateValidationFormData } from '@/lib/validations/validation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

export function CreateValidationForm() {
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
  } = useForm<CreateValidationFormData>({
    resolver: zodResolver(createValidationSchema),
  })

  const createValidation = trpc.validations.create.useMutation({
    onSuccess: () => {
      router.push(`/dashboard`)
    },
    onError: (error) => {
      setError(error.message || 'Failed to create validation')
    },
  })

  const onSubmit = async (data: CreateValidationFormData) => {
    try {
      setError(null)
      await createValidation.mutateAsync(data)
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
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
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
            disabled={isSubmitting || createValidation.isPending}
            className="w-full"
          >
            {isSubmitting || createValidation.isPending
              ? 'Creating Validation...'
              : 'Create Validation'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}