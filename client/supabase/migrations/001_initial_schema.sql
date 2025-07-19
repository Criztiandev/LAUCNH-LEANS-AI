-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create profiles table (extends Supabase Auth)
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  first_name TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create validations table
CREATE TABLE validations (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL CHECK (LENGTH(title) >= 1 AND LENGTH(title) <= 255),
  idea_text TEXT NOT NULL CHECK (LENGTH(idea_text) >= 10 AND LENGTH(idea_text) <= 1000),
  market_score DECIMAL(3,1) CHECK (market_score >= 1.0 AND market_score <= 10.0),
  status TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  competitor_count INTEGER DEFAULT 0,
  feedback_count INTEGER DEFAULT 0,
  sources_scraped JSONB DEFAULT '[]'::jsonb
);

-- Create competitors table
CREATE TABLE competitors (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  validation_id UUID REFERENCES validations(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  website TEXT,
  estimated_users INTEGER,
  estimated_revenue TEXT,
  pricing_model TEXT,
  source TEXT NOT NULL,
  source_url TEXT,
  confidence_score DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create feedback table
CREATE TABLE feedback (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  validation_id UUID REFERENCES validations(id) ON DELETE CASCADE NOT NULL,
  text TEXT NOT NULL,
  sentiment TEXT NOT NULL CHECK (sentiment IN ('positive', 'negative', 'neutral')),
  sentiment_score DECIMAL(3,2) DEFAULT 0.0 CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
  source TEXT NOT NULL,
  source_url TEXT,
  author_info JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create ai_analysis table
CREATE TABLE ai_analysis (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  validation_id UUID REFERENCES validations(id) ON DELETE CASCADE NOT NULL,
  market_opportunity TEXT,
  competitive_analysis TEXT,
  strategic_recommendations TEXT,
  risk_assessment TEXT,
  gtm_strategy TEXT,
  feature_priorities TEXT,
  executive_summary TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE validations ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitors ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_analysis ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

-- RLS Policies for validations
CREATE POLICY "Users can view own validations" ON validations
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own validations" ON validations
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own validations" ON validations
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Service role can update all validations" ON validations
  FOR UPDATE USING (auth.jwt() ->> 'role' = 'service_role');

-- RLS Policies for competitors
CREATE POLICY "Users can view competitors for own validations" ON competitors
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM validations 
      WHERE validations.id = competitors.validation_id 
      AND validations.user_id = auth.uid()
    )
  );

CREATE POLICY "Service role can insert competitors" ON competitors
  FOR INSERT WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- RLS Policies for feedback
CREATE POLICY "Users can view feedback for own validations" ON feedback
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM validations 
      WHERE validations.id = feedback.validation_id 
      AND validations.user_id = auth.uid()
    )
  );

CREATE POLICY "Service role can insert feedback" ON feedback
  FOR INSERT WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- RLS Policies for ai_analysis
CREATE POLICY "Users can view ai_analysis for own validations" ON ai_analysis
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM validations 
      WHERE validations.id = ai_analysis.validation_id 
      AND validations.user_id = auth.uid()
    )
  );

CREATE POLICY "Service role can insert ai_analysis" ON ai_analysis
  FOR INSERT WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- Create indexes for performance
CREATE INDEX idx_validations_user_id ON validations(user_id);
CREATE INDEX idx_validations_status ON validations(status);
CREATE INDEX idx_competitors_validation_id ON competitors(validation_id);
CREATE INDEX idx_feedback_validation_id ON feedback(validation_id);
CREATE INDEX idx_ai_analysis_validation_id ON ai_analysis(validation_id);

-- Function to automatically create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, first_name)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'first_name');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on user signup
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at on profiles
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();