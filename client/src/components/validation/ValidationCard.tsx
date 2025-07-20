'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Calendar, TrendingUp, Users, MessageSquare } from 'lucide-react'
import type { Validation } from '@/lib/db/schema'

interface ValidationCardProps {
  validation: Validation
  onClick?: () => void
}

export function ValidationCard({ validation, onClick }: ValidationCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'default'
      case 'processing':
        return 'secondary'
      case 'failed':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  const getMarketScoreColor = (score?: string | null) => {
    if (!score) return 'text-muted-foreground'
    const numScore = parseFloat(score)
    if (numScore >= 8) return 'text-green-600'
    if (numScore >= 6) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={onClick}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <CardTitle className="text-lg font-semibold line-clamp-1">
            {validation.title}
          </CardTitle>
          <Badge variant={getStatusColor(validation.status)}>
            {validation.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground line-clamp-2">
          {validation.ideaText}
        </p>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
            <div className="flex items-center space-x-1">
              <Calendar className="h-4 w-4" />
              <span>{formatDate(validation.createdAt!)}</span>
            </div>
            
            {validation.status === 'completed' && validation.marketScore && (
              <div className="flex items-center space-x-1">
                <TrendingUp className="h-4 w-4" />
                <span className={getMarketScoreColor(validation.marketScore)}>
                  Score: {validation.marketScore}/10
                </span>
              </div>
            )}
          </div>
          
          {validation.status === 'completed' && (
            <div className="flex items-center space-x-3 text-xs text-muted-foreground">
              <div className="flex items-center space-x-1">
                <Users className="h-3 w-3" />
                <span>{validation.competitorCount || 0}</span>
              </div>
              <div className="flex items-center space-x-1">
                <MessageSquare className="h-3 w-3" />
                <span>{validation.feedbackCount || 0}</span>
              </div>
            </div>
          )}
        </div>

        {validation.status === 'processing' && (
          <div className="w-full bg-secondary rounded-full h-2">
            <div className="bg-primary h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
          </div>
        )}

        {validation.status === 'completed' && (
          <Button variant="outline" size="sm" className="w-full">
            View Results
          </Button>
        )}
      </CardContent>
    </Card>
  )
}