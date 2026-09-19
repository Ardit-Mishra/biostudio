"""Contracts for the Decision Twin's Assay Translation Map."""

from decision_twin.assay_map import build_assay_translation_map
from decision_twin.models import AssayContext, Citation, EvidenceRecord

RATIONALE = "The cited record reports this outcome for the stated assay context."


def _evidence(
    evidence_id: str,
    *,
    system: str | None,
    direction: str = "supports",
) -> EvidenceRecord:
    return EvidenceRecord(
        id=evidence_id,
        claim="A source-backed observation was entered for research triage.",
        citation=Citation(
            source="europe_pmc",
            source_id=evidence_id,
            retrieved_at="2026-09-18T12:00:00Z",
        ),
        structured_record={"source_record_id": evidence_id},
        assay_context=(
            AssayContext(
                target_id="EGFR",
                biological_system=system,
                readout="viability",
                unit="nM",
            )
            if system is not None
            else None
        ),
        outcome_direction=direction,
        direction_rationale=None if direction == "unknown" else RATIONALE,
    )


def test_map_preserves_all_lanes_and_marks_missing_stages_explicitly():
    """An absent human or in-vivo layer cannot disappear from the visual story."""
    assay_map = build_assay_translation_map(
        [
            _evidence("bio-1", system="biochemical"),
            _evidence("cell-1", system="cellular"),
        ]
    )

    lanes = {lane.stage: lane for lane in assay_map.lanes}
    assert [lane.stage for lane in assay_map.lanes] == [
        "biochemical",
        "cellular",
        "in_vivo",
        "human",
        "unclassified",
    ]
    assert lanes["biochemical"].status == "supporting"
    assert lanes["cellular"].evidence_ids == ["cell-1"]
    assert lanes["in_vivo"].status == "missing"
    assert lanes["human"].status == "missing"


def test_map_flags_conflicting_observations_in_their_assay_lane():
    """Opposite outcomes in a lane must be visually visible to the reviewer."""
    assay_map = build_assay_translation_map(
        [
            _evidence("cell-supports", system="cellular", direction="supports"),
            _evidence("cell-contradicts", system="cellular", direction="contradicts"),
        ]
    )

    cellular = next(lane for lane in assay_map.lanes if lane.stage == "cellular")
    assert cellular.status == "conflicting"
    assert cellular.evidence_ids == ["cell-contradicts", "cell-supports"]


def test_map_quarantines_evidence_without_assay_context_instead_of_guessing_a_stage():
    """Contextless records belong in an explicit unresolved lane."""
    assay_map = build_assay_translation_map([_evidence("unknown-1", system=None)])

    unresolved = next(lane for lane in assay_map.lanes if lane.stage == "unclassified")
    assert unresolved.status == "unclassified"
    assert unresolved.evidence_ids == ["unknown-1"]
    assert "assay context" in unresolved.gaps[0].lower()
