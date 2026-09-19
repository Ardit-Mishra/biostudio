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
SourceName = Literal[
    "bindingdb", "chembl", "europe_pmc", "openalex", "open_targets",
    "pubchem", "pubmed", "uniprot",
]


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
    source_title: ShortText | None = None
    excerpt: ExcerptText | None = None
    structured_record: dict[str, Any] | None = None
    assay_context: AssayContext | None = None
    outcome_direction: Literal["supports", "contradicts", "unknown"] = "unknown"
    #: Why this record points the way it does, in the operator's own words.
    #: A direction is an assertion about the evidence, and this product does not
    #: accept an unjustified assertion anywhere else -- a record may not say
    #: "contradicts" while staying silent about what in it contradicts.
    direction_rationale: ClaimText | None = None

    @model_validator(mode="after")
    def has_retained_support(self) -> "EvidenceRecord":
        if not self.excerpt and not self.structured_record:
            raise ValueError("EvidenceRecord requires a structured_record or excerpt")
        return self

    @model_validator(mode="after")
    def a_direction_must_be_justified(self) -> "EvidenceRecord":
        """A stated direction carries a reason; an undirected record need not.

        The compiler turns opposing directions into a hold, so the direction is
        the single field with the most influence on the recommendation. Letting
        it be set from a dropdown with no recorded reasoning would put the least
        justified value in the most load-bearing place.
        """
        if self.outcome_direction != "unknown" and not self.direction_rationale:
            raise ValueError(
                "direction_rationale is required when outcome_direction is "
                "'supports' or 'contradicts'"
            )
        return self


class SourceArtifact(BaseModel):
    """A source result retained before an operator turns it into a study claim."""

    model_config = ConfigDict(extra="forbid")

    citation: Citation
    title: ShortText
    excerpt: ExcerptText | None = None
    structured_record: dict[str, Any] = Field(min_length=1)


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
