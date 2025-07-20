import { z } from 'zod'

export const createValidationSchema = z.object({
  title: z
    .string({ message: 'Title is required' })
    .min(1, 'Title is required')
    .max(255, 'Title must be less than 255 characters'),
  ideaText: z
    .string({ message: 'Idea description is required' })
    .min(10, 'Idea description must be at least 10 characters')
    .max(1000, 'Idea description must be less than 1000 characters')
})

export type CreateValidationFormData = z.infer<typeof createValidationSchema>