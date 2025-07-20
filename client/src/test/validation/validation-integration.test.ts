import { describe, it, expect } from 'vitest'
import { createValidationSchema } from '@/lib/validations/validation'

describe('Validation Integration Tests', () => {
  describe('Schema Integration', () => {
    it('should validate data that would be sent to tRPC', () => {
      const validData = {
        title: 'Revolutionary SaaS Platform',
        ideaText: 'This is a comprehensive SaaS platform that will revolutionize how businesses manage their operations.',
      }

      const result = createValidationSchema.safeParse(validData)
      expect(result.success).toBe(true)
      
      if (result.success) {
        expect(result.data.title).toBe(validData.title)
        expect(result.data.ideaText).toBe(validData.ideaText)
      }
    })

    it('should reject invalid data that would be sent to tRPC', () => {
      const invalidData = {
        title: '', // Too short
        ideaText: 'Short', // Too short
      }

      const result = createValidationSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      
      if (!result.success) {
        expect(result.error.issues).toHaveLength(2)
        const messages = result.error.issues.map(issue => issue.message)
        expect(messages).toContain('Title is required')
        expect(messages).toContain('Idea description must be at least 10 characters')
      }
    })

    it('should handle boundary cases correctly', () => {
      const boundaryData = {
        title: 'a'.repeat(255), // Exactly at limit
        ideaText: 'a'.repeat(1000), // Exactly at limit
      }

      const result = createValidationSchema.safeParse(boundaryData)
      expect(result.success).toBe(true)
    })

    it('should reject data exceeding limits', () => {
      const exceedingData = {
        title: 'a'.repeat(256), // Over limit
        ideaText: 'a'.repeat(1001), // Over limit
      }

      const result = createValidationSchema.safeParse(exceedingData)
      expect(result.success).toBe(false)
      
      if (!result.success) {
        expect(result.error.issues).toHaveLength(2)
        const messages = result.error.issues.map(issue => issue.message)
        expect(messages).toContain('Title must be less than 255 characters')
        expect(messages).toContain('Idea description must be less than 1000 characters')
      }
    })
  })

  describe('Database Schema Compatibility', () => {
    it('should match database constraints for title', () => {
      // Test minimum length
      const minTitle = { title: 'a', ideaText: 'Valid idea text for testing purposes' }
      expect(createValidationSchema.safeParse(minTitle).success).toBe(true)

      // Test maximum length
      const maxTitle = { title: 'a'.repeat(255), ideaText: 'Valid idea text for testing purposes' }
      expect(createValidationSchema.safeParse(maxTitle).success).toBe(true)

      // Test over maximum
      const overMaxTitle = { title: 'a'.repeat(256), ideaText: 'Valid idea text for testing purposes' }
      expect(createValidationSchema.safeParse(overMaxTitle).success).toBe(false)
    })

    it('should match database constraints for ideaText', () => {
      // Test minimum length
      const minIdea = { title: 'Valid Title', ideaText: 'a'.repeat(10) }
      expect(createValidationSchema.safeParse(minIdea).success).toBe(true)

      // Test maximum length
      const maxIdea = { title: 'Valid Title', ideaText: 'a'.repeat(1000) }
      expect(createValidationSchema.safeParse(maxIdea).success).toBe(true)

      // Test over maximum
      const overMaxIdea = { title: 'Valid Title', ideaText: 'a'.repeat(1001) }
      expect(createValidationSchema.safeParse(overMaxIdea).success).toBe(false)
    })
  })

  describe('Real-world Data Scenarios', () => {
    it('should handle typical SaaS idea submissions', () => {
      const typicalIdeas = [
        {
          title: 'Project Management Tool',
          ideaText: 'A comprehensive project management tool that helps teams collaborate more effectively with real-time updates and task tracking.',
        },
        {
          title: 'Customer Support Platform',
          ideaText: 'An AI-powered customer support platform that automates responses and provides intelligent routing of support tickets.',
        },
        {
          title: 'E-commerce Analytics Dashboard',
          ideaText: 'A powerful analytics dashboard for e-commerce businesses to track sales, customer behavior, and inventory management.',
        },
      ]

      typicalIdeas.forEach((idea) => {
        const result = createValidationSchema.safeParse(idea)
        expect(result.success).toBe(true)
      })
    })

    it('should reject common invalid submissions', () => {
      const invalidIdeas = [
        {
          title: '', // Empty title
          ideaText: 'Valid idea description that meets the minimum requirements.',
        },
        {
          title: 'Valid Title',
          ideaText: 'Short', // Too short
        },
        {
          title: 'Valid Title',
          ideaText: '', // Empty idea
        },
      ]

      invalidIdeas.forEach((idea) => {
        const result = createValidationSchema.safeParse(idea)
        expect(result.success).toBe(false)
      })
    })
  })
})