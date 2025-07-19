import { z } from 'zod'

export const loginSchema = z.object({
  email: z
    .string({error:'Email is required' })
    .min(1, 'Email is required')
    .email('Invalid email address'),
  password: z
    .string({error:'Password is required' })
    .min(6, 'Password must be at least 6 characters')
})

export const signupSchema = z.object({
  firstName: z
    .string({error:'First name is required' })
    .min(1, 'First name is required')
    .max(50, 'First name must be less than 50 characters'),
  email: z
    .string({error:'Email is required' })
    .min(1, 'Email is required')
    .email('Invalid email address'),
  password: z
    .string({error:'Password is required' })
    .min(6, 'Password must be at least 6 characters')
    .max(100, 'Password must be less than 100 characters'),
  confirmPassword: z
    .string({error:'Please confirm your password' })
    .min(1, 'Please confirm your password')
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword']
})

export type LoginFormData = z.infer<typeof loginSchema>
export type SignupFormData = z.infer<typeof signupSchema>