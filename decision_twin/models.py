"""Typed contracts for evidence-aware research decisions.

These models deliberately capture what a source said and how it was measured;
they do not treat an LLM narrative as evidence on its own.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from typing_extensions import Annotated


ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
ClaimText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4_000)]
ExcerptText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2_000)]
SourceName = Literal["bindingdb", "chembl", "europe_pmc", "open_targets", "pubchem", "pubmed", "uniprot"]


class Citation(BaseModel):
    """A resolved identifier from an approved research source."""

    model_config = ConfigDict(extra="forbid")

    source: SourceName
    source_id: ShortText
    retrieved_at: datetime


class AssayContext(BaseModel):
    """Minimum metadata needed before two assay observations can be compared."""

    model_config = ConfigDict(extra="forbid")

    target_id: ShortText
    biological_system: ShortText
    readout: ShortText
    unit: ShortText
    genetic_context: str | None = Field(default=None, max_length=500)
    conditions: dict[str, str] = Field(default_factory=dict)


class EvidenceRecord(BaseModel):
    """One claim with retained support from a structured record or excerpt."""

    model_config = ConfigDict(extra="forbid")

    id: ShortText
    claim: ClaimText
    citation: Citation
    excerpt: ExcerptText | None = None
    structured_record: dict[str, Any] | None = None
    assay_context: AssayContext | None = None
    outcome_direction: Literal["supports", "contradicts", "unknown"] = "unknown"

    @model_validator(mode="after")
    def has_retained_support(self) -> "EvidenceRecord":
        if not self.excerpt and not self.structured_record:
            raise ValueError("EvidenceRecord requires a structured_record or excerpt")
        return self


class AssayComparison(BaseModel):
    """The defensible relationship between two source-backed observations."""

    model_config = ConfigDict(extra="forbid")

    left_evidence_id: ShortText
    right_evidence_id: ShortText
    relation: Literal["direct", "supportive", "inferred", "non_comparable", "conflicting"]
    reason: ShortText


class DecisionOutcome(BaseModel):
    """A deterministic research recommendation, not a clinical decision."""

    model_config = ConfigDict(extra="forbid")

    study_id: ShortText
    status: Literal["advance", "hold", "insufficient_evidence"]
    reasons: list[ShortText]
    comparisons: list[AssayComparison]


class DecisionTwinRequest(BaseModel):
    """Request body for compiling a source-backed Decision Twin."""

    model_config = ConfigDict(extra="forbid")

    study_id: ShortText
    evidence: list[EvidenceRecord] = Field(min_length=1, max_length=250)
    model_assessments: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
