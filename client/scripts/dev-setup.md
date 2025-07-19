# Local Development Setup

## Prerequisites
- Docker Desktop installed and running
- Node.js 18+ installed

## Getting Started

### 1. Start Supabase Local Development
```bash
npx supabase start
```

This will start all Supabase services locally:
- **API URL**: http://127.0.0.1:54321
- **Studio URL**: http://127.0.0.1:54323 (Database management UI)
- **DB URL**: postgresql://postgres:postgres@127.0.0.1:54322/postgres
- **Inbucket URL**: http://127.0.0.1:54324 (Email testing)

### 2. Start Next.js Development Server
```bash
npm run dev
```

The app will be available at http://localhost:3000

### 3. Access Supabase Studio
Visit http://127.0.0.1:54323 to:
- View database tables
- Run SQL queries
- Manage authentication
- View logs

## Environment Variables
The `.env.local` file is already configured for local development:
- Supabase URL: http://127.0.0.1:54321
- Database URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres

## Database Management

### Reset Database
```bash
npx supabase db reset
```

### Generate Migration
```bash
npx supabase db diff --file migration_name
```

### Apply Migrations
```bash
npx supabase db push
```

## Testing

### Run Tests
```bash
npm run test
```

### Run Tests in Watch Mode
```bash
npm run test:watch
```

## Stopping Services

### Stop Supabase
```bash
npx supabase stop
```

### Stop Next.js
Press `Ctrl+C` in the terminal running the dev server

## Useful Commands

### View Supabase Status
```bash
npx supabase status
```

### View Supabase Logs
```bash
npx supabase logs
```

### Generate Types from Database
```bash
npx supabase gen types typescript --local > src/types/database.types.ts
```