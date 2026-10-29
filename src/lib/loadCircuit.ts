import { promises as fs } from "fs";
import path from "path";
import type { Catalog, CircuitDefinition } from "./types";

const dataRoot = path.join(process.cwd(), "data");

export async function readCatalog(): Promise<Catalog> {
  const raw = await fs.readFile(path.join(dataRoot, "catalog.json"), "utf8");
  return JSON.parse(raw) as Catalog;
}

export async function readCircuit(
  id: string
): Promise<CircuitDefinition | null> {
  const file = path.join(dataRoot, "circuits", `${id}.json`);
  try {
    const raw = await fs.readFile(file, "utf8");
    return JSON.parse(raw) as CircuitDefinition;
  } catch {
    return null;
  }
}

export async function listCircuitIds(): Promise<string[]> {
  const cat = await readCatalog();
  return cat.circuits.filter((c) => !c.skipped).map((c) => c.id);
}
