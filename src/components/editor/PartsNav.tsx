"use client";

import { partMeta } from "@/lib/parts";
import type { CircuitComponent } from "@/lib/types";

export function PartsNav({
  parts,
  highlightedId,
  onPlace,
}: {
  parts: CircuitComponent[];
  highlightedId?: string | null;
  onPlace: (partId: string) => void;
}) {
  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="flex items-center justify-between gap-3 px-3 py-2">
        <div className="text-xs font-semibold text-gray-600">قطع الدائرة</div>
        <div className="text-[11px] text-gray-400">
          اضغط على قطعة لتنزل إلى مكان الربط
          {parts.length > 0 ? ` · متبقي ${parts.length}` : " · اكتملت القطع"}
        </div>
      </div>
      <div className="flex gap-2 overflow-x-auto px-3 pb-3">
        {parts.length === 0 ? (
          <div className="rounded-md border border-dashed border-gray-200 px-3 py-2 text-xs text-gray-400">
            كل القطع نزلت على اللوحة
          </div>
        ) : (
          parts.map((p) => {
            const meta = partMeta(p.type);
            const active = highlightedId === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => onPlace(p.id)}
                className={
                  active
                    ? "min-w-[112px] shrink-0 rounded-md border-2 border-teal-600 bg-teal-50 px-3 py-2 text-right shadow-sm"
                    : "min-w-[112px] shrink-0 rounded-md border border-gray-300 bg-white px-3 py-2 text-right hover:border-gray-900 hover:bg-gray-50"
                }
                style={{ borderTopWidth: 3, borderTopColor: meta.color }}
                title={`إنزال ${p.label} إلى اللوحة`}
              >
                <div className="text-[11px] font-semibold text-gray-500">
                  {meta.symbol}
                </div>
                <div className="text-sm font-semibold text-gray-900">{p.label}</div>
                <div className="mt-0.5 text-[10px] text-gray-400">{meta.titleAr}</div>
              </button>
            );
          })
        )}
      </div>
    </nav>
  );
}
