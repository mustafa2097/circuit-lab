import { readCatalog } from "@/lib/loadCircuit";
import { CircuitCard } from "@/components/CircuitCard";

export default async function HomePage() {
  const catalog = await readCatalog();
  const active = catalog.circuits.filter((c) => !c.skipped);

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-8 border-b border-gray-200 pb-6">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          مختبر دوائر PLC
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-7 text-gray-600">
          فكّك الدائرة، اربط القطع كما في الملزمة، ثم شغّل المحاكاة. امسح رمز QR
          لفتح الدائرة مباشرة.
        </p>
        <div className="mt-3 text-xs text-gray-500">عدد الدوائر: {active.length}</div>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {active.map((c) => (
          <CircuitCard
            key={c.id}
            title={c.titleAr || c.title}
            sourceFile={c.sourceFile}
            page={c.page}
            purpose={c.purpose}
            href={`/c/${c.slug}`}
          />
        ))}
      </section>
    </main>
  );
}
