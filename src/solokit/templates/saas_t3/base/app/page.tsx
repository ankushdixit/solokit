export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-[#2e026d] to-[#15162c] text-white">
      <div className="container flex flex-col items-center justify-center gap-12 px-4 py-16">
        <h1 className="text-5xl font-extrabold tracking-tight sm:text-[5rem]">
          Welcome to <span className="text-[hsl(280,100%,70%)]">T3</span>
        </h1>
        <p className="text-xl text-white/80">
          Your T3 Stack application is ready. Start building!
        </p>
        <div className="text-center text-white/60">
          <p>Read ARCHITECTURE.md to understand the stack patterns.</p>
          <p>Create your PRD at docs/PRD.md to define your features.</p>
        </div>
      </div>
    </main>
  );
}
