/**
 * The exports carry text a stranger wrote into other people's tools.
 *
 * Every field below originates in a public record or in an operator's own
 * annotation, and all three exports hand it to software that interprets what
 * it is given. The CSV says on its own button that it opens in Excel; the RIS
 * says it imports into Zotero and EndNote. So the question for this file is
 * not whether the text round-trips, but whether it can make the receiving
 * program do something other than display it.
 *
 * Three defects this pins:
 *
 * Quoting a CSV cell does not stop Excel evaluating it. A value opening with
 * `=`, `+`, `-` or `@` is read as a formula even inside quotes, so a claim
 * could arrive as executable spreadsheet content rather than a quotation.
 *
 * RIS is line-oriented. A newline inside a title or a claim starts a line no
 * tag introduces, and a line that happens to look like `ER  -` ends the record
 * early. The abstract and the rationale were normalised; the title and the
 * claim were not.
 *
 * And OpenAlex records were typed `DATA`, so reference managers filed
 * peer-reviewed articles as datasets.
 */

import { describe, expect, it } from "vitest";

import { toCsv, toRis, type DecisionRecordInput, type EvidenceRecord } from "../src/lib/decision-record";
import type { Compilation } from "../src/lib/decision-twin";

const compilation: Compilation = {
  study_id: "s",
  status: "advance",
  reasons: [],
  comparisons: [],
  snapshot_digest: "0".repeat(64),
  evidence_count: 1,
  assay_translation_map: {
    lanes: [
      { stage: "biochemical", status: "missing", evidence_ids: [], gaps: [] },
      { stage: "cellular", status: "missing", evidence_ids: [], gaps: [] },
      { stage: "in_vivo", status: "missing", evidence_ids: [], gaps: [] },
      { stage: "human", status: "supporting", evidence_ids: ["e1"], gaps: [] },
      { stage: "unclassified", status: "missing", evidence_ids: [], gaps: [] },
    ],
  },
};

function evidence(over: Partial<EvidenceRecord> = {}): EvidenceRecord {
  return {
    id: "e1",
    claim: "an ordinary claim",
    citation: { source: "europe_pmc", source_id: "12345678", retrieved_at: "2026-09-20T00:00:00Z" },
    source_title: "An ordinary title",
    excerpt: "an excerpt",
    outcome_direction: "supports",
    direction_rationale: "a reason",
    ...over,
  } as EvidenceRecord;
}

function input(evidences: EvidenceRecord[]): DecisionRecordInput {
  return {
    studyId: "study-1",
    title: "t",
    question: "q",
    searchQuery: "q",
    isExample: false,
    evidence: evidences,
    compilation,
    generatedAt: new Date("2026-09-20T00:00:00Z"),
  };
}

describe("CSV cannot smuggle a formula into a spreadsheet", () => {
  for (const lead of ["=", "+", "-", "@"]) {
    it(`neutralizes a claim opening with "${lead}"`, () => {
      const hostile = `${lead}HYPERLINK("http://x","click")`;
      const csv = toCsv(input([evidence({ claim: hostile })]));
      // The value survives for a reader...
      expect(csv).toContain("HYPERLINK");
      // ...but no cell begins with the character that triggers evaluation.
      const cells = csv.split(/\r\n/).flatMap((line) => line.split('","'));
      const evaluated = cells.filter((c) => /^"?[=+@-]/.test(c.replace(/^"/, "")));
      expect(evaluated).toEqual([]);
    });
  }

  it("leaves ordinary text untouched", () => {
    const csv = toCsv(input([evidence({ claim: "IC50 improved twofold" })]));
    expect(csv).toContain('"IC50 improved twofold"');
    expect(csv).not.toContain("'IC50");
  });

  it("still escapes embedded quotes", () => {
    const csv = toCsv(input([evidence({ claim: 'he said "no"' })]));
    expect(csv).toContain('""no""');
  });
});

describe("RIS stays line-oriented", () => {
  it("a newline in a title cannot start an untagged line", () => {
    const ris = toRis(input([evidence({ source_title: "Line one\nLine two" })]));
    const titleLine = ris.split(/\r\n/).find((l) => l.startsWith("TI  - "));
    expect(titleLine).toBe("TI  - Line one Line two");
    expect(ris.split(/\r\n/).some((l) => l === "Line two")).toBe(false);
  });

  it("a claim cannot inject a record terminator", () => {
    const ris = toRis(input([evidence({ source_title: undefined, claim: "harmless\nER  - \nTY  - BOOK" })]));
    const terminators = ris.split(/\r\n/).filter((l) => l.startsWith("ER  -"));
    expect(terminators).toHaveLength(1);
    expect(ris.split(/\r\n/).filter((l) => l.startsWith("TY  -"))).toHaveLength(1);
  });

  it("every emitted line carries a tag or is blank", () => {
    const ris = toRis(input([evidence({ source_title: "A\nB", claim: "C\nD", excerpt: "E\nF" })]));
    const untagged = ris
      .split(/\r\n/)
      .filter((l) => l.length > 0 && !/^[A-Z][A-Z0-9]  - /.test(l));
    expect(untagged).toEqual([]);
  });
});

describe("RIS types a record by what the lane returns", () => {
  it("OpenAlex works are journal articles, not datasets", () => {
    const ris = toRis(
      input([evidence({ citation: { source: "openalex", source_id: "W123", retrieved_at: "2026-09-20T00:00:00Z" } })]),
    );
    expect(ris).toContain("TY  - JOUR");
    expect(ris).not.toContain("TY  - DATA");
  });

  it("Europe PMC keeps its PMID accession", () => {
    const ris = toRis(input([evidence()]));
    expect(ris).toContain("AN  - 12345678");
  });

  it("a non-literature lane does not claim a PMID accession", () => {
    const ris = toRis(
      input([evidence({ citation: { source: "openalex", source_id: "123456", retrieved_at: "2026-09-20T00:00:00Z" } })]),
    );
    expect(ris).not.toContain("AN  - 123456");
  });

  it("a compound record is still typed DATA", () => {
    const ris = toRis(
      input([evidence({ citation: { source: "chembl", source_id: "CHEMBL25", retrieved_at: "2026-09-20T00:00:00Z" } })]),
    );
    expect(ris).toContain("TY  - DATA");
  });
});
