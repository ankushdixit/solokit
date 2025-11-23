# Docker Development Environment

## Services

- **app**: Next.js application
- **db**: PostgreSQL 16 database

## Architecture

The fullstack_nextjs stack provides a flexible full-stack foundation with:

- **PostgreSQL database** for persistent data storage
- **Prisma ORM** for type-safe database access
- **Flexible API layer** - bring your own (REST, GraphQL, tRPC, etc.)

Unlike saas_t3, this stack does NOT include NextAuth.js by default, giving you flexibility to choose your own authentication solution.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@db:5432/mydb?schema=public` |

## Usage

### Development

```bash
# Start database and application
docker-compose up

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (deletes database data)
docker-compose down -v
```

### Database Commands

```bash
# Run Prisma migrations
docker-compose exec app npx prisma migrate dev

# Open Prisma Studio (database GUI)
docker-compose exec app npx prisma studio

# Generate Prisma client
docker-compose exec app npx prisma generate

# Seed the database
docker-compose exec app npx prisma db seed
```

### Production

```bash
# Build and run production image
docker-compose -f docker-compose.prod.yml up -d
```

## Integration Tests

Integration tests in this stack require the PostgreSQL database:

```bash
# Start database first
docker-compose up db -d

# Wait for database to be ready, then run tests
npm run test:integration
```

The CI workflow automatically sets up a PostgreSQL service for integration tests.

## Comparison with Other Stacks

| Feature | fullstack_nextjs | saas_t3 | dashboard_refine |
|---------|------------------|---------|------------------|
| Database | PostgreSQL | PostgreSQL | None (external API) |
| Auth | Flexible | NextAuth.js | Optional |
| API Layer | Flexible | tRPC | Refine data provider |
| Best For | Custom projects | SaaS apps | Admin dashboards |
