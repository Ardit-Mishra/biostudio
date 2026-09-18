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
    """Hash the canonical decision inputs so a later replay can detect drift."""
    payload = {
        "study_id": study_id,
        "evidence": [record.model_dump(mode="json") for record in evidence],
        "model_assessments": model_assessments,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
