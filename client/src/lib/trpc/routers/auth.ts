import { createTRPCRouter, publicProcedure, protectedProcedure } from '../server'

export const authRouter = createTRPCRouter({
  getSession: publicProcedure.query(async ({ ctx }) => {
    const authHeader = ctx.headers.get('authorization')
    
    if (!authHeader) {
      return { user: null }
    }

    const token = authHeader.replace('Bearer ', '')
    const { data: { user }, error } = await ctx.supabase.auth.getUser(token)

    if (error || !user) {
      return { user: null }
    }

    return { user }
  }),

  signOut: protectedProcedure.mutation(async ({ ctx }) => {
    const { error } = await ctx.supabase.auth.signOut()
    
    if (error) {
      throw new Error('Failed to sign out')
    }

    return { success: true }
  }),
})