# Design Document - launch-lens AI Validation Platform

## Overview

launch-lens AI is architected as a modern full-stack SaaS idea validation platform using Next.js 14 with App Router for the frontend, Supabase for authentication and database, and FastAPI for backend scraping and AI analysis. The system follows a streamlined approach where the frontend handles user interactions and data presentation, while the FastAPI backend manages scraping operations and AI processing asynchronously.

The platform combines automated API-based scraping and headless browser scraping using Patchright from multiple sources (Product Hunt, Reddit, Facebook, Twitter, Instagram, Google Search) with Google AI Studio's Gemini model to provide comprehensive validation reports. These reports include market opportunity analysis, competitive landscape assessment, user feedback sentiment analysis, and exactly 8 strategic recommendations with calculated market scores (1-10 scale).

The architecture prioritizes performance through asynchronous processing, type safety through tRPC, real-time updates via Supabase subscriptions, scalable background processing for data collection and analysis, and comprehensive data export capabilities in CSV and JSON formats. The design ensures data security through Row Level Security (RLS) policies, maintains separation of concerns between user-facing operations and backend processing, and provides responsive mobile-optimized user experiences with comprehensive error handling and recovery mechanisms.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend (Next.js)"
        A[User Interface] --> B[tRPC Client]
        B --> C[Supabase Client]
        A --> D[Real-time Subscriptions]
        A --> E[Export Interface]
    end
    
    subgraph "FastAPI Backend"
        F[tRPC Server] --> G[Supabase Database]
        H[FastAPI Service] --> G
        H --> I[Scraping Orchestrator]
        H --> J[AI Service]
        H --> K[Export Service]
        I --> L[Product Hunt Scraper]
        I --> M[Reddit Scraper]
        I --> N[Google Search Scraper]
        I --> O[Social Media Scrapers]
    end
    
    subgraph "Browser Infrastructure"
        N --> P1[Patchright Browser Pool]
        O --> P2[Patchright Browser Pool]
    end
    
    subgraph "Data Sources"
        L --> S1[Product Hunt API]
        M --> S2[Reddit API]
        N --> S3[Google Search Results]
        O --> S4[Facebook<br/>Twitter<br/>Instagram]
    end
    
    subgraph "External Services"
        J --> T[Google AI Studio]
        P1 --> U[Proxy Services]
        P2 --> U
    end
    
    C --> G
    D --> G
    F --> H
    K --> G
    E --> K
    
    style A fill:#e1f5fe
    style H fill:#f3e5f5
    style G fill:#e8f5e8
    style I fill:#fff3e0
    style N fill:#ff9800,color:#ffffff
    style O fill:#9c27b0,color:#ffffff
```

### Data Flow

1. **User Authentication**: User creates account and authenticates via Supabase Auth
2. **Validation Creation**: User submits validation request (title and idea description) through Next.js frontend
3. **Request Processing**: tRPC server validates input constraints and creates validation record in Supabase with "processing" status
4. **Parallel Job Distribution**: FastAPI creates parallel scraping jobs and dispatches to Redis queues
5. **API-Based Collection**: FastAPI directly handles Product Hunt API and Reddit API scraping
6. **Browser-Based Collection**: FastAPI orchestrates Patchright browser automation for Google Search and social media platforms
7. **Data Aggregation**: All scraping results converge to central processing pipeline
8. **Data Storage**: Scraped competitors and user feedback stored in Supabase with source attribution
9. **AI Analysis**: Gemini AI processes aggregated data to generate comprehensive market analysis
10. **Market Scoring**: System calculates market score (1-10) based on competition density and user sentiment
11. **Completion**: Validation status updated to "completed" with all analysis results
12. **Real-time Updates**: Frontend receives real-time updates via Supabase subscriptions
13. **Results Display**: User views comprehensive validation results through responsive interface
14. **Data Export**: User can export validation data in CSV or JSON format with full user feedback analysis

## Components and Interfaces

### FastAPI Backend Components

#### Core Scraping Components
- **ScrapingOrchestrator**: Manages the complete scraping workflow from validation creation to completion
- **ProductHuntScraper**: 
  - Uses Product Hunt API for structured competitor data
  - Extracts product metrics, user counts, and pricing information
  - Handles API rate limiting and authentication
- **RedditScraper**: 
  - Uses Reddit API (PRAW) for structured discussion data
  - Searches relevant subreddits for keyword-related discussions
  - Extracts user sentiment and pain points from comments

#### Headless Browser Components
- **GoogleSearchScraper**: Uses Patchright for stealth Google search result extraction with anti-detection measures
- **SocialMediaScrapers**: 
  - FacebookScraper for public groups and pages using headless browser automation
  - TwitterScraper for tweet sentiment and trend analysis with stealth measures
  - InstagramScraper for hashtag and content analysis using browser automation
- **HeadlessBrowserService**: Manages Patchright browser pool with session lifecycle and resource cleanup
- **StealthManager**: Implements anti-detection measures across all browser scrapers

#### Core Processing Components
- **ValidationOrchestrator**: Manages the complete validation workflow from creation to completion
- **DataAggregator**: Collects and combines results from all scrapers
- **ProgressTracker**: Tracks real-time progress across all scraping operations
- **ErrorHandler**: Manages scraping failures and continues with available sources

### AI and Analysis Components
- **AIService**: Integrates with Google AI Studio Gemini model for comprehensive analysis generation
- **MarketOpportunityAnalyzer**: Generates market opportunity analysis based on scraped data
- **CompetitiveAnalyzer**: Provides competitive landscape assessment with specific insights
- **StrategicRecommendationGenerator**: Creates exactly 8 strategic recommendations including MVP features, pricing, and GTM strategy
- **RiskAssessmentAnalyzer**: Identifies potential challenges and mitigation strategies
- **MarketScoreCalculator**: Calculates market score (1-10) based on competition density and sentiment

### Data Management and Export
- **SupabaseService**: Database operations and validation status management
- **DataCleaner**: Deduplication and data quality processing with source attribution
- **ExportService**: Generates CSV and JSON exports as specified in requirements
- **FileGenerator**: Creates downloadable files with descriptive filenames including validation title and export date

### API Interfaces

#### FastAPI Endpoints
```python
# Orchestration Operations
POST /api/process-validation           # Trigger validation processing
GET /api/validation/{id}/progress      # Get real-time progress
POST /api/validation/{id}/retry        # Retry failed validation

# Export Operations
GET /api/export/csv/{validation_id}    # Generate CSV export with competitor data
GET /api/export/json/{validation_id}   # Generate JSON export with complete data

# Background Tasks
process_validation()                   # Complete validation processing
aggregate_scraping_results()          # Combine results from all sources
analyze_with_ai()                     # Process data with Gemini AI
cleanup_browser_sessions()            # Browser resource cleanup
```

#### tRPC Procedures
```typescript
// Authentication
auth.login()                           # User authentication
auth.signup()                          # User registration
auth.logout()                          # Session termination

// Validations
validations.create()                   # Create new validation with parallel processing
validations.getAll()                   # Get user's validations with progress indicators
validations.getById()                  # Get specific validation with user feedback analysis
validations.getProgress()              # Get real-time progress
validations.retry()                    # Retry failed validation components

// Export Operations
export.generateCSV()                   # Trigger CSV export with user sentiment data
export.generateJSON()                  # Trigger JSON export with complete analysis
export.getExportStatus()               # Check export generation status
```
// Worker Communication (Redis/HTTP)
POST /worker/google-search/scrape      // Google search scraping job
POST /worker/app-stores/scrape         // App store scraping job  
POST /worker/review-sites/scrape       // Review sites scraping job
POST /worker/reddit-discussions/scrape // Reddit discussions scraping job

// Worker Status
GET /worker/{type}/health              // Individual worker health check
GET /worker/{type}/metrics             // Worker performance metrics
```

#### tRPC Procedures
```typescript
// Authentication
auth.login()                           # User authentication
auth.signup()                          # User registration
auth.logout()                          # Session termination

// Validations
validations.create()                   # Create new validation with parallel processing
validations.getAll()                   # Get user's validations with progress indicators
validations.getById()                  # Get specific validation with user feedback analysis
validations.getProgress()              # Get real-time worker progress
validations.retry()                    # Retry failed validation components

// Export Operations
export.generateCSV()                   # Trigger CSV export with user sentiment data
export.generateJSON()                  # Trigger JSON export with complete analysis
export.getExportStatus()               # Check export generation status
```

## Data Models

### Database Schema (Supabase/PostgreSQL)

#### Core Tables
```sql
-- User validations
validations {
  id: UUID (PK)
  user_id: UUID (FK to auth.users)
  title: TEXT (1-255 chars)
  idea_text: TEXT (10-1000 chars)
  status: TEXT ('processing'|'completed'|'failed')
  market_score: INTEGER (1-10)
  created_at: TIMESTAMP
  updated_at: TIMESTAMP
}

-- Competitor data
competitors {
  id: UUID (PK)
  validation_id: UUID (FK)
  name: TEXT
  description: TEXT
  website: TEXT
  estimated_users: INTEGER
  estimated_revenue: TEXT
  pricing_model: TEXT
  source: TEXT ('product_hunt'|'google_search'|'reddit'|'facebook'|'twitter'|'instagram')
  source_url: TEXT
  confidence_score: DECIMAL(3,2)
  scraping_method: TEXT ('api'|'browser')
  created_at: TIMESTAMP
}

-- User feedback and sentiment
user_feedback {
  id: UUID (PK)
  validation_id: UUID (FK)
  feedback_text: TEXT
  sentiment: TEXT ('positive'|'negative'|'neutral')
  sentiment_score: DECIMAL(3,2)
  source: TEXT ('reddit'|'facebook'|'twitter'|'instagram')
  source_url: TEXT
  author_info: JSONB
  scraping_method: TEXT ('api'|'browser')
  created_at: TIMESTAMP
}

-- AI-generated analysis
ai_analysis {
  id: UUID (PK)
  validation_id: UUID (FK)
  market_opportunity: TEXT
  competitive_analysis: TEXT
  strategic_recommendations: TEXT -- Exactly 8 recommendations
  risk_assessment: TEXT
  gtm_strategy: TEXT
  feature_priorities: TEXT
  executive_summary: TEXT
  created_at: TIMESTAMP
}

-- Export tracking
exports {
  id: UUID (PK)
  validation_id: UUID (FK)
  user_id: UUID (FK)
  export_type: TEXT ('csv'|'json')
  file_path: TEXT
  status: TEXT ('generating'|'completed'|'failed')
  created_at: TIMESTAMP
}
```

### TypeScript Interfaces

#### Data Types
```typescript
interface Validation {
  id: string;
  userId: string;
  title: string;
  ideaText: string;
  status: 'processing' | 'completed' | 'failed';
  marketScore?: number;
  scrapingMetadata?: {
    sourcesScraped: string[];
    browserSessionsUsed: number;
    successRate: number;
    processingTime: number;
  };
  createdAt: string;
  updatedAt: string;
}

interface Competitor {
  id: string;
  validationId: string;
  name: string;
  description?: string;
  website?: string;
  estimatedUsers?: number;
  estimatedRevenue?: string;
  pricingModel?: string;
  source: 'product_hunt' | 'google_search' | 'reddit' | 'facebook' | 'twitter' | 'instagram';
  sourceUrl?: string;
  confidenceScore: number;
  scrapingMethod: 'api' | 'browser';
  createdAt: string;
}

interface Feedback {
  id: string;
  validationId: string;
  text: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentimentScore: number;
  source: 'reddit' | 'facebook' | 'twitter' | 'instagram';
  sourceUrl?: string;
  authorInfo?: any;
  scrapingMethod: 'api' | 'browser';
  createdAt: string;
}

interface AIAnalysis {
  id: string;
  validationId: string;
  marketOpportunity: string;
  competitiveAnalysis: string;
  strategicRecommendations: string;
  riskAssessment: string;
  gtmStrategy: string;
  featurePriorities: string;
  executiveSummary: string;
  createdAt: string;
}

interface ExportData {
  id: string;
  validationId: string;
  userId: string;
  exportType: 'csv' | 'json';
  filePath: string;
  status: 'generating' | 'completed' | 'failed';
  createdAt: string;
}
```

## Headless Browser Infrastructure

### Browser Pool Management

#### Architecture Components
- **Browser Pool**: Maintains 3-5 concurrent Patchright browser instances for parallel scraping
- **Session Lifecycle**: Automatic browser instance rotation every 5-10 requests to avoid detection
- **Resource Management**: Memory monitoring and cleanup to prevent resource leaks
- **Proxy Integration**: Residential proxy rotation for improved success rates

#### Stealth Measures
- **Patchright Configuration**: Enhanced stealth plugin configuration to avoid detection signatures
- **Human Behavior Simulation**: Random delays (2-8 seconds), mouse movements, and scroll patterns
- **Fingerprint Randomization**: Dynamic viewport sizes, user agents, and browser settings
- **Captcha Handling**: Detection and logging of captcha challenges with graceful fallbacks

#### Performance Optimization
- **Intelligent Queuing**: Priority-based scraping queue with retry mechanisms
- **Success Rate Monitoring**: Track and adapt to platform-specific success rates
- **Fallback Strategies**: API-first approach with browser scraping as fallback when possible

### Design Rationale
The headless browser infrastructure provides reliable data extraction while maintaining stealth capabilities and respecting platform rate limits. The pool-based approach ensures efficient resource utilization while the stealth measures minimize detection risks.

## Error Handling

### Enhanced Error Management Strategy

The system implements multi-layered error handling with specific focus on browser automation challenges:

#### Orchestrator-Level Error Handling
- **Worker Failures**: Automatic job reassignment to backup workers
- **Partial Results**: Completion with available data when some workers fail
- **Timeout Handling**: Maximum processing time limits with graceful degradation
- **Data Quality**: Validation and cleanup of worker results

### User Experience During Errors
- **Real-time Updates**: Progress indicators showing which sources are processing/completed/failed
- **Partial Results**: Display available results even if some sources fail
- **Retry Options**: Allow users to retry failed components
- **Transparent Communication**: Clear error messages explaining what data might be missingText: string;
  status: 'processing' | 'completed' | 'failed';
  marketScore?: number;
  scrapingMetadata?: {
    sourcesScraped: string[];
    browserSessionsUsed: number;
    successRate: number;
    processingTime: number;
  };
  createdAt: string;
  updatedAt: string;
}

interface Competitor {
  id: string;
  validationId: string;
  name: string;
  description?: string;
  website?: string;
  estimatedUsers?: number;
  estimatedRevenue?: string;
  pricingModel?: string;
  source: string;
  sourceUrl?: string;
  confidenceScore: number;
  scrapingMethod: 'api' | 'browser';
  createdAt: string;
}

interface Feedback {
  id: string;
  validationId: string;
  text: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentimentScore: number;
  source: string;
  sourceUrl?: string;
  authorInfo?: any;
  scrapingMethod: 'api' | 'browser';
  createdAt: string;
}

interface AIAnalysis {
  id: string;
  validationId: string;
  marketOpportunity: string;
  competitiveAnalysis: string;
  strategicRecommendations: string;
  riskAssessment: string;
  gtmStrategy: string;
  featurePriorities: string;
  executiveSummary: string;
  createdAt: string;
}

interface ExportData {
  id: string;
  validationId: string;
  userId: string;
  exportType: 'csv' | 'json';
  filePath: string;
  status: 'generating' | 'completed' | 'failed';
  createdAt: string;
}
```

## Headless Browser Infrastructure

### Browser Pool Management

#### Architecture Components
- **Browser Pool**: Maintains 3-5 concurrent Patchright browser instances for parallel scraping
- **Session Lifecycle**: Automatic browser instance rotation every 5-10 requests to avoid detection
- **Resource Management**: Memory monitoring and cleanup to prevent resource leaks
- **Proxy Integration**: Residential proxy rotation for improved success rates

#### Stealth Measures
- **Patchright Configuration**: Enhanced stealth plugin configuration to avoid detection signatures
- **Human Behavior Simulation**: Random delays (2-8 seconds), mouse movements, and scroll patterns
- **Fingerprint Randomization**: Dynamic viewport sizes, user agents, and browser settings
- **Captcha Handling**: Detection and logging of captcha challenges with graceful fallbacks

#### Performance Optimization
- **Intelligent Queuing**: Priority-based scraping queue with retry mechanisms
- **Success Rate Monitoring**: Track and adapt to platform-specific success rates
- **Fallback Strategies**: API-first approach with browser scraping as fallback when possible

### Design Rationale
The headless browser infrastructure provides reliable data extraction while maintaining stealth capabilities and respecting platform rate limits. The pool-based approach ensures efficient resource utilization while the stealth measures minimize detection risks.

## Error Handling

### Enhanced Error Management Strategy

The system implements multi-layered error handling with specific focus on browser automation challenges:

#### Frontend Error Handling
- **React Error Boundaries**: Catch component-level errors and display fallback UI
- **Form Validation**: Real-time validation with user-friendly error messages
- **Network Error Recovery**: Retry mechanisms for failed API calls with exponential backoff
- **Loading States**: Clear indicators during processing with timeout handling

#### Backend Error Handling
- **Browser Session Management**: Automatic recovery from browser crashes and timeouts
- **Scraper Resilience**: Individual scraper failures don't halt entire validation process
- **Captcha Detection**: Graceful handling of anti-bot challenges with logging
- **Rate Limiting**: Intelligent backoff strategies for platform-specific limits
- **Data Quality**: Enhanced validation and sanitization of browser-scraped data
- **Status Management**: Detailed validation status updates with error context

#### Design Rationale
This approach ensures the platform remains functional even when browser automation faces challenges, providing users with clear feedback and maintaining data integrity while maximizing scraping success rates.

## Security and Privacy

### Enhanced Data Protection Strategy

#### Authentication and Authorization
- **Supabase Auth**: Secure user authentication with session management
- **Row Level Security (RLS)**: Database-level access control ensuring users only see their data
- **Protected Routes**: Frontend route protection for authenticated users only
- **Export Authorization**: Secure file generation with user ownership validation

#### Data Security
- **Input Validation**: Strict validation of user inputs (title 1-255 chars, idea 10-1000 chars)
- **Data Sanitization**: Enhanced cleaning and validation of browser-scraped data
- **Secure API Communication**: HTTPS for all external API calls
- **Rate Limiting**: Prevent abuse through API endpoint rate limiting
- **File Security**: Temporary export file storage with automatic cleanup

#### Browser Security
- **Sandboxed Execution**: Isolated browser instances with restricted permissions
- **Proxy Security**: Secure proxy rotation with encrypted connections
- **Session Isolation**: No cross-validation data leakage between browser sessions

#### Design Rationale
Security is implemented at multiple layers including browser automation security to protect user data and ensure compliance with privacy standards while maintaining system performance.

## Performance and Scalability

### Enhanced Real-time Updates and Responsiveness

#### Real-time Architecture
- **Supabase Subscriptions**: Real-time validation status updates without polling
- **Optimistic Updates**: Immediate UI feedback for better user experience
- **Background Processing**: Asynchronous scraping with browser pool management prevents UI blocking
- **Progress Tracking**: Granular progress updates during multi-source scraping

#### Browser Performance Optimization
- **Resource Monitoring**: Memory and CPU usage tracking for browser instances
- **Intelligent Scaling**: Dynamic browser pool sizing based on demand
- **Cache Management**: Browser cache optimization for improved performance
- **Concurrent Processing**: Parallel scraping with managed resource allocation

#### Mobile Optimization
- **Responsive Design**: Tailwind CSS for mobile-first responsive layouts
- **Touch-friendly UI**: Optimized interactions for mobile devices
- **Performance Budgets**: 3-second load time targets for cached content
- **Export Optimization**: Mobile-friendly export interfaces

#### Design Rationale
The enhanced real-time architecture with browser pool management ensures users receive immediate feedback on validation progress while maintaining optimal resource utilization and consistent experience across devices.

## Data Export System

### Comprehensive Export Functionality

#### Export Architecture
- **Export Service**: Dedicated service for generating CSV and JSON exports with proper authentication
- **File Generation**: Structured data formatting with validation metadata and timestamps
- **Download Management**: Secure file serving with automatic cleanup
- **Format Optimization**: Platform-specific formatting for CSV compatibility and JSON structure

#### Export Data Structure
- **CSV Format**: Competitor data with headers: Name, Description, Website, Estimated Users, Revenue, Pricing Model, Source, Confidence Score, Date Added
- **JSON Format**: Complete validation data including competitors, feedback, AI analysis, and processing metadata
- **Metadata Inclusion**: Export timestamp, validation details, and data source attribution

#### Security and Performance
- **Access Control**: User-specific export generation with ownership validation
- **File Security**: Temporary storage with automatic cleanup after download
- **Rate Limiting**: Export generation limits to prevent abuse
- **Progress Tracking**: Real-time export generation status updates

#### Design Rationale
The export system provides users with portable data formats for external analysis while maintaining security and performance standards.

## AI Analysis Integration

### Enhanced Market Intelligence

#### AI Processing Pipeline
- **Data Aggregation**: Combine scraped data from all sources including browser automation results
- **Market Scoring**: Calculate 1-10 market score based on competition density, sentiment, and data quality
- **Strategic Insights**: Generate 8 specific recommendations including MVP features, pricing, and GTM strategy
- **Quality Assessment**: Enhanced analysis based on scraping method and confidence scores

#### Analysis Components
- **Market Opportunity**: Assess market size and potential based on enhanced competitor analysis
- **Competitive Landscape**: Detailed competitor analysis with browser-extracted positioning insights
- **Risk Assessment**: Identify potential challenges including data reliability considerations
- **Feature Prioritization**: Recommend MVP features based on comprehensive market gaps analysis

#### Design Rationale
The enhanced AI integration transforms browser-scraped data into actionable business insights, providing entrepreneurs with comprehensive market intelligence while accounting for data quality and source reliability.

## Dashboard and Validation Management

### Enhanced User Dashboard Design

#### Dashboard Components
- **ValidationList**: Displays all user validations with scraping method indicators and processing details
- **ValidationCard**: Shows title, status, market score, data sources, and creation date
- **Progress Indicators**: Real-time status updates with browser automation progress and estimated completion time
- **Export Interface**: Integrated CSV and JSON export functionality with download management
- **Empty State**: Call-to-action for users with no validations to create their first validation

#### Validation Results Interface
- **Executive Summary**: Prominently displays AI-generated summary, market score, and data quality indicators
- **Competitor Table**: Enhanced sortable display with scraping method, confidence scores, and export options
- **Sentiment Analysis**: Visual representation of feedback with source attribution and reliability indicators
- **AI Analysis Sections**: Organized presentation with enhanced insights based on comprehensive data collection
- **Export Controls**: Integrated CSV and JSON export buttons with progress indicators

#### Design Rationale
The enhanced dashboard provides comprehensive validation management with data export capabilities while presenting complex browser-scraped data in an accessible, actionable format that supports informed decision-making.

## Testing Strategy

### Enhanced Testing Approach

#### Frontend Testing
- **Unit Tests**: Component testing with Jest and React Testing Library including export functionality
- **Integration Tests**: tRPC client-server communication testing with export endpoints
- **E2E Tests**: Critical user flows using Playwright including export workflows
- **Responsive Testing**: Cross-device and cross-browser compatibility with export interfaces

#### Backend Testing
- **Unit Tests**: Individual scraper and service function testing with browser automation mocking
- **Integration Tests**: FastAPI endpoint testing including export endpoints with test client
- **Browser Automation Testing**: Patchright browser testing with mock websites and anti-bot scenarios
- **Load Testing**: Concurrent scraping performance validation with browser pool management
- **Export Testing**: File generation and download functionality testing

#### Design Rationale
The enhanced testing strategy ensures reliability across all system components including browser automation and export functionality while maintaining development velocity through comprehensive automated testing pipelines.

