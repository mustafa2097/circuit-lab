"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { QrCode } from "@/components/QrCode";

export function CircuitCard({
  title,
  sourceFile,
  page,
  purpose,
  href,
}: {
  title: string;
  sourceFile: string;
  page: string;
  purpose: string;
  href: string;
}) {
  const [url, setUrl] = useState("");

  useEffect(() => {
    setUrl(`${window.location.origin}${href}`);
  }, [href]);

  return (
    <article className="flex flex-col rounded-lg border border-gray-200 bg-white p-4 transition hover:border-teal-600">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold leading-6 text-gray-900">{title}</h2>
          <p className="mt-1 text-[11px] text-gray-500">
            {sourceFile} · {page}
          </p>
        </div>
        {url ? (
          <QrCode value={url} size={72} className="shrink-0 rounded" />
        ) : (
          <div className="h-[72px] w-[72px] shrink-0 rounded bg-gray-100" />
        )}
      </div>
      <p className="mt-3 line-clamp-2 flex-1 text-xs leading-5 text-gray-600">
        {purpose}
      </p>
      <Link
        href={href}
        className="mt-4 inline-flex items-center justify-center rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-black"
      >
        فتح الدائرة
      </Link>
    </article>
  );
}
