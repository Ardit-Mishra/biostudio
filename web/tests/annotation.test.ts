import { describe, expect, it } from "vitest";

import {
  createEvidenceFromAnnotation,
  excerptPreview,
  isAnnotationReady,
  type EvidenceAnnotationDraft,
} from "../src/lib/annotation";
import type { SourceArtifact } from "../src/lib/decision-twin";

const artifact: SourceArtifact = {
  citation: {
    source: "europe_pmc",
    source_id: "42714840",
    retrieved_at: "2026-09-18T17:51:39Z",
  },
  title: "A public source record",
  excerpt: "A retained excerpt from the public record.",
  structured_record: { europe_pmc_id: "42714840" },
};

const completeDraft: EvidenceAnnotationDraft = {
  id: "ev-operator-authored",
  claim: "An operator-authored interpretation of the retained source record.",
  target_id: "ENSG00000146648",
  biological_system: "human",
  readout: "progression_free_survival",
  unit: "months",
  outcome_direction: "supports",
};

describe("operator evidence annotation", () => {
  it("keeps source search results scannable without altering retained source text", () => {
    const excerpt = "A source sentence. ".repeat(40);

    expect(excerptPreview(excerpt, 80)).toHaveLength(80);
    expect(excerptPreview(excerpt, 80)).toMatch(/…$/);
    expect(excerpt).toHaveLength(760);
  });

  it("keeps a public source record inert until required operator context exists", () => {
    expect(isAnnotationReady({ ...completeDraft, claim: "" })).toBe(false);
    expect(isAnnotationReady({ ...completeDraft, readout: "" })).toBe(false);
  });

  it("uses an operator-authored claim rather than promoting the source title", () => {
    const evidence = createEvidenceFromAnnotation(artifact, completeDraft);

    expect(evidence.claim).toBe(completeDraft.claim);
    expect(evidence.claim).not.toBe(artifact.title);
    expect(evidence.citation).toEqual(artifact.citation);
    expect(evidence.assay_context).toMatchObject({
      target_id: completeDraft.target_id,
      biological_system: completeDraft.biological_system,
      readout: completeDraft.readout,
      unit: completeDraft.unit,
    });
  });
});
