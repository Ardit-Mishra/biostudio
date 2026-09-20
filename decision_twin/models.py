"""Typed contracts for evidence-aware research decisions.

These models deliberately capture what a source said and how it was measured;
they do not treat an LLM narrative as evidence on its own.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from typing_extensions import Annotated


ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
ClaimText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4_000)]
ExcerptText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2_000)]
#: Assay conditions are free-form by nature (buffer, temperature, pre-incubation),
#: so the key and the value are both operator text. Bounding them keeps an
#: unbounded map out of every record, every digest and every exported dossier.
ConditionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
MAX_CONDITIONS = 24
#: A structured record is whatever a source returned, so its shape is not ours
#: to fix. Its cost is: a deeply nested or enormous record is carried through
#: comparison, hashing and export, and is echoed back on every read.
MAX_RECORD_DEPTH = 6
MAX_RECORD_BYTES = 32_000
SourceName = Literal[
    "bindingdb", "chembl", "europe_pmc", "openalex", "open_targets",
    "pubchem", "pubmed", "uniprot",
]


def _bounded_record(value: dict[str, Any] | None, *, field: str) -> dict[str, Any] | None:
    """Reject a structured record that is too deep or too large to carry safely.

    Depth first, because a cyclic-looking or deeply nested payload is cheap to
    send and expensive to serialize -- and the size check below has to serialize
    it to measure it. Measuring the JSON encoding rather than len() of the dict
    is the point: a two-key dict can still hold a megabyte of text.
    """
    if value is None:
        return None

    def depth(node: Any, level: int = 1) -> int:
        if level > MAX_RECORD_DEPTH:
            return level
        if isinstance(node, dict):
            return max((depth(v, level + 1) for v in node.values()), default=level)
        if isinstance(node, list):
            return max((depth(v, level + 1) for v in node), default=level)
        return level

    if depth(value) > MAX_RECORD_DEPTH:
        raise ValueError(f"{field} nests deeper than {MAX_RECORD_DEPTH} levels")
    try:
        encoded = json.dumps(value, default=str)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} is not JSON-serializable") from exc
    if len(encoded.encode("utf-8")) > MAX_RECORD_BYTES:
        raise ValueError(f"{field} exceeds {MAX_RECORD_BYTES} bytes")
    return value


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
    conditions: dict[ConditionText, ConditionText] = Field(
        default_factory=dict, max_length=MAX_CONDITIONS
    )


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
    def structured_record_is_bounded(self) -> "EvidenceRecord":
        _bounded_record(self.structured_record, field="structured_record")
        return self

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

    @model_validator(mode="after")
    def structured_record_is_bounded(self) -> "SourceArtifact":
        _bounded_record(self.structured_record, field="structured_record")
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
