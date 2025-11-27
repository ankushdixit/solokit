# Docker Development Environment

## Services

- **app**: Next.js application with Refine.dev

## Why No Database?

The dashboard_refine stack is designed for building admin dashboards that connect to **existing external APIs**. Unlike saas_t3 and fullstack_nextjs which manage their own PostgreSQL database, dashboard_refine:

- Uses Refine.dev's data provider abstraction to connect to any backend
- Ships with a placeholder data provider that guides you to configure your backend
- Expects you to configure a real data provider (REST, GraphQL, Supabase, etc.)

If your dashboard needs its own database, consider using the `fullstack_nextjs` or `saas_t3` stack instead.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | External API base URL | `https://api.fake-rest.refine.dev` |

## Usage

### Development

```bash
# Start the development environment
docker-compose up

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

### Production

```bash
# Build and run production image
docker-compose -f docker-compose.prod.yml up -d
```

## Integration Tests

Since dashboard_refine connects to external APIs rather than a local database, integration tests:

- Do NOT require PostgreSQL or any database setup
- Run against your configured data provider
- Are simpler to set up compared to database-backed stacks

To run integration tests:

```bash
npm run test:integration
```

## Switching to a Real Backend

When ready to connect to your real API:

1. Update `NEXT_PUBLIC_API_URL` in your `.env` file
2. Configure your data provider in `lib/refine.tsx`
3. See ARCHITECTURE.md for detailed setup instructions
