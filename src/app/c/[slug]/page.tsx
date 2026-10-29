import Link from "next/link";
import { notFound } from "next/navigation";
import { readCatalog, readCircuit } from "@/lib/loadCircuit";
import { CircuitWorkspace } from "@/components/editor/CircuitWorkspace";
import { LiveQr } from "@/components/LiveQr";

export async function generateStaticParams() {
  const catalog = await readCatalog();
  return catalog.circuits
    .filter((c) => !c.skipped)
    .map((c) => ({ slug: c.slug }));
}

export default async function CircuitPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const catalog = await readCatalog();
  const entry = catalog.circuits.find((c) => c.slug === slug || c.id === slug);
  if (!entry || entry.skipped) notFound();

  const circuit = await readCircuit(entry.id);
  if (!circuit) notFound();

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between gap-4 border-b border-gray-200 px-4 py-3">
        <div className="min-w-0">
          <Link href="/" className="text-xs text-teal-700 hover:underline">
            ← كل الدوائر
          </Link>
          <h1 className="truncate text-base font-bold text-gray-900">
            {circuit.titleAr || circuit.title}
          </h1>
          <p className="truncate text-[11px] text-gray-500">
            {circuit.sourceFile} · {circuit.page}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <LiveQr path={`/c/${entry.slug}`} size={56} />
        </div>
      </header>
      <CircuitWorkspace circuit={circuit} />
    </div>
  );
}
