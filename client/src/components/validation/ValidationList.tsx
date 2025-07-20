'use client'

import { ValidationCard } from './ValidationCard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Plus, Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import type { Validation } from '@/lib/db/schema'

interface ValidationListProps {
  validations?: Validation[]
  isLoading: boolean
  error?: Error | any
}

export function ValidationList({ validations, isLoading, error }: ValidationListProps) {
  const router = useRouter()

  const handleValidationClick = (validation: Validation) => {
    if (validation.status === 'completed') {
      router.push(`/validation/${validation.id}`)
    }
  }

  const handleCreateNew = () => {
    router.push('/create-validation')
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <p className="text-destructive mb-4">Failed to load validations</p>
            <Button variant="outline" onClick={() => window.location.reload()}>
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Your Validations</CardTitle>
            <CardDescription>
              Manage and track your SaaS idea validations
            </CardDescription>
          </div>
          <Button onClick={handleCreateNew} className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>New Validation</span>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center space-x-2 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Loading validations...</span>
            </div>
          </div>
        ) : !validations || validations.length === 0 ? (
          <div className="text-center py-12">
            <div className="mx-auto w-24 h-24 bg-muted rounded-full flex items-center justify-center mb-4">
              <Plus className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No validations yet</h3>
            <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
              Get started by creating your first SaaS idea validation to receive AI-powered market insights.
            </p>
            <Button onClick={handleCreateNew} size="lg">
              Create Your First Validation
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {validations.map((validation) => (
              <ValidationCard
                key={validation.id}
                validation={validation}
                onClick={() => handleValidationClick(validation)}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}