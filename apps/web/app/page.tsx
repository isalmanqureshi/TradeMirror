export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col justify-center px-6 py-20">
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-400">TradeMirror</p>
      <h1 className="mt-4 text-4xl font-semibold leading-tight text-white md:text-6xl">
        Your trading history, journals, and market context — in one intelligent copilot.
      </h1>
      <p className="mt-6 max-w-2xl text-lg text-slate-300">
        This is the initial production-oriented foundation for the TradeMirror RAG assistant.
        Analytics and strategy modules are intentionally deferred.
      </p>
    </main>
  );
}
