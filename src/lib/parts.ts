import type { PartType, PortDef } from "./types";

export interface PartMeta {
  type: PartType;
  titleAr: string;
  titleEn: string;
  color: string;
  defaultPorts: PortDef[];
  width: number;
  height: number;
  symbol: string;
}

const LR = (left = "L", right = "R"): PortDef[] => [
  { id: left, side: "left" },
  { id: right, side: "right" },
];

export const PART_LIBRARY: Record<PartType, PartMeta> = {
  RAIL_L: {
    type: "RAIL_L",
    titleAr: "عمود L1",
    titleEn: "L1 Column",
    color: "#111827",
    defaultPorts: [{ id: "out", side: "right", label: "L1" }],
    width: 48,
    height: 160,
    symbol: "L1",
  },
  RAIL_R: {
    type: "RAIL_R",
    titleAr: "عمود L2",
    titleEn: "L2 Column",
    color: "#111827",
    defaultPorts: [{ id: "in", side: "left", label: "L2" }],
    width: 48,
    height: 160,
    symbol: "L2",
  },
  PB_NO: {
    type: "PB_NO",
    titleAr: "ضغطة NO",
    titleEn: "Pushbutton NO",
    color: "#2563EB",
    defaultPorts: LR(),
    width: 110,
    height: 56,
    symbol: "PB⏐ ⏐",
  },
  PB_NC: {
    type: "PB_NC",
    titleAr: "ضغطة NC",
    titleEn: "Pushbutton NC",
    color: "#DC2626",
    defaultPorts: LR(),
    width: 110,
    height: 56,
    symbol: "PB⏐/⏐",
  },
  CONTACT_NO: {
    type: "CONTACT_NO",
    titleAr: "تلامس NO",
    titleEn: "NO Contact",
    color: "#0F766E",
    defaultPorts: LR(),
    width: 110,
    height: 52,
    symbol: "⏐ ⏐",
  },
  CONTACT_NC: {
    type: "CONTACT_NC",
    titleAr: "تلامس NC",
    titleEn: "NC Contact",
    color: "#B45309",
    defaultPorts: LR(),
    width: 110,
    height: 52,
    symbol: "⏐/⏐",
  },
  COIL: {
    type: "COIL",
    titleAr: "ملف",
    titleEn: "Coil",
    color: "#7C3AED",
    defaultPorts: LR(),
    width: 100,
    height: 56,
    symbol: "( )",
  },
  LAMP: {
    type: "LAMP",
    titleAr: "لمبة",
    titleEn: "Lamp",
    color: "#CA8A04",
    defaultPorts: LR(),
    width: 100,
    height: 56,
    symbol: "◎",
  },
  OL: {
    type: "OL",
    titleAr: "حماية حمل زائد",
    titleEn: "Overload",
    color: "#EA580C",
    defaultPorts: LR(),
    width: 100,
    height: 52,
    symbol: "OL",
  },
  TON: {
    type: "TON",
    titleAr: "مؤقت TON",
    titleEn: "On-Delay",
    color: "#0369A1",
    defaultPorts: LR("IN", "Q"),
    width: 120,
    height: 72,
    symbol: "TON",
  },
  TOF: {
    type: "TOF",
    titleAr: "مؤقت TOF",
    titleEn: "Off-Delay",
    color: "#075985",
    defaultPorts: LR("IN", "Q"),
    width: 120,
    height: 72,
    symbol: "TOF",
  },
  TP: {
    type: "TP",
    titleAr: "مؤقت نبضة",
    titleEn: "Pulse Timer",
    color: "#0E7490",
    defaultPorts: LR("IN", "Q"),
    width: 120,
    height: 72,
    symbol: "TP",
  },
  CTU: {
    type: "CTU",
    titleAr: "عداد تصاعدي",
    titleEn: "Up Counter",
    color: "#4F46E5",
    defaultPorts: [
      { id: "CU", side: "left" },
      { id: "R", side: "left" },
      { id: "Q", side: "right" },
    ],
    width: 120,
    height: 80,
    symbol: "CTU",
  },
  CTD: {
    type: "CTD",
    titleAr: "عداد تنازلي",
    titleEn: "Down Counter",
    color: "#4338CA",
    defaultPorts: [
      { id: "CD", side: "left" },
      { id: "LD", side: "left" },
      { id: "Q", side: "right" },
    ],
    width: 120,
    height: 80,
    symbol: "CTD",
  },
  CTUD: {
    type: "CTUD",
    titleAr: "عداد صعود/نزول",
    titleEn: "Up/Down Counter",
    color: "#3730A3",
    defaultPorts: [
      { id: "CU", side: "left" },
      { id: "CD", side: "left" },
      { id: "QU", side: "right" },
      { id: "QD", side: "right" },
    ],
    width: 130,
    height: 88,
    symbol: "CTUD",
  },
  SENSOR: {
    type: "SENSOR",
    titleAr: "حساس",
    titleEn: "Sensor",
    color: "#059669",
    defaultPorts: LR(),
    width: 110,
    height: 52,
    symbol: "S",
  },
  THERMOSTAT: {
    type: "THERMOSTAT",
    titleAr: "ترموستات",
    titleEn: "Thermostat",
    color: "#BE123C",
    defaultPorts: LR(),
    width: 120,
    height: 52,
    symbol: "θ",
  },
};

export function partMeta(type: PartType): PartMeta {
  return PART_LIBRARY[type];
}
