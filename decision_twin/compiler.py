"""Deterministic Decision Twin compilation and provenance hashing."""

from __future__ import annotations

import hashlib
import json
from itertools import combinations
from typing import Any

from decision_twin.models import AssayComparison, DecisionOutcome, EvidenceRecord
from decision_twin.normalization import compare_evidence


def compile_decision(
    *, study_id: str, evidence: list[EvidenceRecord], model_assessments: list[dict[str, Any]]
) -> DecisionOutcome:
    """Return a conservative research recommendation from validated evidence.

    A model assessment can add context but can never erase a recorded conflict.
    The caller must separately decide which research action, if any, to take.
    """
    comparisons = [compare_evidence(left, right) for left, right in combinations(evidence, 2)]
    conflicts = [comparison for comparison in comparisons if comparison.relation == "conflicting"]
    if conflicts:
        return DecisionOutcome(
            study_id=study_id,
            status="hold",
            reasons=["Evidence conflict detected; resolve the incompatible observations before advancing."],
            comparisons=comparisons,
        )

    supporting_records = [record for record in evidence if record.outcome_direction == "supports"]
    if not supporting_records:
        return DecisionOutcome(
            study_id=study_id,
            status="insufficient_evidence",
            reasons=["No source-backed supporting observation is available for this research decision."],
            comparisons=comparisons,
        )

    return DecisionOutcome(
        study_id=study_id,
        status="advance",
        reasons=["Source-backed supporting evidence is present and no recorded conflict was found."],
        comparisons=comparisons,
    )


def snapshot_digest(
    *, study_id: str, evidence: list[EvidenceRecord], model_assessments: list[dict[str, Any]]
) -> str:
    """Hash the canonical decision inputs so a later replay can detect drift.

    `sort_keys` canonicalises the inside of each object but not the order of
    the lists holding them, so the same study re-posted with its evidence in a
    different order used to hash differently. That is a false positive in the
    one place a false positive is most expensive: the digest exists to say "the
    inputs changed", and annotating records in a different order is not a
    change. Both lists are therefore ordered by their own canonical encoding
    before hashing, which is stable across processes and runs.
    """

    def canonical_of(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    payload = {
        "study_id": study_id,
        "evidence": sorted(
            (record.model_dump(mode="json") for record in evidence), key=canonical_of
        ),
        "model_assessments": sorted(model_assessments, key=canonical_of),
    }
    return hashlib.sha256(canonical_of(payload).encode("utf-8")).hexdigest()
