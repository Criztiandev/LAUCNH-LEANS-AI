import { describe, it, expect } from 'vitest'
import { loginSchema, signupSchema } from '@/lib/validations/auth'

describe('Auth Validation Schemas', () => {
  describe('loginSchema', () => {
    it('should validate correct login data', () => {
      const validData = {
        email: 'test@example.com',
        password: 'password123'
      }

      const result = loginSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject invalid email', () => {
      const invalidData = {
        email: 'invalid-email',
        password: 'password123'
      }

      const result = loginSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Invalid email address')
      }
    })

    it('should reject empty email', () => {
      const invalidData = {
        email: '',
        password: 'password123'
      }

      const result = loginSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Email is required')
      }
    })

    it('should reject short password', () => {
      const invalidData = {
        email: 'test@example.com',
        password: '123'
      }

      const result = loginSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Password must be at least 6 characters')
      }
    })

    it('should reject missing fields', () => {
      const invalidData = {}

      const result = loginSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues).toHaveLength(2)
        const messages = result.error.issues.map(issue => issue.message)
        // Check that the paths are correct
        const paths = result.error.issues.map(issue => issue.path[0])
        expect(paths).toContain('email')
        expect(paths).toContain('password')
        // Check that we get required error messages
        expect(messages).toContain('Email is required')
        expect(messages).toContain('Password is required')
      }
    })
  })

  describe('signupSchema', () => {
    it('should validate correct signup data', () => {
      const validData = {
        firstName: 'John',
        email: 'john@example.com',
        password: 'password123',
        confirmPassword: 'password123'
      }

      const result = signupSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject mismatched passwords', () => {
      const invalidData = {
        firstName: 'John',
        email: 'john@example.com',
        password: 'password123',
        confirmPassword: 'different123'
      }

      const result = signupSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe("Passwords don't match")
        expect(result.error.issues[0].path).toEqual(['confirmPassword'])
      }
    })

    it('should reject empty first name', () => {
      const invalidData = {
        firstName: '',
        email: 'john@example.com',
        password: 'password123',
        confirmPassword: 'password123'
      }

      const result = signupSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('First name is required')
      }
    })

    it('should reject long first name', () => {
      const invalidData = {
        firstName: 'a'.repeat(51), // 51 characters
        email: 'john@example.com',
        password: 'password123',
        confirmPassword: 'password123'
      }

      const result = signupSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('First name must be less than 50 characters')
      }
    })

    it('should reject invalid email format', () => {
      const invalidData = {
        firstName: 'John',
        email: 'invalid-email',
        password: 'password123',
        confirmPassword: 'password123'
      }

      const result = signupSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Invalid email address')
      }
    })

    it('should reject long password', () => {
      const longPassword = 'a'.repeat(101) // 101 characters
      const invalidData = {
        firstName: 'John',
        email: 'john@example.com',
        password: longPassword,
        confirmPassword: longPassword
      }

      const result = signupSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Password must be less than 100 characters')
      }
    })

    it('should reject all missing fields', () => {
      const invalidData = {}

      const result = signupSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues).toHaveLength(4)
        const messages = result.error.issues.map(issue => issue.message)
        // Check that all required paths are present
        const paths = result.error.issues.map(issue => issue.path[0])
        expect(paths).toContain('firstName')
        expect(paths).toContain('email')
        expect(paths).toContain('password')
        expect(paths).toContain('confirmPassword')
        // Check that we get required error messages
        expect(messages).toContain('First name is required')
        expect(messages).toContain('Email is required')
        expect(messages).toContain('Password is required')
        expect(messages).toContain('Please confirm your password')
      }
    })

    it('should handle edge case with valid minimum values', () => {
      const validData = {
        firstName: 'A', // 1 character (minimum)
        email: 'a@b.co', // Valid minimal email
        password: '123456', // 6 characters (minimum)
        confirmPassword: '123456'
      }

      const result = signupSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should handle edge case with valid maximum values', () => {
      const validData = {
        firstName: 'a'.repeat(50), // 50 characters (maximum)
        email: 'test@example.com',
        password: 'a'.repeat(100), // 100 characters (maximum)
        confirmPassword: 'a'.repeat(100)
      }

      const result = signupSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })
})