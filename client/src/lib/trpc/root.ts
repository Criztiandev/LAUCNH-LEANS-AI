import { createTRPCRouter } from './server'
import { authRouter } from './routers/auth'
import { validationsRouter } from './routers/validations'

export const appRouter = createTRPCRouter({
  auth: authRouter,
  validations: validationsRouter,
})

export type AppRouter = typeof appRouter