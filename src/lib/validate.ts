import type {
  CircuitDefinition,
  ReferenceWire,
  ValidationIssue,
  ValidationResult,
} from "./types";

/** Normalize undirected wire endpoint pair for comparison */
export function wireKey(from: string, to: string): string {
  return [from, to].sort().join("|");
}

export function normalizeStudentWires(
  wires: { from: string; to: string }[]
): Set<string> {
  return new Set(wires.map((w) => wireKey(w.from, w.to)));
}

export function referenceWireSet(wires: ReferenceWire[]): Set<string> {
  return new Set(wires.map((w) => wireKey(w.from, w.to)));
}

function labelPort(port: string, circuit: CircuitDefinition): string {
  const [compId, portId] = port.split(".");
  const comp = circuit.components.find((c) => c.id === compId);
  if (!comp) return port;
  return `${comp.label}.${portId}`;
}

export function validateWiring(
  circuit: CircuitDefinition,
  studentWires: { from: string; to: string }[]
): ValidationResult {
  const expected = referenceWireSet(circuit.referenceWires);
  const actual = normalizeStudentWires(studentWires);
  const issues: ValidationIssue[] = [];

  for (const w of circuit.referenceWires) {
    const key = wireKey(w.from, w.to);
    if (!actual.has(key)) {
      issues.push({
        code: "missing_wire",
        message: `ناقص سلك: من «${labelPort(w.from, circuit)}» إلى «${labelPort(w.to, circuit)}»`,
        expectedFrom: w.from,
        expectedTo: w.to,
      });
    }
  }

  for (const w of studentWires) {
    const key = wireKey(w.from, w.to);
    if (!expected.has(key)) {
      issues.push({
        code: "extra_wire",
        message: `سلك زائد غير موجود في الملزمة: من «${labelPort(w.from, circuit)}» إلى «${labelPort(w.to, circuit)}»`,
        actualFrom: w.from,
        actualTo: w.to,
      });
    }
  }

  const matched = circuit.referenceWires.filter((w) =>
    actual.has(wireKey(w.from, w.to))
  ).length;

  return {
    ok: issues.length === 0,
    matched,
    expected: circuit.referenceWires.length,
    issues,
  };
}

export function nextGuideHint(
  circuit: CircuitDefinition,
  studentWires: { from: string; to: string }[],
  stepIndex: number
) {
  const result = validateWiring(circuit, studentWires);
  if (result.ok) {
    return {
      done: true as const,
      message: "الربط مطابق للملزمة. يمكنك تشغيل المحاكاة.",
    };
  }

  const step = circuit.steps[stepIndex];
  if (step?.wireId) {
    const wire = circuit.referenceWires.find((w) => w.id === step.wireId);
    if (wire) {
      const key = wireKey(wire.from, wire.to);
      const has = normalizeStudentWires(studentWires).has(key);
      if (!has) {
        return {
          done: false as const,
          message: step.detail,
          ghostFrom: wire.from,
          ghostTo: wire.to,
          step,
        };
      }
    }
  }

  const missing = result.issues.find((i) => i.code === "missing_wire");
  if (missing) {
    return {
      done: false as const,
      message: missing.message + " — اربط النقطتين كما في رسم الملزمة فقط.",
      ghostFrom: missing.expectedFrom,
      ghostTo: missing.expectedTo,
      step,
    };
  }

  const extra = result.issues.find((i) => i.code === "extra_wire");
  return {
    done: false as const,
    message: extra?.message ?? result.issues[0]?.message ?? "راجع الربط",
    step,
  };
}
