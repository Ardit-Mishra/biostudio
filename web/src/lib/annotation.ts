import type {
  EvidenceRecord,
  OutcomeDirection,
  SourceArtifact,
} from "@/lib/decision-twin";

/**
 * The human-authored context that turns a retained source artifact into a
 * candidate evidence record. None of these values may be inferred from a
 * title, abstract, or model output: this is the operator's interpretation of
 * what the source actually measured.
 */
export interface EvidenceAnnotationDraft {
  id: string;
  claim: string;
  target_id: string;
  biological_system: string;
  readout: string;
  unit: string;
  genetic_context?: string;
  outcome_direction: OutcomeDirection;
}

const REQUIRED_FIELDS: Array<keyof Omit<EvidenceAnnotationDraft, "outcome_direction" | "genetic_context">> = [
  "id",
  "claim",
  "target_id",
  "biological_system",
  "readout",
  "unit",
];

/** Short display copy for source-result scanning; the artifact remains whole. */
export function excerptPreview(excerpt: string | null | undefined, limit = 420): string | null {
  if (!excerpt) return null;
  const text = excerpt.trim();
  if (text.length <= limit) return text;
  return `${text.slice(0, Math.max(0, limit - 1))}…`;
}

/** A source artifact is not decision evidence until this returns true. */
export function isAnnotationReady(draft: EvidenceAnnotationDraft): boolean {
  return REQUIRED_FIELDS.every((field) => draft[field].trim().length > 0);
}

/**
 * Compose a decision input from a source record and an explicit annotation.
 *
 * This does not write, upload, or execute anything. Its only job is to keep
 * sourced material distinct from the operator's claim until a study compiler
 * receives the resulting record.
 */
export function createEvidenceFromAnnotation(
  artifact: SourceArtifact,
  draft: EvidenceAnnotationDraft,
): EvidenceRecord {
  if (!isAnnotationReady(draft)) {
    throw new Error("Add a claim, target, biological system, readout, and unit before using this source as evidence.");
  }

  return {
    id: draft.id.trim(),
    claim: draft.claim.trim(),
    citation: artifact.citation,
    source_title: artifact.title,
    excerpt: artifact.excerpt,
    structured_record: artifact.structured_record,
    assay_context: {
      target_id: draft.target_id.trim(),
      biological_system: draft.biological_system.trim(),
      readout: draft.readout.trim(),
      unit: draft.unit.trim(),
      genetic_context: draft.genetic_context?.trim() || null,
    },
    outcome_direction: draft.outcome_direction,
  };
}
