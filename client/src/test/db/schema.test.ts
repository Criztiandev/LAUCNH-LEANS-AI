import { describe, it, expect } from 'vitest'
import { validations, competitors, feedback, aiAnalysis, profiles } from '@/lib/db/schema'

describe('Database Schema', () => {
  it('should have correct table structures', () => {
    // Test validations table structure
    expect(validations).toBeDefined()
    expect(validations.id).toBeDefined()
    expect(validations.userId).toBeDefined()
    expect(validations.title).toBeDefined()
    expect(validations.ideaText).toBeDefined()
    expect(validations.marketScore).toBeDefined()
    expect(validations.status).toBeDefined()
    expect(validations.createdAt).toBeDefined()
    expect(validations.completedAt).toBeDefined()
    expect(validations.competitorCount).toBeDefined()
    expect(validations.feedbackCount).toBeDefined()
    expect(validations.sourcesScraped).toBeDefined()

    // Test competitors table structure
    expect(competitors).toBeDefined()
    expect(competitors.id).toBeDefined()
    expect(competitors.validationId).toBeDefined()
    expect(competitors.name).toBeDefined()
    expect(competitors.description).toBeDefined()
    expect(competitors.website).toBeDefined()
    expect(competitors.estimatedUsers).toBeDefined()
    expect(competitors.estimatedRevenue).toBeDefined()
    expect(competitors.pricingModel).toBeDefined()
    expect(competitors.source).toBeDefined()
    expect(competitors.sourceUrl).toBeDefined()
    expect(competitors.confidenceScore).toBeDefined()
    expect(competitors.createdAt).toBeDefined()

    // Test feedback table structure
    expect(feedback).toBeDefined()
    expect(feedback.id).toBeDefined()
    expect(feedback.validationId).toBeDefined()
    expect(feedback.text).toBeDefined()
    expect(feedback.sentiment).toBeDefined()
    expect(feedback.sentimentScore).toBeDefined()
    expect(feedback.source).toBeDefined()
    expect(feedback.sourceUrl).toBeDefined()
    expect(feedback.authorInfo).toBeDefined()
    expect(feedback.createdAt).toBeDefined()

    // Test ai_analysis table structure
    expect(aiAnalysis).toBeDefined()
    expect(aiAnalysis.id).toBeDefined()
    expect(aiAnalysis.validationId).toBeDefined()
    expect(aiAnalysis.marketOpportunity).toBeDefined()
    expect(aiAnalysis.competitiveAnalysis).toBeDefined()
    expect(aiAnalysis.strategicRecommendations).toBeDefined()
    expect(aiAnalysis.riskAssessment).toBeDefined()
    expect(aiAnalysis.gtmStrategy).toBeDefined()
    expect(aiAnalysis.featurePriorities).toBeDefined()
    expect(aiAnalysis.executiveSummary).toBeDefined()
    expect(aiAnalysis.createdAt).toBeDefined()

    // Test profiles table structure
    expect(profiles).toBeDefined()
    expect(profiles.id).toBeDefined()
    expect(profiles.firstName).toBeDefined()
    expect(profiles.createdAt).toBeDefined()
    expect(profiles.updatedAt).toBeDefined()
  })

  it('should have correct type exports', () => {
    // This test ensures our TypeScript types are properly exported
    // The actual type checking happens at compile time
    // We test that the schema objects are properly constructed Drizzle tables
    expect(typeof validations).toBe('object')
    expect(typeof competitors).toBe('object')
    expect(typeof feedback).toBe('object')
    expect(typeof aiAnalysis).toBe('object')
    expect(typeof profiles).toBe('object')
    
    // Test that they have the basic table structure
    expect(validations).toHaveProperty('id')
    expect(competitors).toHaveProperty('id')
    expect(feedback).toHaveProperty('id')
    expect(aiAnalysis).toHaveProperty('id')
    expect(profiles).toHaveProperty('id')
  })
})