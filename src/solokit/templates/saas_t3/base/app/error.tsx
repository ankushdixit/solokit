"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-4 rounded-xl border bg-foreground/5 p-6">
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold text-foreground">Something went wrong!</h2>
          <p className="text-sm text-foreground/70">{error.message || "An unexpected error occurred"}</p>
        </div>
        <button
          onClick={reset}
          className="w-full rounded-lg bg-foreground/10 px-4 py-2 font-semibold text-foreground transition hover:bg-foreground/20"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
