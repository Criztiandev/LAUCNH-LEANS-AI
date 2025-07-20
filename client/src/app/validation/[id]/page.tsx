'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { trpc } from '@/lib/trpc/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface ValidationResultsPageProps {
  params: {
    id: string
  }
}

export default function ValidationResultsPage({ params }: ValidationResultsPageProps) {
  return (
    <ProtectedRoute>
      <ValidationResultsContent validationId={params.id} />
    </ProtectedRoute>
  )
}

function ValidationResultsContent({ validationId }: { validationId: string }) {
  const router = useRouter()
  const { data, isLoading, error } = trpc.validations.getById.useQuery({ id: validationId })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex items-center space-x-2 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading validation results...</span>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-destructive mb-4">Failed to load validation results</p>
              <div className="space-x-2">
                <Button variant="outline" onClick={() => router.back()}>
                  Go Back
                </Button>
                <Button onClick={() => window.location.reload()}>
                  Try Again
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const { validation, competitors, feedback, aiAnalysis } = data

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center py-6 space-x-4">
            <Button variant="ghost" size="sm" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
            <div className="flex-1">
              <h1 className="text-3xl font-bold">{validation.title}</h1>
              <div className="flex items-center space-x-4 mt-2">
                <Badge variant={validation.status === 'completed' ? 'default' : 'secondary'}>
                  {validation.status}
                </Badge>
                {validation.marketScore && (
                  <span className="text-sm text-muted-foreground">
                    Market Score: {validation.marketScore}/10
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Idea Description</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">{validation.ideaText}</p>
            </CardContent>
          </Card>

          {validation.status === 'completed' && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Analysis Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">
                        {validation.marketScore}/10
                      </div>
                      <div className="text-sm text-muted-foreground">Market Score</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">
                        {competitors.length}
                      </div>
                      <div className="text-sm text-muted-foreground">Competitors Found</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">
                        {feedback.length}
                      </div>
                      <div className="text-sm text-muted-foreground">Feedback Items</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {aiAnalysis && (
                <Card>
                  <CardHeader>
                    <CardTitle>AI Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {aiAnalysis.executiveSummary && (
                        <div>
                          <h4 className="font-semibold mb-2">Executive Summary</h4>
                          <p className="text-muted-foreground">{aiAnalysis.executiveSummary}</p>
                        </div>
                      )}
                      {aiAnalysis.marketOpportunity && (
                        <div>
                          <h4 className="font-semibold mb-2">Market Opportunity</h4>
                          <p className="text-muted-foreground">{aiAnalysis.marketOpportunity}</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {validation.status === 'processing' && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
                  <h3 className="text-lg font-semibold mb-2">Processing Your Validation</h3>
                  <p className="text-muted-foreground">
                    We're analyzing your idea and gathering market insights. This usually takes a few minutes.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}