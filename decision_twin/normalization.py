"""Assay-context comparison with conservative defaults.

The comparator only marks a relationship as direct when the minimum context
matches. Missing context is evidence of uncertainty, never permission to pool.
"""

from __future__ import annotations

from decision_twin.models import AssayComparison, EvidenceRecord


def compare_evidence(left: EvidenceRecord, right: EvidenceRecord) -> AssayComparison:
    """Classify the relationship between two evidence records.

    This is intentionally a small, deterministic policy. More detailed protocol
    harmonization can be added without changing the externally visible labels.
    """
    if left.assay_context is None or right.assay_context is None:
        return _comparison(left, right, "non_comparable", "Missing assay context prevents a safe comparison")

    left_context = left.assay_context
    right_context = right.assay_context
    if left_context.target_id != right_context.target_id:
        return _comparison(left, right, "non_comparable", "Target identifiers differ")

    same_measurement = (
        left_context.biological_system == right_context.biological_system
        and left_context.readout == right_context.readout
        and left_context.unit == right_context.unit
        and left_context.genetic_context == right_context.genetic_context
        and left_context.conditions == right_context.conditions
    )
    opposite_outcomes = {left.outcome_direction, right.outcome_direction} == {"supports", "contradicts"}
    if opposite_outcomes:
        return _comparison(left, right, "conflicting", "Comparable target evidence has opposing outcomes")
    if same_measurement:
        return _comparison(left, right, "direct", "Target, system, readout, unit, and genetic context match")
    return _comparison(left, right, "supportive", "Target matches but the measurement context differs")


def _comparison(
    left: EvidenceRecord, right: EvidenceRecord, relation: str, reason: str
) -> AssayComparison:
    return AssayComparison(
        left_evidence_id=left.id,
        right_evidence_id=right.id,
        relation=relation,
        reason=reason,
    )
