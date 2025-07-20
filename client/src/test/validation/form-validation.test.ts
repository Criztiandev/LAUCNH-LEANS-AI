import { describe, it, expect } from 'vitest'
import { createValidationSchema } from '@/lib/validations/validation'

describe('Validation Form Schema', () => {
  describe('title validation', () => {
    it('should accept valid title', () => {
      const result = createValidationSchema.safeParse({
        title: 'Valid SaaS Idea Title',
        ideaText: 'This is a valid idea description that meets the minimum length requirement.',
      })

      expect(result.success).toBe(true)
    })

    it('should reject empty title', () => {
      const result = createValidationSchema.safeParse({
        title: '',
        ideaText: 'This is a valid idea description that meets the minimum length requirement.',
      })

      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Title is required')
      }
    })

    it('should reject title longer than 255 characters', () => {
      const longTitle = 'a'.repeat(256)
      const result = createValidationSchema.safeParse({
        title: longTitle,
        ideaText: 'This is a valid idea description that meets the minimum length requirement.',
      })

      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Title must be less than 255 characters')
      }
    })

    it('should accept title with exactly 255 characters', () => {
      const maxTitle = 'a'.repeat(255)
      const result = createValidationSchema.safeParse({
        title: maxTitle,
        ideaText: 'This is a valid idea description that meets the minimum length requirement.',
      })

      expect(result.success).toBe(true)
    })

    it('should accept title with 1 character', () => {
      const result = createValidationSchema.safeParse({
        title: 'a',
        ideaText: 'This is a valid idea description that meets the minimum length requirement.',
      })

      expect(result.success).toBe(true)
    })
  })

  describe('ideaText validation', () => {
    it('should accept valid idea text', () => {
      const result = createValidationSchema.safeParse({
        title: 'Valid Title',
        ideaText: 'This is a valid idea description that meets the minimum length requirement and provides enough detail.',
      })

      expect(result.success).toBe(true)
    })

    it('should reject idea text shorter than 10 characters', () => {
      const result = createValidationSchema.safeParse({
        title: 'Valid Title',
        ideaText: 'Short',
      })

      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Idea description must be at least 10 characters')
      }
    })

    it('should reject idea text longer than 1000 characters', () => {
      const longIdeaText = 'a'.repeat(1001)
      const result = createValidationSchema.safeParse({
        title: 'Valid Title',
        ideaText: longIdeaText,
      })

      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Idea description must be less than 1000 characters')
      }
    })

    it('should accept idea text with exactly 10 characters', () => {
      const result = createValidationSchema.safeParse({
        title: 'Valid Title',
        ideaText: 'a'.repeat(10),
      })

      expect(result.success).toBe(true)
    })

    it('should accept idea text with exactly 1000 characters', () => {
      const result = createValidationSchema.safeParse({
        title: 'Valid Title',
        ideaText: 'a'.repeat(1000),
      })

      expect(result.success).toBe(true)
    })

    it('should reject empty idea text', () => {
      const result = createValidationSchema.safeParse({
        title: 'Valid Title',
        ideaText: '',
      })

      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Idea description must be at least 10 characters')
      }
    })
  })

  describe('combined validation', () => {
    it('should reject both invalid title and idea text', () => {
      const result = createValidationSchema.safeParse({
        title: '',
        ideaText: 'Short',
      })

      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues).toHaveLength(2)
        const messages = result.error.issues.map(issue => issue.message)
        expect(messages).toContain('Title is required')
        expect(messages).toContain('Idea description must be at least 10 characters')
      }
    })

    it('should accept valid data at boundary values', () => {
      const result = createValidationSchema.safeParse({
        title: 'a'.repeat(255),
        ideaText: 'a'.repeat(1000),
      })

      expect(result.success).toBe(true)
    })

    it('should handle missing fields', () => {
      const result = createValidationSchema.safeParse({})

      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues).toHaveLength(2)
        const messages = result.error.issues.map(issue => issue.message)
        // Zod generates "Title is required" and "Idea description is required" for missing required fields
        expect(messages).toContain('Title is required')
        expect(messages).toContain('Idea description is required')
        const titleIssue = result.error.issues.find(issue => issue.path[0] === 'title')
        const ideaTextIssue = result.error.issues.find(issue => issue.path[0] === 'ideaText')
        expect(titleIssue).toBeDefined()
        expect(ideaTextIssue).toBeDefined()
      }
    })
  })
})