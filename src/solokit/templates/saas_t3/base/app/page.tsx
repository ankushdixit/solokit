/**
 * Home Page - Server Component
 *
 * This is a minimal starting point for your T3 application.
 * See ARCHITECTURE.md for patterns on adding features.
 */
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background text-foreground">
      <div className="container flex flex-col items-center justify-center gap-12 px-4 py-16">
        <h1 className="text-5xl font-extrabold tracking-tight sm:text-[5rem]">
          Welcome to <span className="text-blue-500">T3</span>
        </h1>
        <p className="text-xl opacity-80">
          Your T3 Stack application is ready. Start building!
        </p>
        <div className="text-center opacity-60">
          <p>Read ARCHITECTURE.md to understand the stack patterns.</p>
          <p>Create your PRD at docs/PRD.md to define your features.</p>
        </div>
      </div>
    </main>
  );
}
