"use client";

import { useEffect, useState } from "react";
import { QrCode } from "@/components/QrCode";

export function LiveQr({ path, size = 56 }: { path: string; size?: number }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    setUrl(`${window.location.origin}${path}`);
  }, [path]);
  if (!url) return <div style={{ width: size, height: size }} className="rounded bg-gray-100" />;
  return <QrCode value={url} size={size} className="rounded border border-gray-200" />;
}
