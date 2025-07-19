import { initTRPC, TRPCError } from '@trpc/server'
import { supabase } from '@/lib/supabase'
import { db } from '@/lib/db'
import superjson from 'superjson'

export const createTRPCContext = async (opts: { headers: Headers }) => {
  return {
    db,
    supabase,
    headers: opts.headers,
  }
}

const t = initTRPC.context<typeof createTRPCContext>().create({
  transformer: superjson,
})

export const createTRPCRouter = t.router
export const publicProcedure = t.procedure

// Auth middleware
const enforceUserIsAuthed = t.middleware(async ({ ctx, next }) => {
  const authHeader = ctx.headers.get('authorization')
  
  if (!authHeader) {
    throw new TRPCError({ code: 'UNAUTHORIZED' })
  }

  const token = authHeader.replace('Bearer ', '')
  const { data: { user }, error } = await ctx.supabase.auth.getUser(token)

  if (error || !user) {
    throw new TRPCError({ code: 'UNAUTHORIZED' })
  }

  return next({
    ctx: {
      ...ctx,
      user,
    },
  })
})

export const protectedProcedure = t.procedure.use(enforceUserIsAuthed)