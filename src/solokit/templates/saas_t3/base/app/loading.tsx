export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="space-y-4 text-center">
        <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-foreground/30 border-t-foreground"></div>
        <p className="text-sm text-foreground/70">Loading...</p>
      </div>
    </div>
  );
}
