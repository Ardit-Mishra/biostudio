import { describe, expect, it } from "vitest";

import {
  filenameFor,
  toCsv,
  toJson,
  toMarkdown,
  toRis,
  type DecisionRecordInput,
} from "../src/lib/decision-record";
import type { Compilation, EvidenceRecord } from "../src/lib/decision-twin";

const evidence: EvidenceRecord[] = [
  {
    id: "ev-human",
    claim: 'A claim with a "quote", a comma, and\na newline.',
    citation: { source: "europe_pmc", source_id: "42714840", retrieved_at: "2026-09-18T17:51:39Z" },
    source_title: "Osimertinib After Definitive Chemoradiotherapy.",
    excerpt: "Retained excerpt.",
    assay_context: {
      target_id: "ENSG00000146648",
      biological_system: "human",
      readout: "progression_free_survival",
      unit: "months",
      genetic_context: "EGFR-mutated",
      conditions: { design: "randomized_trial" },
    },
    outcome_direction: "supports",
  },
  {
    id: "ev-cell",
    claim: "A contradicting cellular observation.",
    citation: { source: "europe_pmc", source_id: "PMC13585410", retrieved_at: "2026-09-18T17:51:39Z" },
    source_title: "Mechanisms of acquired resistance.",
    assay_context: {
      target_id: "ENSG00000146648",
      biological_system: "cell_line",
      readout: "viability_ic50",
      unit: "nM",
    },
    outcome_direction: "contradicts",
  },
];

const compilation: Compilation = {
  study_id: "study-egfr",
  status: "hold",
  reasons: ["Evidence conflict detected; resolve the incompatible observations before advancing."],
  comparisons: [
    {
      left_evidence_id: "ev-human",
      right_evidence_id: "ev-cell",
      relation: "conflicting",
      reason: "Comparable target evidence has opposing outcomes",
    },
  ],
  snapshot_digest: "4135d5daadd895d8f2deea639279d8a0c90671cbfd85943d5c98e781e72c5fdf",
  evidence_count: 2,
  assay_translation_map: {
    lanes: [
      { stage: "biochemical", status: "missing", evidence_ids: [], gaps: ["No biochemical evidence was supplied."] },
      { stage: "cellular", status: "contradicting", evidence_ids: ["ev-cell"], gaps: [] },
      { stage: "in_vivo", status: "missing", evidence_ids: [], gaps: ["No in vivo evidence was supplied."] },
      { stage: "human", status: "supporting", evidence_ids: ["ev-human"], gaps: [] },
      { stage: "unclassified", status: "missing", evidence_ids: [], gaps: [] },
    ],
  },
};

const record: DecisionRecordInput = {
  studyId: "study-egfr-nsclc-2026-09-19",
  title: "EGFR in non-small-cell lung cancer",
  question: "Is the public evidence strong enough to advance?",
  searchQuery: "EGFR osimertinib resistance",
  isExample: false,
  evidence,
  compilation,
  generatedAt: new Date("2026-09-19T12:00:00Z"),
};

describe("Decision Record — markdown dossier", () => {
  const md = toMarkdown(record);

  it("states the recommendation and every reason behind it", () => {
    expect(md).toContain("Hold");
    expect(md).toContain("Evidence conflict detected");
  });

  it("reports absence as explicitly as presence", () => {
    // A stage with no evidence has to appear in the document. A dossier that
    // silently omits the empty rows would read as if the chain were complete.
    expect(md).toContain("No biochemical evidence was supplied.");
    expect(md).toContain("No in vivo evidence was supplied.");
  });

  it("carries a resolvable citation for every record", () => {
    for (const r of evidence) expect(md).toContain(r.citation.source_id);
    expect(md).toContain("https://europepmc.org/article/MED/42714840");
    expect(md).toContain("https://europepmc.org/article/PMC/PMC13585410");
  });

  it("lists every decisive comparison with its reason", () => {
    expect(md).toContain("Comparable target evidence has opposing outcomes");
  });

  it("discloses the tool and the search, which reporting standards require", () => {
    expect(md).toContain("BioStudio Decision Twin");
    expect(md).toContain("EGFR osimertinib resistance");
  });

  it("keeps the claim separate from the source title", () => {
    expect(md).toContain("**Claim.**");
    expect(md).toContain("**Source title.**");
  });

  it("prints the digest needed to replay it", () => {
    expect(md).toContain(compilation.snapshot_digest);
  });
});

describe("Decision Record — CSV evidence table", () => {
  const csv = toCsv(record);

  it("emits a header and one row per record", () => {
    const rows = csv.trimEnd().split("\r\n");
    expect(rows).toHaveLength(1 + evidence.length);
  });

  it("survives quotes, commas and newlines inside a claim", () => {
    // The claim deliberately contains all three. Excel must still see 2 rows.
    expect(csv).toContain('""quote""');
    const rows = csv.trimEnd().split("\r\n");
    expect(rows).toHaveLength(3);
  });

  it("starts with a BOM so Excel reads UTF-8", () => {
    expect(csv.charCodeAt(0)).toBe(0xfeff);
  });

  it("carries the assay context that decided comparability", () => {
    expect(csv).toContain("progression_free_survival");
    expect(csv).toContain("EGFR-mutated");
  });
});

describe("Decision Record — RIS citations", () => {
  const ris = toRis(record);

  it("opens and closes one entry per record", () => {
    expect((ris.match(/^TY {2}- /gm) ?? [])).toHaveLength(evidence.length);
    expect((ris.match(/^ER {2}- /gm) ?? [])).toHaveLength(evidence.length);
  });

  it("uses the source title as the title, not the operator's claim", () => {
    expect(ris).toContain("TI  - Osimertinib After Definitive Chemoradiotherapy.");
    expect(ris).not.toContain("TI  - A contradicting cellular observation.");
  });

  it("records the PMID as an accession number for literature", () => {
    expect(ris).toContain("AN  - 42714840");
  });

  it("never emits a bare newline inside a field", () => {
    // RIS is line-oriented; an unescaped newline in an abstract corrupts the
    // record for every importer that reads it.
    for (const line of ris.split("\r\n")) {
      if (line === "") continue;
      expect(line).toMatch(/^[A-Z][A-Z0-9] {2}- /);
    }
  });
});

describe("Decision Record — replay snapshot", () => {
  const parsed = JSON.parse(toJson(record));

  it("carries the exact request the compiler was given", () => {
    // This is what makes the digest claim real: the body can be re-posted.
    expect(parsed.compile_request.study_id).toBe(record.studyId);
    expect(parsed.compile_request.evidence).toEqual(evidence);
    expect(parsed.compile_request.model_assessments).toEqual([]);
  });

  it("carries the digest the re-run must reproduce", () => {
    expect(parsed.compilation.snapshot_digest).toBe(compilation.snapshot_digest);
  });
});

describe("filenames", () => {
  it("strips characters a filesystem would reject", () => {
    expect(filenameFor("a/b\\c:*?d", "csv", new Date("2026-09-19T00:00:00Z")))
      .toBe("a-b-c-d-2026-09-19.csv");
  });

  it("never produces a nameless file", () => {
    expect(filenameFor("///", "json", new Date("2026-09-19T00:00:00Z")))
      .toBe("study-2026-09-19.json");
  });
});
