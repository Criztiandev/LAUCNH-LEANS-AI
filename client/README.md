# RealValidator AI

An AI-powered SaaS idea validation platform built with Next.js, Supabase, and shadcn/ui.

## Features

- 🔐 **Authentication**: Secure user authentication with Supabase Auth
- 💾 **Database**: PostgreSQL with Row Level Security (RLS)
- 🎨 **UI Components**: Modern UI with shadcn/ui and Tailwind CSS
- 🔄 **API**: Type-safe APIs with tRPC
- 🧪 **Testing**: Unit and integration tests with Vitest
- 🐳 **Local Development**: Full local development environment with Supabase

## Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript
- **Backend**: tRPC, Supabase
- **Database**: PostgreSQL with Drizzle ORM
- **UI**: shadcn/ui, Tailwind CSS
- **Testing**: Vitest, Testing Library
- **Development**: Supabase CLI, Docker

## Getting Started

### Prerequisites

- Node.js 18+
- Docker Desktop
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd realvalidator-ai
```

2. Install dependencies:
```bash
npm install
```

3. Start Supabase local development:
```bash
npm run db:start
```

4. Start the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Quick Start (All Services)

```bash
npm run dev:full
```

This command starts both Supabase and the Next.js development server.

## Development

### Database Management

- **Start Supabase**: `npm run db:start`
- **Stop Supabase**: `npm run db:stop`
- **Reset Database**: `npm run db:reset`
- **View Status**: `npm run db:status`
- **Open Studio**: `npm run db:studio`
- **Generate Types**: `npm run db:types`

### Testing

- **Run Tests**: `npm test`
- **Run Tests (CI)**: `npm run test:run`
- **Test UI**: `npm run test:ui`

### Building

```bash
npm run build
npm start
```

## Project Structure

```
realvalidator-ai/
├── src/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # React components
│   │   ├── ui/             # shadcn/ui components
│   │   ├── auth/           # Authentication components
│   │   └── providers/      # Context providers
│   ├── lib/                # Utility libraries
│   │   ├── db/             # Database schema and connection
│   │   ├── trpc/           # tRPC setup and routers
│   │   └── utils.ts        # Utility functions
│   ├── test/               # Test files
│   └── types/              # TypeScript type definitions
├── supabase/
│   ├── migrations/         # Database migrations
│   └── config.toml         # Supabase configuration
└── scripts/                # Development scripts
```

## Environment Variables

The project uses `.env.local` for local development with Supabase local instance:

```env
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=<local-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<local-service-role-key>
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

## Database Schema

The application includes the following main tables:

- **profiles**: User profile information
- **validations**: SaaS idea validation records
- **competitors**: Competitor analysis data
- **feedback**: User feedback and sentiment analysis
- **ai_analysis**: AI-generated insights and recommendations

## API Routes

- `/api/trpc/[trpc]`: tRPC API endpoints

## Authentication

The app uses Supabase Auth with:
- Email/password authentication
- Row Level Security (RLS) policies
- Automatic profile creation on signup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.