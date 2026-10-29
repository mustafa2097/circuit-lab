"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";
import { partMeta } from "@/lib/parts";
import type { PartType } from "@/lib/types";
import clsx from "clsx";

export type PartNodeData = {
  label: string;
  partType: PartType;
  ports: { id: string; side: "left" | "right" | "top" | "bottom" }[];
  live?: boolean;
  highlight?: boolean;
};

function sideToPos(side: string): Position {
  if (side === "left") return Position.Left;
  if (side === "right") return Position.Right;
  if (side === "top") return Position.Top;
  return Position.Bottom;
}

export function PartNode({ data }: NodeProps) {
  const d = data as PartNodeData;
  const meta = partMeta(d.partType);
  const isRail = d.partType === "RAIL_L" || d.partType === "RAIL_R";

  return (
    <div
      className={clsx(
        "rounded-md border bg-white px-3 py-2 shadow-sm",
        d.highlight ? "border-teal-600 ring-2 ring-teal-200" : "border-gray-300",
        d.live ? "live-on" : "live-off",
        isRail ? "min-h-[120px] w-12" : "min-w-[108px]"
      )}
      style={{ borderTopWidth: 3, borderTopColor: meta.color }}
    >
      {d.ports.map((p) => (
        <Handle
          key={p.id}
          id={p.id}
          type="source"
          position={sideToPos(p.side)}
          className="!h-3 !w-3 !rounded-full !border-2 !border-white !bg-gray-800"
        />
      ))}

      <div className="text-center">
        <div className="text-[11px] font-semibold text-gray-500">{meta.symbol}</div>
        <div className="text-sm font-semibold text-gray-900">{d.label}</div>
      </div>
    </div>
  );
}
