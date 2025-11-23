# Docker Development Environment

## Services

- **app**: Next.js application with tRPC
- **db**: PostgreSQL 16 database

## Architecture

The saas_t3 stack is a full-stack application with:

- **PostgreSQL database** for persistent data storage
- **Prisma ORM** for type-safe database access
- **NextAuth.js** for authentication
- **tRPC** for type-safe API layer

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@db:5432/mydb?schema=public` |
| `NEXTAUTH_SECRET` | NextAuth.js secret key | `your-secret-here` (change in production!) |
| `NEXTAUTH_URL` | Application URL for NextAuth | `http://localhost:3000` |

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

| Feature | saas_t3 | fullstack_nextjs | dashboard_refine |
|---------|---------|------------------|------------------|
| Database | PostgreSQL | PostgreSQL | None (external API) |
| Auth | NextAuth.js | Optional | Optional |
| API Layer | tRPC | Flexible | Refine data provider |
