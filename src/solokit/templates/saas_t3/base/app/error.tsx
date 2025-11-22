"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md space-y-4 rounded-xl bg-white/10 p-6">
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold">Something went wrong!</h2>
          <p className="text-sm text-white/70">{error.message || "An unexpected error occurred"}</p>
        </div>
        <button
          onClick={reset}
          className="w-full rounded-lg bg-white/20 px-4 py-2 font-semibold transition hover:bg-white/30"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
