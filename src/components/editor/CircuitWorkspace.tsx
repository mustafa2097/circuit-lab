"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useEdgesState,
  useNodesState,
  ConnectionMode,
  useReactFlow,
  ReactFlowProvider,
  type Connection,
  type Edge,
  type Node,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { CircuitComponent, CircuitDefinition } from "@/lib/types";
import { PartNode, type PartNodeData } from "./PartNode";
import { PartsNav } from "./PartsNav";
import { nextGuideHint, validateWiring } from "@/lib/validate";
import {
  createInitialState,
  setInput,
  tick,
  type SimState,
} from "@/lib/sim/engine";

const nodeTypes = { part: PartNode };

function portRef(nodeId: string, handle?: string | null) {
  if (!handle) return nodeId;
  const h = handle.startsWith("t-") ? handle.slice(2) : handle;
  return `${nodeId}.${h}`;
}

function edgesToWires(edges: Edge[]) {
  return edges.map((e) => ({
    from: portRef(e.source, e.sourceHandle),
    to: portRef(e.target, e.targetHandle),
  }));
}

function componentToNode(c: CircuitComponent): Node {
  return {
    id: c.id,
    type: "part",
    position: { ...c.targetPosition },
    data: {
      label: c.label,
      partType: c.type,
      ports: c.ports,
      symbol: c.symbol,
      live: false,
      highlight: false,
    } satisfies PartNodeData,
  };
}

function WorkspaceInner({ circuit }: { circuit: CircuitDefinition }) {
  const { fitView, setCenter } = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [stepIndex, setStepIndex] = useState(0);
  const [sim, setSim] = useState<SimState>(() => createInitialState(circuit));
  const [showDiagram, setShowDiagram] = useState(false);
  const [dropCount, setDropCount] = useState(0);
  const timerRef = useRef<number | null>(null);
  const wiresRef = useRef<{ from: string; to: string }[]>([]);

  const placedIds = useMemo(() => new Set(nodes.map((n) => n.id)), [nodes]);

  const trayParts = useMemo(
    () => circuit.components.filter((c) => !placedIds.has(c.id)),
    [circuit.components, placedIds]
  );

  const wires = useMemo(() => edgesToWires(edges), [edges]);
  wiresRef.current = wires;

  const validation = useMemo(
    () => validateWiring(circuit, wires),
    [circuit, wires]
  );

  const guide = useMemo(
    () => nextGuideHint(circuit, wires, stepIndex),
    [circuit, wires, stepIndex]
  );

  const ghostEdge: Edge | null = useMemo(() => {
    if (!("ghostFrom" in guide) || !guide.ghostFrom || !guide.ghostTo) {
      return null;
    }
    const [sId, sH] = guide.ghostFrom.split(".");
    const [tId, tH] = guide.ghostTo.split(".");
    if (!placedIds.has(sId) || !placedIds.has(tId)) return null;
    return {
      id: "ghost-guide",
      source: sId,
      sourceHandle: sH,
      target: tId,
      targetHandle: tH,
      className: "ghost-edge",
      animated: true,
      style: { stroke: "#0f766e" },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#0f766e" },
      selectable: false,
      focusable: false,
      interactionWidth: 0,
    };
  }, [guide, placedIds]);

  const highlightId = guide.step?.placeComponentId ?? null;

  const displayNodes = useMemo(
    () =>
      nodes.map((n) => {
        const c = circuit.components.find((x) => x.id === n.id);
        const key = c?.signal;
        // A Reset coil shares the latched bit, but it is not "on" while that bit is held.
        const live =
          c?.coilAction === "reset" ? false : key ? !!sim.signals[key] : false;
        const prev = n.data as PartNodeData;
        return {
          ...n,
          data: {
            ...prev,
            live,
            highlight: highlightId === n.id,
          } satisfies PartNodeData,
        };
      }),
    [nodes, sim.signals, circuit.components, highlightId]
  );

  const displayEdges = useMemo(
    () => (ghostEdge ? [...edges, ghostEdge] : edges),
    [edges, ghostEdge]
  );

  const placePart = useCallback(
    (partId: string) => {
      const c = circuit.components.find((x) => x.id === partId);
      if (!c) return;
      setNodes((nds) => {
        if (nds.some((n) => n.id === partId)) return nds;
        const offset = (dropCount % 6) * 12;
        const node = componentToNode(c);
        node.position = {
          x: c.targetPosition.x + offset,
          y: c.targetPosition.y + offset,
        };
        return [...nds, node];
      });
      setDropCount((n) => n + 1);
      window.requestAnimationFrame(() => {
        setCenter(
          c.targetPosition.x + 60,
          c.targetPosition.y + 40,
          { zoom: 1, duration: 280 }
        );
      });
    },
    [circuit.components, dropCount, setNodes, setCenter]
  );

  const onConnect = useCallback(
    (conn: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...conn,
            id: `e-${conn.source}-${conn.sourceHandle}-${conn.target}-${conn.targetHandle}-${Date.now()}`,
            style: { stroke: "#111827", strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed, color: "#111827" },
          },
          eds
        )
      );
    },
    [setEdges]
  );

  const resetAll = () => {
    setNodes([]);
    setEdges([]);
    setStepIndex(0);
    setDropCount(0);
    setSim(createInitialState(circuit));
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = null;
  };

  const snapAndShowSolution = () => {
    setNodes(circuit.components.map((c) => componentToNode(c)));
    setEdges(
      circuit.referenceWires.map((w) => {
        const [sId, sH] = w.from.split(".");
        const [tId, tH] = w.to.split(".");
        return {
          id: `sol-${w.id}`,
          source: sId,
          sourceHandle: sH,
          target: tId,
          targetHandle: tH,
          style: { stroke: "#111827", strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: "#111827" },
        };
      })
    );
    window.requestAnimationFrame(() => fitView({ padding: 0.2, duration: 300 }));
  };

  const startSim = () => {
    if (!validation.ok) return;
    setSim((s) => ({ ...s, running: true }));
    if (timerRef.current) window.clearInterval(timerRef.current);
    const dt = circuit.simulation.tickMs ?? 50;
    timerRef.current = window.setInterval(() => {
      setSim((s) => tick(circuit, wiresRef.current, s, dt));
    }, dt);
  };

  const stopSim = () => {
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = null;
    setSim((s) => ({ ...s, running: false }));
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, []);

  // Reset board when circuit changes
  useEffect(() => {
    setNodes([]);
    setEdges([]);
    setStepIndex(0);
    setDropCount(0);
    setSim(createInitialState(circuit));
  }, [circuit, setNodes, setEdges]);

  const pressInput = (id: string, kind: string) => {
    if (kind === "momentary") {
      setSim((s) => setInput(s, id, true));
      window.setTimeout(() => {
        setSim((cur) => setInput(cur, id, false));
      }, 180);
    } else {
      setSim((s) => setInput(s, id, !s.signals[id]));
    }
  };

  const nextStep = () => {
    setStepIndex((i) => Math.min(i + 1, Math.max(circuit.steps.length - 1, 0)));
  };
  const prevStep = () => {
    setStepIndex((i) => Math.max(i - 1, 0));
  };

  const step = circuit.steps[stepIndex];
  const statusMessage = validation.ok
    ? circuit.simulation.description
    : guide.message;

  return (
    <div className="flex h-[calc(100dvh-64px)] flex-col">
      <PartsNav
        parts={trayParts}
        highlightedId={highlightId}
        onPlace={placePart}
      />

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[1fr_300px]">
        <div className="relative min-h-[45vh] border-gray-200 lg:border-l">
          <ReactFlow
            nodes={displayNodes}
            edges={displayEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            connectionMode={ConnectionMode.Loose}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background gap={18} color="#e5e7eb" />
            <Controls position="top-left" />
            <MiniMap
              position="bottom-left"
              pannable
              zoomable
              className="!bg-white !border !border-gray-200"
            />
          </ReactFlow>

          {nodes.length === 0 ? (
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <div className="rounded-lg border border-dashed border-gray-300 bg-white/90 px-4 py-3 text-sm text-gray-500">
                اختر قطعة من الشريط العلوي لتنزل هنا
              </div>
            </div>
          ) : null}

          <div className="pointer-events-none absolute left-3 top-3 rounded-md border border-gray-200 bg-white/95 px-3 py-2 text-xs text-gray-600 shadow-sm">
            مطابق الملزمة: {validation.matched}/{validation.expected}
            {validation.ok ? (
              <span className="mr-2 text-green-700"> — جاهز للتشغيل</span>
            ) : null}
          </div>
        </div>

        <aside className="flex flex-col gap-3 overflow-y-auto border-gray-200 bg-white p-4">
          <div>
            <div className="text-xs text-gray-500">خطوة الربط</div>
            <div className="mt-1 text-sm font-semibold">
              {step ? `${stepIndex + 1}. ${step.title}` : "لا خطوات"}
            </div>
            <p className="mt-1 text-sm leading-6 text-gray-600">
              {step?.detail ?? ""}
            </p>
            <div className="mt-2 flex gap-2">
              <button
                type="button"
                onClick={prevStep}
                className="rounded border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
              >
                السابق
              </button>
              <button
                type="button"
                onClick={nextStep}
                className="rounded border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
              >
                التالي
              </button>
            </div>
          </div>

          <div className="rounded-md border border-teal-100 bg-teal-50/60 p-3 text-sm leading-6 text-teal-950">
            {statusMessage}
          </div>

          {!validation.ok && validation.issues.length > 0 ? (
            <div className="rounded-md border border-red-100 bg-red-50 p-3">
              <div className="text-xs font-semibold text-red-800">تصحيح الربط</div>
              <ul className="mt-1 list-disc pr-4 text-sm text-red-900">
                {validation.issues.slice(0, 4).map((iss, i) => (
                  <li key={i}>{iss.message}</li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setShowDiagram(true)}
              disabled={!circuit.referenceImage}
              className="rounded-md border border-gray-900 px-3 py-2 text-sm font-medium text-gray-900 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              عرض الدائرة
            </button>
            <button
              type="button"
              onClick={startSim}
              disabled={!validation.ok}
              className="rounded-md bg-teal-700 px-3 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              تشغيل
            </button>
            <button
              type="button"
              onClick={stopSim}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
            >
              إيقاف
            </button>
            <button
              type="button"
              onClick={resetAll}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
            >
              إعادة تعيين
            </button>
            <button
              type="button"
              onClick={snapAndShowSolution}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
            >
              عرض حل الملزمة
            </button>
          </div>

          <div>
            <div className="mb-2 text-xs font-semibold text-gray-500">
              لوحة التشغيل
            </div>
            <div className="flex flex-wrap gap-2">
              {circuit.simulation.inputs.map((inp) => {
                const on = !!sim.signals[inp.id];
                return (
                  <button
                    key={inp.id}
                    type="button"
                    onClick={() => pressInput(inp.id, inp.kind)}
                    className={
                      on
                        ? "rounded-md bg-gray-900 px-3 py-2 text-sm text-white"
                        : "rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
                    }
                  >
                    {inp.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <div className="mb-2 text-xs font-semibold text-gray-500">المخارج</div>
            <div className="grid grid-cols-2 gap-2">
              {circuit.simulation.outputs.map((out) => {
                const on = !!sim.signals[out.id];
                return (
                  <div
                    key={out.id}
                    className={
                      on
                        ? "rounded-md border border-green-300 bg-green-50 px-2 py-2 text-sm"
                        : "rounded-md border border-gray-200 px-2 py-2 text-sm text-gray-500"
                    }
                  >
                    <div className="font-medium">{out.label}</div>
                    <div className="text-xs">{on ? "ON" : "OFF"}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-auto text-[11px] leading-5 text-gray-400">
            اضغط القطعة من الشريط لتنزل، ثم اربط المنافذ كما في الملزمة.
          </div>
        </aside>
      </div>

      {showDiagram && circuit.referenceImage ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          role="dialog"
          aria-modal="true"
          aria-label="عرض الدائرة"
          onClick={() => setShowDiagram(false)}
        >
          <div
            className="relative max-h-[92vh] w-full max-w-5xl overflow-auto rounded-lg bg-white p-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-gray-900">عرض الدائرة</div>
                <div className="text-xs text-gray-500">
                  {circuit.sourceFile} · {circuit.page}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowDiagram(false)}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
              >
                إغلاق
              </button>
            </div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={circuit.referenceImage}
              alt={`دائرة الملزمة: ${circuit.titleAr || circuit.title}`}
              className="mx-auto max-h-[80vh] w-auto max-w-full rounded border border-gray-200 object-contain"
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function CircuitWorkspace({ circuit }: { circuit: CircuitDefinition }) {
  return (
    <ReactFlowProvider>
      <WorkspaceInner circuit={circuit} />
    </ReactFlowProvider>
  );
}
