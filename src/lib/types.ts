export type PartType =
  | "RAIL_L"
  | "RAIL_R"
  | "PB_NO"
  | "PB_NC"
  | "CONTACT_NO"
  | "CONTACT_NC"
  | "COIL"
  | "LAMP"
  | "OL"
  | "TON"
  | "TOF"
  | "TP"
  | "CTU"
  | "CTD"
  | "CTUD"
  | "SENSOR"
  | "THERMOSTAT";

export interface PortDef {
  id: string;
  side: "left" | "right" | "top" | "bottom";
  label?: string;
}

export interface CircuitComponent {
  id: string;
  type: PartType;
  label: string;
  /** Simulation signal name (input key or coil/output key) */
  signal?: string;
  /** For aux contacts: which coil/signal they follow */
  monitors?: string;
  normallyClosed?: boolean;
  /** Timer/counter preset in ms or counts */
  preset?: number;
  ports: PortDef[];
  /** Disassembled tray position */
  trayPosition: { x: number; y: number };
  /** Correct assembled position on canvas */
  targetPosition: { x: number; y: number };
}

export interface ReferenceWire {
  id: string;
  from: string; // componentId.portId
  to: string;
}

export interface GuideStep {
  id: string;
  title: string;
  detail: string;
  /** Highlight this wire while guiding */
  wireId?: string;
  from?: string;
  to?: string;
  placeComponentId?: string;
}

export interface SimInput {
  id: string;
  label: string;
  kind: "momentary" | "toggle" | "nc-hold";
  default?: boolean;
}

export interface SimOutput {
  id: string;
  label: string;
  kind: "coil" | "lamp" | "actuator" | "timer" | "counter";
}

export interface CircuitDefinition {
  id: string;
  title: string;
  titleAr: string;
  sourceFile: string;
  page: string;
  purpose: string;
  /** Image of the original booklet circuit diagram */
  referenceImage?: string;
  components: CircuitComponent[];
  referenceWires: ReferenceWire[];
  steps: GuideStep[];
  simulation: {
    inputs: SimInput[];
    outputs: SimOutput[];
    tickMs?: number;
    description: string;
  };
}

export interface CatalogEntry {
  id: string;
  title: string;
  titleAr: string;
  sourceFile: string;
  page: string;
  category: string;
  kind: string;
  purpose: string;
  slug: string;
  skipped: boolean;
  skipReason: string | null;
  dataFile: string | null;
}

export interface Catalog {
  version: number;
  total: number;
  active: number;
  skipped: number;
  circuits: CatalogEntry[];
}

export interface ValidationIssue {
  code: "missing_wire" | "extra_wire" | "missing_component" | "wrong_place";
  message: string;
  expectedFrom?: string;
  expectedTo?: string;
  actualFrom?: string;
  actualTo?: string;
}

export interface ValidationResult {
  ok: boolean;
  matched: number;
  expected: number;
  issues: ValidationIssue[];
}
