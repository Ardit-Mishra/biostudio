/**
 * A decision record has to state the method, not the intention.
 *
 * The exported dossier used to say "public sources searched for `KRAS G12C
 * pancreatic`". That is what the reader typed. What actually ran was
 * `(KRAS G12C pancreatic) AND PUB_TYPE:"Randomized Controlled Trial"`, and the
 * five records shown were five of six -- or, on OpenAlex, five of 5,974. None
 * of that reached the page a reviewer would be handed, so the search could not
 * be reproduced and the synthesis had no denominator.
 *
 * These tests pin the three facts that were missing: the executed query, the
 * study design, and the coverage.
 */

import { describe, expect, it } from "vitest";

import { toJson, toMarkdown, type DecisionRecordInput, type SearchProvenance } from "../src/lib/decision-record";
import type { Compilation } from "../src/lib/decision-twin";

const compilation: Compilation = {
  study_id: "study-kras",
  status: "insufficient_evidence",
  reasons: ["Nothing source-backed supports a step either way."],
  comparisons: [],
  snapshot_digest: "0".repeat(64),
  evidence_count: 0,
  assay_translation_map: {
    lanes: [
      { stage: "biochemical", status: "missing", evidence_ids: [], gaps: ["No biochemical evidence was supplied."] },
      { stage: "cellular", status: "missing", evidence_ids: [], gaps: ["No cellular evidence was supplied."] },
      { stage: "in_vivo", status: "missing", evidence_ids: [], gaps: ["No in vivo evidence was supplied."] },
      { stage: "human", status: "missing", evidence_ids: [], gaps: ["No human evidence was supplied."] },
      { stage: "unclassified", status: "missing", evidence_ids: [], gaps: [] },
    ],
  },
};

const provenance: SearchProvenance = {
  source: "Europe PMC",
  executedQuery: '(KRAS G12C pancreatic) AND PUB_TYPE:"Randomized Controlled Trial"',
  studyDesignLabel: "Randomized controlled trial",
  studyDesignCannotSupport:
    "Generalisation to patients who would not have met the eligibility criteria.",
  totalHits: 6,
  returned: 5,
};

function input(overrides: Partial<DecisionRecordInput> = {}): DecisionRecordInput {
  return {
    studyId: "study-kras",
    title: "KRAS G12C pancreatic",
    question: "Is the public evidence consistent enough to justify the next step?",
    searchQuery: "KRAS G12C pancreatic",
    isExample: false,
    evidence: [],
    compilation,
    generatedAt: new Date("2026-09-20T00:00:00Z"),
    searchProvenance: provenance,
    ...overrides,
  };
}

describe("markdown export", () => {
  it("states the query that actually ran, not the one that was typed", () => {
    const md = toMarkdown(input());
    expect(md).toContain('(KRAS G12C pancreatic) AND PUB_TYPE:"Randomized Controlled Trial"');
    expect(md).toContain("Europe PMC");
  });

  it("records the chosen design and what it cannot support", () => {
    const md = toMarkdown(input());
    expect(md).toContain("Randomized controlled trial");
    expect(md).toContain("Cannot support:");
    expect(md).toContain("eligibility criteria");
  });

  it("gives the denominator and names what was left unscreened", () => {
    const md = toMarkdown(input());
    expect(md).toContain("5 of 6");
    expect(md).toMatch(/1 matching record was not screened/);
  });

  it("says so plainly when every matching record was screened", () => {
    const md = toMarkdown(input({ searchProvenance: { ...provenance, totalHits: 5, returned: 5 } }));
    expect(md).toContain("All matching records were screened.");
  });

  it("distinguishes an unreported total from a total of zero", () => {
    const md = toMarkdown(input({ searchProvenance: { ...provenance, totalHits: null } }));
    expect(md).toContain("does not report a total");
    expect(md).not.toContain("of 0");
  });

  it("still produces a record when no search was run", () => {
    const md = toMarkdown(input({ searchProvenance: undefined, searchQuery: "" }));
    expect(md).toContain("Records supplied directly to the study.");
    expect(md).not.toContain("Coverage.");
  });
});

describe("json export", () => {
  it("carries every provenance field a reviewer would ask for", () => {
    const parsed = JSON.parse(toJson(input()));
    const meta = parsed.record ?? parsed;
    const flat = JSON.stringify(meta);
    expect(flat).toContain("search_executed");
    expect(flat).toContain('AND PUB_TYPE:\\"Randomized Controlled Trial\\"');
    expect(flat).toContain("study_design");
    expect(flat).toContain("total_hits");
    expect(flat).toContain("records_screened");
  });

  it("nulls the provenance fields rather than omitting them when absent", () => {
    const parsed = JSON.parse(toJson(input({ searchProvenance: undefined })));
    const flat = JSON.stringify(parsed);
    expect(flat).toContain("search_executed");
    expect(flat).toContain("total_hits");
  });
});
