import {
  RELATION_LABEL,
  STAGE_LABEL,
  TRANSLATION_STAGES,
  type AssayMapLane,
  type Compilation,
  type EvidenceRecord, citationUrl,} from "@/lib/decision-twin";

/**
 * The Decision Record — the artifact a study exists to produce.
 *
 * Until this file, BioStudio assembled cited, assay-aware evidence, refused to
 * overclaim, printed a replayable digest, and then stranded all of it in a
 * browser tab. A researcher could not take the verdict to a meeting, attach it
 * to a go/no-go memo, put the citations in Zotero, or hand a colleague anything
 * to check. A decision-integrity system that produces no record is the one
 * contradiction the product cannot afford.
 *
 * What the formats are for, and why these four:
 *
 *   Markdown  the dossier a human reads, and the print/PDF source. Drug
 *             discovery's own name for this is a target dossier: the document
 *             that "comprehensively presents all the information experts need
 *             in the decision-making process".
 *   CSV       the evidence table, because that is what every systematic-review
 *             tool in this space exports and what a reviewer opens in Excel.
 *   RIS       the citations, because that is what Zotero, EndNote and Mendeley
 *             import. Exporting claims without exporting citations would make
 *             the references un-checkable, which is the opposite of the point.
 *   JSON      the replay artifact. The snapshot digest claims a study can be
 *             re-run and compared; that claim is empty unless the exact inputs
 *             can leave the browser.
 *
 * Reporting-standard debts this pays, from PRISMA 2020 and GRADE:
 *   - the search that produced the evidence is stated, not implied
 *   - the tool and its version are disclosed, because automated retrieval has
 *     to be declared alongside the human judgement
 *   - every decisive comparison carries the reason it was decisive
 *   - absence is reported as explicitly as presence
 */

export interface DecisionRecordInput {
  studyId: string;
  title: string;
  question: string;
  /** What was typed into the source search, if anything. PRISMA wants this. */
  searchQuery: string;
  /**
   * The method, as opposed to the intent.
   *
   * `searchQuery` is what the reader typed; `searchProvenance` is what the
   * source was actually asked, how many it said existed, and how many of those
   * were looked at. A record that states only the first reads as a methods
   * section but cannot be reproduced from: the design filter is invisible, and
   * five of six and five of five thousand look identical.
   */
  searchProvenance?: SearchProvenance;
  isExample: boolean;
  evidence: EvidenceRecord[];
  compilation: Compilation;
  generatedAt?: Date;
}

export interface SearchProvenance {
  /** The source that was queried, for the reader who has to repeat it. */
  source: string;
  /** The query string as the source received it, design filter included. */
  executedQuery: string;
  /** The chosen level of evidence, and what it cannot support. */
  studyDesignLabel?: string;
  studyDesignCannotSupport?: string;
  /** What the source said exists; null when a source reports no total. */
  totalHits: number | null;
  returned: number;
}

function coverageSentence(p: SearchProvenance): string {
  // "Screened" is a claim about a person having read something, and this tool
  // cannot know that. It knows what the source returned. Reporting retrieval
  // as screening would overstate the review in the one document a reviewer
  // reads to judge how thorough it was.
  if (p.totalHits === null) {
    return `${p.returned} record${p.returned === 1 ? "" : "s"} retrieved; this source does not report a total.`;
  }
  const unseen = Math.max(0, p.totalHits - p.returned);
  const tail = unseen > 0
    ? ` ${unseen} matching record${unseen === 1 ? " was" : "s were"} not retrieved.`
    : " All matching records were retrieved.";
  return `${p.returned} of ${p.totalHits} matching record${p.totalHits === 1 ? "" : "s"} retrieved.${tail}`;
}

const TOOL = "BioStudio Decision Twin";

const STATUS_SENTENCE: Record<Compilation["status"], string> = {
  advance: "Advance — source-backed support is present and no conflict was recorded.",
  hold: "Hold — incompatible observations must be resolved before advancing.",
  insufficient_evidence:
    "Insufficient evidence — nothing source-backed supports a step either way.",
};

function isoDay(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function laneFor(lanes: AssayMapLane[], stage: string): AssayMapLane | undefined {
  return lanes.find((lane) => lane.stage === stage);
}

/**
 * Delegate to the one resolver, rather than keeping a second copy here.
 *
 * There were two. This one never learned about OpenAlex, so every OpenAlex
 * record exported to Markdown, CSV and RIS carried an empty link while the
 * same citation resolved correctly on screen. Two resolvers for one fact will
 * always drift; there is now one.
 */
function citationUrlFor(record: EvidenceRecord): string {
  return citationUrl(record.citation) ?? "";
}

// ---------------------------------------------------------------- Markdown ---

export function toMarkdown(input: DecisionRecordInput): string {
  const at = input.generatedAt ?? new Date();
  const { compilation: c, evidence } = input;
  const lanes = c.assay_translation_map.lanes;
  const decisive = c.comparisons.filter(
    (x) => x.relation === "conflicting" || x.relation === "non_comparable",
  );

  const lines: string[] = [];
  lines.push(`# Decision Record — ${input.title}`);
  lines.push("");
  lines.push(`**Study** \`${input.studyId}\`  `);
  lines.push(`**Compiled** ${isoDay(at)}  `);
  lines.push(`**Snapshot digest** \`${c.snapshot_digest}\``);
  if (input.isExample) {
    lines.push("");
    lines.push(
      "> This is the published worked example, not a study assembled by the reader.",
    );
  }
  lines.push("");
  lines.push("## Question");
  lines.push("");
  lines.push(input.question);
  lines.push("");

  lines.push("## Recommendation");
  lines.push("");
  lines.push(`**${STATUS_SENTENCE[c.status]}**`);
  lines.push("");
  for (const reason of c.reasons) lines.push(`- ${reason}`);
  lines.push("");
  lines.push(
    "This is a research recommendation about what to investigate next. It is not " +
      "a clinical, regulatory or purchasing decision, and it is derived only from " +
      "the records listed below.",
  );
  lines.push("");

  lines.push("## Assay translation");
  lines.push("");
  lines.push("| Stage | Status | Records | Gap |");
  lines.push("|---|---|---|---|");
  for (const stage of TRANSLATION_STAGES) {
    const lane = laneFor(lanes, stage);
    lines.push(
      `| ${STAGE_LABEL[stage]} | ${lane?.status ?? "missing"} | ${lane?.evidence_ids.length ?? 0} | ${lane?.gaps[0] ?? "—"} |`,
    );
  }
  lines.push("");
  lines.push(
    "Evidence does not automatically carry from a purified target to a cell to " +
      "an animal to a person. A stage marked missing has no retained observation; " +
      "it is not weak evidence, it is none.",
  );
  lines.push("");

  lines.push(`## Evidence (${evidence.length})`);
  lines.push("");
  for (const record of evidence) {
    lines.push(`### ${record.id}`);
    lines.push("");
    lines.push(`**Claim.** ${record.claim}`);
    lines.push("");
    if (record.source_title) lines.push(`**Source title.** ${record.source_title}`);
    lines.push(
      `**Citation.** ${record.citation.source.replace(/_/g, " ")} ${record.citation.source_id} — ${citationUrlFor(record)}`,
    );
    lines.push(`**Retrieved.** ${record.citation.retrieved_at.slice(0, 10)}`);
    lines.push(`**Direction.** ${record.outcome_direction}`);
    if (record.direction_rationale) {
      lines.push(`**Why.** ${record.direction_rationale}`);
    }
    const ctx = record.assay_context;
    if (ctx) {
      lines.push(
        `**Assay context.** target ${ctx.target_id}; system ${ctx.biological_system}; ` +
          `readout ${ctx.readout}; unit ${ctx.unit}` +
          (ctx.genetic_context ? `; genetic context ${ctx.genetic_context}` : "") +
          (ctx.conditions && Object.keys(ctx.conditions).length
            ? `; ${Object.entries(ctx.conditions).map(([k, v]) => `${k} ${v}`).join("; ")}`
            : ""),
      );
    }
    if (record.excerpt) {
      lines.push("");
      lines.push(`> ${record.excerpt}`);
    }
    lines.push("");
  }

  lines.push("## Integrity checks");
  lines.push("");
  lines.push(`${c.comparisons.length} pairwise comparisons were made across ${c.evidence_count} records.`);
  lines.push("");
  if (decisive.length === 0) {
    lines.push("No comparison was conflicting or non-comparable.");
  } else {
    lines.push("| Left | Right | Relation | Reason |");
    lines.push("|---|---|---|---|");
    for (const x of decisive) {
      lines.push(
        `| ${x.left_evidence_id} | ${x.right_evidence_id} | ${RELATION_LABEL[x.relation]} | ${x.reason} |`,
      );
    }
    lines.push("");
    lines.push(
      "Every decisive comparison is listed in full. Agreeing pairs are counted " +
        "above but not enumerated; none of them changed the recommendation.",
    );
  }
  lines.push("");

  lines.push("## How this was produced");
  lines.push("");
  lines.push(`- **Tool.** ${TOOL}`);
  lines.push(
    `- **Retrieval.** ${input.searchQuery ? `Public sources searched for \`${input.searchQuery}\`.` : "Records supplied directly to the study."} Retrieval never promotes a record to evidence; an operator supplied every claim and assay context below.`,
    ...(input.searchProvenance
      ? [
          `- **Search executed.** \`${input.searchProvenance.executedQuery}\` against ${input.searchProvenance.source}.`,
          ...(input.searchProvenance.studyDesignLabel
            ? [`- **Study design.** ${input.searchProvenance.studyDesignLabel}.${input.searchProvenance.studyDesignCannotSupport ? ` Cannot support: ${input.searchProvenance.studyDesignCannotSupport}` : ""}`]
            : []),
          `- **Coverage.** ${coverageSentence(input.searchProvenance)}`,
        ]
      : []),
  );
  lines.push(
    "- **Comparison rule.** Two records are comparable only when target, biological system, readout, unit and genetic context agree. Opposing directions on the same target are recorded as conflicting and force a hold.",
  );
  lines.push(
    `- **Replay.** Re-compiling the exported JSON reproduces snapshot digest \`${c.snapshot_digest}\`. A changed source produces a different digest, which is the study diff.`,
  );
  lines.push("");
  lines.push(
    "Educational and research use. BioStudio reports whether public evidence is " +
      "consistent enough to justify a next research step; it does not discover " +
      "drugs, replace experimental validation, or make clinical recommendations.",
  );
  lines.push("");
  return lines.join("\n");
}

// -------------------------------------------------------------------- CSV ---

function csvCell(value: unknown): string {
  const text = value === null || value === undefined ? "" : String(value);
  // Quote always: the fields carry commas, quotes and newlines from abstracts.
  return `"${text.replace(/"/g, '""')}"`;
}

export function toCsv(input: DecisionRecordInput): string {
  const header = [
    "study_id", "evidence_id", "direction", "direction_rationale", "claim", "source_title", "source",
    "source_id", "source_url", "retrieved", "target_id", "biological_system",
    "readout", "unit", "genetic_context", "excerpt",
  ];
  const rows = input.evidence.map((r) => {
    const ctx = r.assay_context;
    return [
      input.studyId, r.id, r.outcome_direction, r.direction_rationale ?? "", r.claim, r.source_title ?? "",
      r.citation.source, r.citation.source_id, citationUrlFor(r),
      r.citation.retrieved_at, ctx?.target_id ?? "", ctx?.biological_system ?? "",
      ctx?.readout ?? "", ctx?.unit ?? "", ctx?.genetic_context ?? "", r.excerpt ?? "",
    ].map(csvCell).join(",");
  });
  // CRLF and a UTF-8 BOM so Excel opens accented text correctly on Windows.
  return "﻿" + [header.map(csvCell).join(","), ...rows].join("\r\n") + "\r\n";
}

// -------------------------------------------------------------------- RIS ---

/**
 * RIS for the citations, so a reader can check them in their own library.
 * JOUR is used for literature; a compound or target record is a database
 * entry, which RIS spells DATA.
 */
/** RIS is line-oriented: a newline inside a field corrupts the record. */
const NEWLINES = new RegExp(String.fromCharCode(13) + '?' + String.fromCharCode(10), 'g');

export function toRis(input: DecisionRecordInput): string {
  const out: string[] = [];
  for (const r of input.evidence) {
    const literature = r.citation.source === "europe_pmc";
    out.push(`TY  - ${literature ? "JOUR" : "DATA"}`);
    out.push(`TI  - ${r.source_title ?? r.claim}`);
    if (literature && /^\d+$/.test(r.citation.source_id)) {
      out.push(`AN  - ${r.citation.source_id}`);
    }
    out.push(`UR  - ${citationUrlFor(r)}`);
    out.push(`DB  - ${r.citation.source.replace(/_/g, " ")}`);
    out.push(`ID  - ${r.citation.source_id}`);
    if (r.excerpt) out.push(`AB  - ${r.excerpt.replace(NEWLINES, " ")}`);
    out.push(`N1  - Retained in study ${input.studyId} as ${r.outcome_direction}: ${r.claim}`);
    if (r.direction_rationale) {
      out.push(
        `N1  - Reason for direction: ${r.direction_rationale.replace(NEWLINES, " ")}`,
      );
    }
    out.push(`Y2  - ${r.citation.retrieved_at.slice(0, 10).replace(/-/g, "/")}`);
    out.push("ER  - ");
    out.push("");
  }
  return out.join("\r\n");
}

// ------------------------------------------------------------------- JSON ---

/** The replay artifact: exactly what the compiler was given, plus what it said. */
export function toJson(input: DecisionRecordInput): string {
  return JSON.stringify(
    {
      tool: TOOL,
      generated_at: (input.generatedAt ?? new Date()).toISOString(),
      study_id: input.studyId,
      title: input.title,
      question: input.question,
      search_query: input.searchQuery || null,
      search_executed: input.searchProvenance?.executedQuery ?? null,
      search_source: input.searchProvenance?.source ?? null,
      study_design: input.searchProvenance?.studyDesignLabel ?? null,
      study_design_cannot_support: input.searchProvenance?.studyDesignCannotSupport ?? null,
      total_hits: input.searchProvenance?.totalHits ?? null,
      records_returned: input.searchProvenance?.returned ?? null,
      is_worked_example: input.isExample,
      // The exact request body, so re-posting it reproduces the digest.
      compile_request: { study_id: input.studyId, evidence: input.evidence, model_assessments: [] },
      compilation: input.compilation,
    },
    null,
    2,
  );
}

// --------------------------------------------------------------- download ---

export function filenameFor(studyId: string, extension: string, at = new Date()): string {
  const safe = studyId.replace(/[^a-zA-Z0-9._-]+/g, "-").replace(/^-+|-+$/g, "") || "study";
  return `${safe}-${isoDay(at)}.${extension}`;
}

export function downloadText(filename: string, text: string, mime: string): void {
  const blob = new Blob([text], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  // Revoking immediately can cancel the download in some browsers.
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
