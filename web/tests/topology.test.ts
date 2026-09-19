import { describe, expect, it } from "vitest";

import { buildEvidenceTopology } from "../src/lib/topology";
import type { AssayMapLane, EvidenceRecord } from "../src/lib/decision-twin";

const evidence: EvidenceRecord[] = [
  {
    id: "ev-cell",
    claim: "A measured cellular observation.",
    citation: { source: "europe_pmc", source_id: "PMC1", retrieved_at: "2026-09-19T00:00:00Z" },
    assay_context: { target_id: "EGFR", biological_system: "cell_line", readout: "ic50", unit: "nM" },
    outcome_direction: "contradicts",
  },
  {
    id: "ev-human",
    claim: "A human observation.",
    citation: { source: "chembl", source_id: "CHEMBL203", retrieved_at: "2026-09-19T00:00:00Z" },
    assay_context: { target_id: "EGFR", biological_system: "human", readout: "pfs", unit: "months" },
    outcome_direction: "supports",
  },
];

const lanes: AssayMapLane[] = [
  { stage: "biochemical", status: "missing", evidence_ids: [], gaps: ["No biochemical record."] },
  { stage: "cellular", status: "contradicting", evidence_ids: ["ev-cell"], gaps: [] },
  { stage: "in_vivo", status: "missing", evidence_ids: [], gaps: ["No in-vivo record."] },
  { stage: "human", status: "supporting", evidence_ids: ["ev-human"], gaps: [] },
];

describe("evidence topology", () => {
  it("maps only retained source records into source nodes and preserves their assay layer", () => {
    const topology = buildEvidenceTopology(evidence, lanes);

    expect(topology.sources.map((source) => source.id)).toEqual(["chembl", "europe_pmc"]);
    expect(topology.records.find((record) => record.id === "ev-cell")?.stage).toBe("cellular");
    expect(topology.records.find((record) => record.id === "ev-human")?.stage).toBe("human");
  });

  it("keeps absent biological layers as explicitly missing nodes, never as a filled data point", () => {
    const topology = buildEvidenceTopology(evidence, lanes);

    expect(topology.stages.find((stage) => stage.id === "biochemical")).toMatchObject({
      status: "missing",
      evidenceCount: 0,
    });
    expect(topology.connectors.some((edge) => edge.kind === "missing")).toBe(true);
  });
});
