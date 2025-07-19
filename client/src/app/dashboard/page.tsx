'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { useAuth } from '@/components/providers/AuthProvider'
import { trpc } from '@/lib/trpc/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  )
}

function DashboardContent() {
  const { user, signOut } = useAuth()
  const { data: validations, isLoading } = trpc.validations.getAll.useQuery()

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-muted-foreground">
                Welcome, {user?.user_metadata?.first_name || user?.email}
              </span>
              <Button variant="outline" onClick={signOut}>
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <Card>
            <CardHeader>
              <CardTitle>Your Validations</CardTitle>
              <CardDescription>
                Manage and track your SaaS idea validations
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <p className="text-muted-foreground">Loading validations...</p>
              ) : validations?.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">No validations yet</p>
                  <Button>Create Your First Validation</Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {validations?.map((validation) => (
                    <Card key={validation.id}>
                      <CardContent className="pt-6">
                        <div className="space-y-2">
                          <h3 className="font-medium">{validation.title}</h3>
                          <p className="text-sm text-muted-foreground">{validation.ideaText}</p>
                          <div className="flex items-center space-x-4">
                            <Badge 
                              variant={
                                validation.status === 'completed' ? 'default' :
                                validation.status === 'processing' ? 'secondary' :
                                'destructive'
                              }
                            >
                              {validation.status}
                            </Badge>
                            {validation.marketScore && (
                              <span className="text-sm text-muted-foreground">
                                Market Score: {validation.marketScore}/10
                              </span>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}