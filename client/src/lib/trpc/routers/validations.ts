import { z } from 'zod'
import { eq, desc } from 'drizzle-orm'
import { createTRPCRouter, protectedProcedure } from '../server'
import { validations, competitors, feedback, aiAnalysis } from '@/lib/db/schema'

const createValidationSchema = z.object({
  title: z.string().min(1).max(255),
  ideaText: z.string().min(10).max(1000),
})

export const validationsRouter = createTRPCRouter({
  create: protectedProcedure
    .input(createValidationSchema)
    .mutation(async ({ ctx, input }) => {
      const [validation] = await ctx.db
        .insert(validations)
        .values({
          userId: ctx.user.id,
          title: input.title,
          ideaText: input.ideaText,
          status: 'processing',
        })
        .returning()

      return validation
    }),

  getAll: protectedProcedure.query(async ({ ctx }) => {
    return await ctx.db
      .select()
      .from(validations)
      .where(eq(validations.userId, ctx.user.id))
      .orderBy(desc(validations.createdAt))
  }),

  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ ctx, input }) => {
      const validation = await ctx.db
        .select()
        .from(validations)
        .where(eq(validations.id, input.id))
        .limit(1)

      if (!validation.length || validation[0].userId !== ctx.user.id) {
        throw new Error('Validation not found')
      }

      const [competitorsData, feedbackData, aiAnalysisData] = await Promise.all([
        ctx.db
          .select()
          .from(competitors)
          .where(eq(competitors.validationId, input.id)),
        ctx.db
          .select()
          .from(feedback)
          .where(eq(feedback.validationId, input.id)),
        ctx.db
          .select()
          .from(aiAnalysis)
          .where(eq(aiAnalysis.validationId, input.id))
          .limit(1),
      ])

      return {
        validation: validation[0],
        competitors: competitorsData,
        feedback: feedbackData,
        aiAnalysis: aiAnalysisData[0] || null,
      }
    }),

  updateStatus: protectedProcedure
    .input(z.object({
      id: z.string().uuid(),
      status: z.enum(['processing', 'completed', 'failed']),
      marketScore: z.number().min(1).max(10).optional(),
      completedAt: z.date().optional(),
    }))
    .mutation(async ({ ctx, input }) => {
      const [validation] = await ctx.db
        .update(validations)
        .set({
          status: input.status,
          marketScore: input.marketScore?.toString(),
          completedAt: input.completedAt,
        })
        .where(eq(validations.id, input.id))
        .returning()

      return validation
    }),
})