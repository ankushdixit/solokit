import Link from "next/link";

/**
 * Home Page - Server Component
 *
 * This is a minimal starting point for your application.
 * See ARCHITECTURE.md for patterns on adding features.
 */
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background text-foreground">
      <div className="container flex flex-col items-center justify-center gap-12 px-4 py-16">
        <h1 className="text-5xl font-extrabold tracking-tight sm:text-[5rem]">
          Full-Stack <span className="text-blue-500">Next.js</span>
        </h1>

        <p className="text-center text-xl opacity-80">
          Your project is ready. Start building from your PRD.
        </p>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-8">
          <Link
            href="/api/health"
            className="flex max-w-xs flex-col gap-4 rounded-xl bg-foreground/10 p-4 hover:bg-foreground/20"
          >
            <h3 className="text-2xl font-bold">Health Check →</h3>
            <div className="text-lg">Verify the API is running at /api/health</div>
          </Link>
          <div className="flex max-w-xs flex-col gap-4 rounded-xl bg-foreground/10 p-4">
            <h3 className="text-2xl font-bold">Get Started</h3>
            <div className="text-lg">
              Read <code className="text-blue-700 dark:text-blue-400">ARCHITECTURE.md</code> for patterns
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
