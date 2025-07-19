import { pgTable, uuid, text, timestamp, decimal, integer, jsonb, check } from 'drizzle-orm/pg-core'
import { relations, sql } from 'drizzle-orm'

// Profiles table
export const profiles = pgTable('profiles', {
  id: uuid('id').primaryKey(),
  firstName: text('first_name'),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).defaultNow(),
})

// Validations table
export const validations = pgTable('validations', {
  id: uuid('id').defaultRandom().primaryKey(),
  userId: uuid('user_id').notNull(),
  title: text('title').notNull(),
  ideaText: text('idea_text').notNull(),
  marketScore: decimal('market_score', { precision: 3, scale: 1 }),
  status: text('status', { enum: ['processing', 'completed', 'failed'] }).notNull().default('processing'),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow(),
  completedAt: timestamp('completed_at', { withTimezone: true }),
  competitorCount: integer('competitor_count').default(0),
  feedbackCount: integer('feedback_count').default(0),
  sourcesScraped: jsonb('sources_scraped').default([]),
}, (table) => ({
  titleLengthCheck: check('title_length_check', sql`LENGTH(${table.title}) >= 1 AND LENGTH(${table.title}) <= 255`),
  ideaTextLengthCheck: check('idea_text_length_check', sql`LENGTH(${table.ideaText}) >= 10 AND LENGTH(${table.ideaText}) <= 1000`),
  marketScoreCheck: check('market_score_check', sql`${table.marketScore} >= 1.0 AND ${table.marketScore} <= 10.0`),
}))

// Competitors table
export const competitors = pgTable('competitors', {
  id: uuid('id').defaultRandom().primaryKey(),
  validationId: uuid('validation_id').notNull(),
  name: text('name').notNull(),
  description: text('description'),
  website: text('website'),
  estimatedUsers: integer('estimated_users'),
  estimatedRevenue: text('estimated_revenue'),
  pricingModel: text('pricing_model'),
  source: text('source').notNull(),
  sourceUrl: text('source_url'),
  confidenceScore: decimal('confidence_score', { precision: 3, scale: 2 }).default('0.5'),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow(),
}, (table) => ({
  confidenceScoreCheck: check('confidence_score_check', sql`${table.confidenceScore} >= 0.0 AND ${table.confidenceScore} <= 1.0`),
}))

// Feedback table
export const feedback = pgTable('feedback', {
  id: uuid('id').defaultRandom().primaryKey(),
  validationId: uuid('validation_id').notNull(),
  text: text('text').notNull(),
  sentiment: text('sentiment', { enum: ['positive', 'negative', 'neutral'] }).notNull(),
  sentimentScore: decimal('sentiment_score', { precision: 3, scale: 2 }).default('0.0'),
  source: text('source').notNull(),
  sourceUrl: text('source_url'),
  authorInfo: jsonb('author_info').default({}),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow(),
}, (table) => ({
  sentimentScoreCheck: check('sentiment_score_check', sql`${table.sentimentScore} >= -1.0 AND ${table.sentimentScore} <= 1.0`),
}))

// AI Analysis table
export const aiAnalysis = pgTable('ai_analysis', {
  id: uuid('id').defaultRandom().primaryKey(),
  validationId: uuid('validation_id').notNull(),
  marketOpportunity: text('market_opportunity'),
  competitiveAnalysis: text('competitive_analysis'),
  strategicRecommendations: text('strategic_recommendations'),
  riskAssessment: text('risk_assessment'),
  gtmStrategy: text('gtm_strategy'),
  featurePriorities: text('feature_priorities'),
  executiveSummary: text('executive_summary'),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow(),
})

// Relations
export const validationsRelations = relations(validations, ({ many, one }) => ({
  competitors: many(competitors),
  feedback: many(feedback),
  aiAnalysis: one(aiAnalysis),
  profile: one(profiles, {
    fields: [validations.userId],
    references: [profiles.id],
  }),
}))

export const competitorsRelations = relations(competitors, ({ one }) => ({
  validation: one(validations, {
    fields: [competitors.validationId],
    references: [validations.id],
  }),
}))

export const feedbackRelations = relations(feedback, ({ one }) => ({
  validation: one(validations, {
    fields: [feedback.validationId],
    references: [validations.id],
  }),
}))

export const aiAnalysisRelations = relations(aiAnalysis, ({ one }) => ({
  validation: one(validations, {
    fields: [aiAnalysis.validationId],
    references: [validations.id],
  }),
}))

export const profilesRelations = relations(profiles, ({ many }) => ({
  validations: many(validations),
}))

// Types
export type Validation = typeof validations.$inferSelect
export type NewValidation = typeof validations.$inferInsert
export type Competitor = typeof competitors.$inferSelect
export type NewCompetitor = typeof competitors.$inferInsert
export type Feedback = typeof feedback.$inferSelect
export type NewFeedback = typeof feedback.$inferInsert
export type AIAnalysis = typeof aiAnalysis.$inferSelect
export type NewAIAnalysis = typeof aiAnalysis.$inferInsert
export type Profile = typeof profiles.$inferSelect
export type NewProfile = typeof profiles.$inferInsert