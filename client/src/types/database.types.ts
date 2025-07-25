// Database types for Supabase
export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string
          first_name: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          first_name?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          first_name?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      validations: {
        Row: {
          id: string
          user_id: string
          title: string
          idea_text: string
          market_score: number | null
          status: 'processing' | 'completed' | 'failed'
          created_at: string
          completed_at: string | null
          competitor_count: number
          feedback_count: number
          sources_scraped: Json
        }
        Insert: {
          id?: string
          user_id: string
          title: string
          idea_text: string
          market_score?: number | null
          status?: 'processing' | 'completed' | 'failed'
          created_at?: string
          completed_at?: string | null
          competitor_count?: number
          feedback_count?: number
          sources_scraped?: Json
        }
        Update: {
          id?: string
          user_id?: string
          title?: string
          idea_text?: string
          market_score?: number | null
          status?: 'processing' | 'completed' | 'failed'
          created_at?: string
          completed_at?: string | null
          competitor_count?: number
          feedback_count?: number
          sources_scraped?: Json
        }
        Relationships: []
      }
    }
    Views: Record<string, never>
    Functions: Record<string, never>
    Enums: Record<string, never>
    CompositeTypes: Record<string, never>
  }
}