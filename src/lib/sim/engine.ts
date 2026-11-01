import type { CircuitComponent, CircuitDefinition, PartType } from "../types";

export interface SimState {
  /** Live boolean signals (inputs + coils + timer Q + counter Q) */
  signals: Record<string, boolean>;
  /** Elapsed ms for timers keyed by component id */
  timerEt: Record<string, number>;
  /** Counter current values */
  counterCv: Record<string, number>;
  /** Previous edge memory for counters */
  edges: Record<string, boolean>;
  running: boolean;
}

const PASSIVE_ALWAYS: PartType[] = ["RAIL_L", "RAIL_R"];

function isConductive(
  comp: CircuitComponent,
  signals: Record<string, boolean>
): boolean {
  if (PASSIVE_ALWAYS.includes(comp.type)) return true;

  if (comp.type === "OL") {
    // OL NC: open only if overload signal true
    return !signals[comp.signal ?? "OL"];
  }

  if (
    comp.type === "PB_NO" ||
    comp.type === "CONTACT_NO" ||
    comp.type === "SENSOR" ||
    comp.type === "THERMOSTAT"
  ) {
    const key = comp.monitors ?? comp.signal;
    if (!key) return false;
    return !!signals[key];
  }

  if (comp.type === "PB_NC" || comp.type === "CONTACT_NC") {
    const key = comp.monitors ?? comp.signal;
    if (!key) return true;
    return !signals[key];
  }

  // Timer FB: Q side is live when timer output bit is true (drives coil on same rung)
  if (
    (comp.type === "TON" || comp.type === "TOF" || comp.type === "TP") &&
    comp.signal
  ) {
    return !!signals[comp.signal];
  }

  if (
    comp.type === "COIL" ||
    comp.type === "LAMP" ||
    comp.type === "CTU" ||
    comp.type === "CTD" ||
    comp.type === "CTUD"
  ) {
    return false;
  }

  return false;
}

function buildAdjacency(
  circuit: CircuitDefinition,
  wires: { from: string; to: string }[]
): Map<string, Set<string>> {
  const adj = new Map<string, Set<string>>();
  const add = (a: string, b: string) => {
    if (!adj.has(a)) adj.set(a, new Set());
    adj.get(a)!.add(b);
  };

  // Internal component continuity L↔R when conductive — handled at search time
  for (const w of wires) {
    add(w.from, w.to);
    add(w.to, w.from);
  }
  return adj;
}

function componentOfPort(
  circuit: CircuitDefinition,
  portRef: string
): CircuitComponent | undefined {
  const id = portRef.split(".")[0];
  return circuit.components.find((c) => c.id === id);
}

/** Can power flow from L1 rails to this coil's left port? */
function powered(
  circuit: CircuitDefinition,
  wires: { from: string; to: string }[],
  signals: Record<string, boolean>,
  targetPort: string
): boolean {
  const adj = buildAdjacency(circuit, wires);
  const railPorts = circuit.components
    .filter((c) => c.type === "RAIL_L")
    .flatMap((c) => c.ports.map((p) => `${c.id}.${p.id}`));

  if (railPorts.length === 0) return false;

  const visited = new Set<string>();
  const stack = [...railPorts];

  while (stack.length) {
    const cur = stack.pop()!;
    if (visited.has(cur)) continue;
    visited.add(cur);
    if (cur === targetPort) return true;

    const comp = componentOfPort(circuit, cur);
    if (!comp) continue;

    // Cross through component if conductive (or rail)
    const canCross =
      PASSIVE_ALWAYS.includes(comp.type) || isConductive(comp, signals);

    if (canCross) {
      for (const p of comp.ports) {
        const other = `${comp.id}.${p.id}`;
        if (other !== cur && !visited.has(other)) stack.push(other);
      }
    }

    // Also: coil/lamp/timer IN port is the destination — don't cross through them
    // but we already return true when we reach targetPort

    for (const n of adj.get(cur) ?? []) {
      if (!visited.has(n)) stack.push(n);
    }
  }
  return false;
}

export function createInitialState(circuit: CircuitDefinition): SimState {
  const signals: Record<string, boolean> = {};
  for (const inp of circuit.simulation.inputs) {
    signals[inp.id] = inp.default ?? (inp.kind === "nc-hold" ? true : false);
  }
  for (const out of circuit.simulation.outputs) {
    signals[out.id] = false;
  }
  // Ensure coil signals exist
  for (const c of circuit.components) {
    if (c.signal && signals[c.signal] === undefined) signals[c.signal] = false;
  }
  return {
    signals,
    timerEt: {},
    counterCv: {},
    edges: {},
    running: false,
  };
}

export function setInput(
  state: SimState,
  id: string,
  value: boolean
): SimState {
  return {
    ...state,
    signals: { ...state.signals, [id]: value },
  };
}

export function tick(
  circuit: CircuitDefinition,
  wires: { from: string; to: string }[],
  state: SimState,
  dtMs: number
): SimState {
  if (!state.running) return state;

  // PLC scan: contacts see previous image; write new image once per tick
  const prev = { ...state.signals };
  const next = { ...state.signals };
  const timerEt = { ...state.timerEt };
  const counterCv = { ...state.counterCv };
  const edges = { ...state.edges };

  // 1) Timers / counters first (IN path uses previous coil image)
  for (const comp of circuit.components) {
    if (comp.type === "TON" && comp.signal) {
      const inn = powered(circuit, wires, prev, `${comp.id}.IN`);
      const pt = comp.preset ?? 1000;
      if (inn) {
        timerEt[comp.id] = (timerEt[comp.id] ?? 0) + dtMs;
        next[comp.signal] = (timerEt[comp.id] ?? 0) >= pt;
      } else {
        timerEt[comp.id] = 0;
        next[comp.signal] = false;
      }
    }

    if (comp.type === "TOF" && comp.signal) {
      const inn = powered(circuit, wires, prev, `${comp.id}.IN`);
      const pt = comp.preset ?? 1000;
      if (inn) {
        timerEt[comp.id] = pt;
        next[comp.signal] = true;
      } else if ((timerEt[comp.id] ?? 0) > 0) {
        timerEt[comp.id] = Math.max(0, (timerEt[comp.id] ?? 0) - dtMs);
        next[comp.signal] = true;
      } else {
        next[comp.signal] = false;
      }
    }

    if (comp.type === "TP" && comp.signal) {
      const inn = powered(circuit, wires, prev, `${comp.id}.IN`);
      const pt = comp.preset ?? 1000;
      const was = edges[comp.id] ?? false;
      if (inn && !was) timerEt[comp.id] = pt;
      edges[comp.id] = inn;
      if ((timerEt[comp.id] ?? 0) > 0) {
        timerEt[comp.id] = Math.max(0, (timerEt[comp.id] ?? 0) - dtMs);
        next[comp.signal] = true;
      } else {
        next[comp.signal] = false;
      }
    }

    if (comp.type === "CTU" && comp.signal) {
      const cu = powered(circuit, wires, prev, `${comp.id}.CU`);
      const rst = powered(circuit, wires, prev, `${comp.id}.R`);
      const was = edges[comp.id] ?? false;
      if (rst) counterCv[comp.id] = 0;
      else if (cu && !was) counterCv[comp.id] = (counterCv[comp.id] ?? 0) + 1;
      edges[comp.id] = cu;
      next[comp.signal] = (counterCv[comp.id] ?? 0) >= (comp.preset ?? 10);
    }

    if (comp.type === "CTD" && comp.signal) {
      const cd = powered(circuit, wires, prev, `${comp.id}.CD`);
      const ld = powered(circuit, wires, prev, `${comp.id}.LD`);
      const was = edges[comp.id] ?? false;
      const pv = comp.preset ?? 10;
      if (ld) counterCv[comp.id] = pv;
      else if (cd && !was)
        counterCv[comp.id] = Math.max(0, (counterCv[comp.id] ?? pv) - 1);
      edges[comp.id] = cd;
      next[comp.signal] = (counterCv[comp.id] ?? pv) <= 0;
    }
  }

  // Merge timer bits into contact image for coil evaluation this scan
  const mid = { ...prev, ...Object.fromEntries(
    circuit.components
      .filter((c) =>
        (c.type === "TON" || c.type === "TOF" || c.type === "TP" ||
          c.type === "CTU" || c.type === "CTD") &&
        c.signal
      )
      .map((c) => [c.signal!, next[c.signal!]])
  )};

  // 2) Ordinary coils / lamps. Contacts still see the previous coil image,
  // while timer Q bits in `mid` are already this scan's values.
  for (const comp of circuit.components) {
    if (
      (comp.type === "COIL" || comp.type === "LAMP") &&
      comp.signal &&
      !comp.coilAction
    ) {
      next[comp.signal] = powered(circuit, wires, mid, `${comp.id}.L`);
    }
  }

  // 3) Set/Reset latches. CR (and any other coil written above) is visible,
  // so a lower Reset rung can use the timer coil from this same scan.
  // Reset wins when Set and Reset are both true, matching top-to-bottom order.
  const latched = { ...mid };
  for (const comp of circuit.components) {
    if (
      (comp.type === "COIL" || comp.type === "LAMP") &&
      comp.signal &&
      !comp.coilAction
    ) {
      latched[comp.signal] = !!next[comp.signal];
    }
  }

  const srSignals = new Set(
    circuit.components
      .filter((c) => c.coilAction && c.signal)
      .map((c) => c.signal as string)
  );
  for (const sig of srSignals) {
    let value = !!prev[sig];
    const sets = circuit.components.filter(
      (c) => c.coilAction === "set" && c.signal === sig
    );
    const resets = circuit.components.filter(
      (c) => c.coilAction === "reset" && c.signal === sig
    );
    if (sets.some((c) => powered(circuit, wires, latched, `${c.id}.L`))) {
      value = true;
    }
    if (resets.some((c) => powered(circuit, wires, latched, `${c.id}.L`))) {
      value = false;
    }
    next[sig] = value;
  }

  return { ...state, signals: next, timerEt, counterCv, edges };
}
