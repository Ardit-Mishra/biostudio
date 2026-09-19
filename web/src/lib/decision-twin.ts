/**
 * Typed client for the Decision Twin API.
 *
 * These types mirror `decision_twin/models.py` and `decision_twin/assay_map.py`
 * exactly. They are written as closed unions rather than `string` on purpose:
 * if the Python side gains a relation or a lane status, the compiler should
 * fail here rather than the UI silently rendering an unknown state as a
 * neutral chip. Provenance is the product, so an unrecognised status is a bug,
 * not something to paper over at render time.
 */

export type SourceName = "europe_pmc" | "open_targets" | "chembl";

export type AssayStage =
  | "biochemical"
  | "cellular"
  | "in_vivo"
  | "human"
  | "unclassified";

export type LaneStatus =
  | "supporting"
  | "contradicting"
  | "conflicting"
  | "inconclusive"
  | "missing"
  | "unclassified";

export type Relation =
  | "direct"
  | "supportive"
  | "inferred"
  | "non_comparable"
  | "conflicting";

export type DecisionStatus = "advance" | "hold" | "insufficient_evidence";

export type OutcomeDirection = "supports" | "contradicts" | "unknown";

export interface Citation {
  source: SourceName;
  source_id: string;
  retrieved_at: string;
}

export interface AssayContext {
  target_id: string;
  biological_system: string;
  readout: string;
  unit: string;
  genetic_context?: string | null;
  conditions?: Record<string, string>;
}

export interface EvidenceRecord {
  id: string;
  claim: string;
  citation: Citation;
  excerpt?: string | null;
  structured_record?: Record<string, unknown> | null;
  assay_context?: AssayContext | null;
  outcome_direction: OutcomeDirection;
}

export interface AssayComparison {
  left_evidence_id: string;
  right_evidence_id: string;
  relation: Relation;
  reason: string;
}

export interface AssayMapLane {
  stage: AssayStage;
  status: LaneStatus;
  evidence_ids: string[];
  gaps: string[];
}

export interface Compilation {
  study_id: string;
  status: DecisionStatus;
  reasons: string[];
  comparisons: AssayComparison[];
  snapshot_digest: string;
  evidence_count: number;
  assay_translation_map: { lanes: AssayMapLane[] };
}

export interface SourceArtifact {
  citation: Citation;
  title: string;
  excerpt?: string | null;
  structured_record: Record<string, unknown>;
}

/**
 * The stages the map walks, in translation order. `unclassified` is held back
 * deliberately: it is a catch-all bucket, not a step in the biological chain,
 * so drawing it inline would imply evidence translates *through* it.
 */
export const TRANSLATION_STAGES: readonly AssayStage[] = [
  "biochemical",
  "cellular",
  "in_vivo",
  "human",
] as const;

export const STAGE_LABEL: Record<AssayStage, string> = {
  biochemical: "Biochemical",
  cellular: "Cellular",
  in_vivo: "In vivo",
  human: "Human",
  unclassified: "Unclassified",
};

/** What each stage actually measures — shown so the chain reads as biology. */
export const STAGE_MEANING: Record<AssayStage, string> = {
  biochemical: "Isolated target, purified system",
  cellular: "Target in a living cell",
  in_vivo: "Target in a whole animal",
  human: "Target in people",
  unclassified: "No biological system recorded",
};

export const RELATION_LABEL: Record<Relation, string> = {
  direct: "Direct",
  supportive: "Supportive",
  inferred: "Inferred",
  non_comparable: "Not comparable",
  conflicting: "Conflicting",
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    // Surface the API's own error shape rather than a generic message: this
    // backend returns {error:{code,message}} and that message is usually the
    // actionable part (a validation failure naming the offending field).
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      detail = payload?.error?.message ?? payload?.detail ?? detail;
    } catch {
      /* response had no JSON body; the status line is all we have */
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export function compileStudy(request: {
  study_id: string;
  evidence: EvidenceRecord[];
  model_assessments?: Record<string, unknown>[];
}): Promise<Compilation> {
  return post<Compilation>("/v2/decision-twins/compile", {
    model_assessments: [],
    ...request,
  });
}

export async function searchEuropePmc(
  query: string,
  limit = 10,
): Promise<SourceArtifact[]> {
  const url = `${API_BASE}/v2/sources/europe-pmc/search?query=${encodeURIComponent(query)}&page_size=${limit}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Europe PMC search failed (${response.status})`);
  const payload = (await response.json()) as { records?: SourceArtifact[] };
  return payload.records ?? [];
}

/** Resolve one ChEMBL compound through the API's fixed identifier route. */
export async function getChEMBLCompound(
  chemblId: string,
): Promise<SourceArtifact[]> {
  const normalizedId = chemblId.trim().toUpperCase();
  const response = await fetch(
    `${API_BASE}/v2/sources/chembl/compounds/${encodeURIComponent(normalizedId)}`,
  );
  if (!response.ok) throw new Error(`ChEMBL lookup failed (${response.status})`);
  const payload = (await response.json()) as { records?: SourceArtifact[] };
  return payload.records ?? [];
}

/** Build a citation URL for a resolved source id. Never guess a host. */
export function citationUrl(citation: Citation): string | null {
  if (citation.source === "europe_pmc") {
    const id = citation.source_id;
    return id.startsWith("PMC")
      ? `https://europepmc.org/article/PMC/${id}`
      : `https://europepmc.org/article/MED/${id}`;
  }
  if (citation.source === "open_targets") {
    return `https://platform.opentargets.org/target/${citation.source_id}`;
  }
  if (citation.source === "chembl") {
    return `https://www.ebi.ac.uk/chembl/explore/compound/${citation.source_id}`;
  }
  return null;
}
