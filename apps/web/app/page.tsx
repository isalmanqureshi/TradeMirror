import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-6 px-6 text-center">
      <h1 className="text-4xl font-bold tracking-tight">TradeMirror</h1>
      <p className="text-lg text-slate-600">
        Monorepo scaffold is ready. Start building the web app, API, and shared packages.
      </p>
      <div className="flex gap-3">
        <Button>Get Started</Button>
        <Button variant="outline">Read Docs</Button>
      </div>
    </main>
  );
}
