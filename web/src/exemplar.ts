import type { EvidenceRecord } from "@/lib/decision-twin";

/**
 * The public exemplar study: EGFR in non-small-cell lung cancer.
 *
 * Every citation here is a real Europe PMC record, retrieved through this
 * application's own /v2/sources/europe-pmc/search connector on 2026-09-18. The
 * plan's scope discipline is explicit that the exemplar must use verified
 * public records rather than fabricated biology, so the claims are written to
 * say no more than the cited record's own title and abstract support.
 *
 * It is chosen because it produces a `hold` honestly. Osimertinib has genuine
 * clinical support in EGFR-mutant NSCLC *and* a large literature on acquired
 * resistance in T790M-positive disease. Those two bodies of evidence are about
 * the same target and point opposite ways, which is exactly the assay-context
 * conflict the compiler is built to refuse to average away — and the case the
 * product exists to demonstrate.
 */

export const EXEMPLAR_STUDY_ID = "egfr-nsclc-osimertinib-2026-09";

export const EXEMPLAR_TITLE = "EGFR in non-small-cell lung cancer";
export const EXEMPLAR_QUESTION =
  "Is the public evidence strong enough to advance an osimertinib-directed step in EGFR-mutant NSCLC?";

const RETRIEVED = "2026-09-18T17:51:39Z";
const EGFR = "ENSG00000146648";

export const EXEMPLAR_EVIDENCE: EvidenceRecord[] = [
  {
    id: "ev-clinical-consolidation",
    claim:
      "Osimertinib consolidation after definitive chemoradiotherapy was studied in unresectable stage III EGFR-mutated NSCLC.",
    citation: {
      source: "europe_pmc",
      source_id: "42714840",
      retrieved_at: RETRIEVED,
    },
    source_title:
      "Osimertinib After Definitive Chemoradiotherapy in Unresectable Stage III EGFR-Mutated NSCLC.",
    excerpt:
      "Osimertinib After Definitive Chemoradiotherapy in Unresectable Stage III EGFR-mutated NSCLC.",
    assay_context: {
      target_id: EGFR,
      biological_system: "human",
      readout: "progression_free_survival",
      unit: "months",
      genetic_context: "EGFR-mutated (exon 19del / L858R)",
      conditions: { line_of_therapy: "consolidation", design: "randomized_trial" },
    },
    outcome_direction: "supports",
  },
  {
    id: "ev-cellular-t790m-resistance",
    claim:
      "Acquired resistance mechanisms to osimertinib are reported in EGFR T790M-positive lung adenocarcinoma.",
    citation: {
      source: "europe_pmc",
      source_id: "PMC13585410",
      retrieved_at: RETRIEVED,
    },
    source_title:
      "Mechanisms of acquired resistance to osimertinib in EGFR T790M-Positive lung adenocarcinoma.",
    excerpt:
      "Mechanisms of acquired resistance to osimertinib in EGFR T790M-Positive lung adenocarcinoma.",
    assay_context: {
      target_id: EGFR,
      biological_system: "cell_line",
      readout: "viability_ic50",
      unit: "nM",
      genetic_context: "EGFR T790M",
      conditions: { exposure: "chronic", selection: "acquired_resistance" },
    },
    outcome_direction: "contradicts",
  },
  {
    id: "ev-cellular-tead-resistance",
    claim:
      "TEAD upregulation is reported to promote osimertinib resistance in NSCLC models.",
    citation: {
      source: "europe_pmc",
      source_id: "42705393",
      retrieved_at: RETRIEVED,
    },
    source_title: "TEAD upregulation promotes osimertinib resistance in NSCLC.",
    excerpt: "TEAD upregulation promotes osimertinib resistance in NSCLC.",
    assay_context: {
      target_id: EGFR,
      biological_system: "cell_line",
      readout: "viability_ic50",
      unit: "nM",
      genetic_context: "EGFR T790M",
      conditions: { exposure: "chronic", selection: "acquired_resistance" },
    },
    outcome_direction: "contradicts",
  },
];
